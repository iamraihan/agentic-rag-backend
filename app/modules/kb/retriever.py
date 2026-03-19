import logging
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.modules.kb.embedder import EmbeddingService
from app.modules.kb.repository import DocumentChunkRepository
from app.providers.base import LLMProvider

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RetrievedContext:
    source: str
    chunk_index: int
    content: str
    similarity: float


class RetrieverService:
    def __init__(
        self,
        settings: Settings,
        session: AsyncSession,
        *,
        provider: LLMProvider | None = None,
    ) -> None:
        self._settings = settings
        self._embedder = EmbeddingService(settings, provider=provider)
        self._repo = DocumentChunkRepository(session)

    async def retrieve(
        self,
        query: str,
        *,
        namespace: str = "default",
        top_k: int | None = None,
    ) -> list[RetrievedContext]:
        k = top_k or self._settings.retrieval_top_k
        query_embedding = await self._embedder.embed_query(query)
        results = await self._repo.similarity_search(
            query_embedding,
            namespace=namespace,
            top_k=k,
        )

        contexts = [
            RetrievedContext(
                source=chunk.source,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                similarity=round(score, 4),
            )
            for chunk, score in results
        ]

        logger.info(
            "Retrieved %d contexts for query (top similarity=%.4f)",
            len(contexts),
            contexts[0].similarity if contexts else 0.0,
        )
        return contexts
