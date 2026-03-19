import uuid

from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.kb.models import DocumentChunk


class DocumentChunkRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def insert_many(self, chunks: list[DocumentChunk]) -> int:
        self._session.add_all(chunks)
        await self._session.flush()
        return len(chunks)

    async def similarity_search(
        self,
        embedding: list[float],
        *,
        namespace: str = "default",
        top_k: int = 4,
    ) -> list[tuple[DocumentChunk, float]]:
        embedding_literal = f"[{','.join(str(v) for v in embedding)}]"
        distance_expr = DocumentChunk.embedding.cosine_distance(
            text(f"'{embedding_literal}'::vector")
        )

        stmt = (
            select(DocumentChunk, distance_expr.label("distance"))
            .where(DocumentChunk.namespace == namespace)
            .order_by(distance_expr)
            .limit(top_k)
        )
        result = await self._session.execute(stmt)
        rows = result.all()
        return [(row[0], 1.0 - float(row[1])) for row in rows]

    async def delete_by_source(self, source: str, namespace: str = "default") -> int:
        stmt = (
            delete(DocumentChunk)
            .where(DocumentChunk.source == source)
            .where(DocumentChunk.namespace == namespace)
        )
        result = await self._session.execute(stmt)
        return result.rowcount  # type: ignore[return-value]

    async def get_by_id(self, chunk_id: uuid.UUID) -> DocumentChunk | None:
        return await self._session.get(DocumentChunk, chunk_id)
