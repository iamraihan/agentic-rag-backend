from pgvector.sqlalchemy import Vector
from sqlalchemy import Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.config import get_settings
from app.core.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

_dimensions = get_settings().embedding_dimensions


class DocumentChunk(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "document_chunks"

    namespace: Mapped[str] = mapped_column(String(255), nullable=False, default="default")
    source: Mapped[str] = mapped_column(String(512), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(_dimensions), nullable=False)

    __table_args__ = (
        Index("ix_document_chunks_namespace", "namespace"),
        Index("ix_document_chunks_source", "source"),
        Index(
            "ix_document_chunks_embedding",
            "embedding",
            postgresql_using="ivfflat",
            postgresql_with={"lists": 100},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )
