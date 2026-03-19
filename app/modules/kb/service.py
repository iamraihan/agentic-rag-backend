import logging
import tempfile
from dataclasses import dataclass
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.exceptions import DocumentProcessingError, FileTooLargeError, UnsupportedFileTypeError
from app.modules.kb.embedder import EmbeddingService
from app.modules.kb.loader import SUPPORTED_EXTENSIONS, extract_text
from app.modules.kb.models import DocumentChunk
from app.modules.kb.repository import DocumentChunkRepository
from app.modules.kb.splitter import split_text
from app.providers.base import LLMProvider

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class IngestionResult:
    namespace: str
    source: str
    total_chunks: int


class IngestionService:
    def __init__(
        self,
        settings: Settings,
        session: AsyncSession,
        *,
        provider: LLMProvider | None = None,
    ) -> None:
        self._settings = settings
        self._session = session
        self._embedder = EmbeddingService(settings, provider=provider)
        self._repo = DocumentChunkRepository(session)

    async def ingest_file(
        self,
        file: UploadFile,
        *,
        namespace: str = "default",
    ) -> IngestionResult:
        self._validate_file(file)

        # Pre-check file size before reading into memory
        if file.size and file.size > self._settings.max_upload_size_bytes:
            raise FileTooLargeError(self._settings.max_upload_size_mb)

        with tempfile.NamedTemporaryFile(
            suffix=self._safe_suffix(file.filename),
            delete=True,
        ) as tmp:
            content = await file.read()
            if len(content) > self._settings.max_upload_size_bytes:
                raise FileTooLargeError(self._settings.max_upload_size_mb)

            tmp.write(content)
            tmp.flush()
            tmp_path = Path(tmp.name)

            raw_text = extract_text(tmp_path)

        if not raw_text.strip():
            raise DocumentProcessingError("Document contains no extractable text")

        chunks = split_text(
            raw_text,
            chunk_size=self._settings.chunk_size,
            chunk_overlap=self._settings.chunk_overlap,
        )

        texts = [c.content for c in chunks]
        embeddings = await self._embedder.embed_texts(texts)

        source = file.filename or "unknown"
        db_chunks = [
            DocumentChunk(
                namespace=namespace,
                source=source,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                embedding=embeddings[i],
            )
            for i, chunk in enumerate(chunks)
        ]

        count = await self._repo.insert_many(db_chunks)
        logger.info("Ingested %d chunks from '%s' into namespace '%s'", count, source, namespace)

        return IngestionResult(namespace=namespace, source=source, total_chunks=count)

    def _validate_file(self, file: UploadFile) -> None:
        filename = file.filename or ""
        suffix = Path(filename).suffix.lower()
        if suffix not in SUPPORTED_EXTENSIONS:
            raise UnsupportedFileTypeError(suffix)

    @staticmethod
    def _safe_suffix(filename: str | None) -> str:
        suffix = Path(filename or "file.txt").suffix.lower()
        if suffix in SUPPORTED_EXTENSIONS:
            return suffix
        return ".txt"
