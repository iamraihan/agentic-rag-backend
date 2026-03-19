"""Initial schema with pgvector

Revision ID: 001
Revises:
Create Date: 2026-03-19

"""
from typing import Sequence, Union

import os

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Read dimension from env so migration matches the chosen provider
# OpenAI text-embedding-3-small = 1536, Gemini text-embedding-004 = 768
EMBEDDING_DIM = int(os.environ.get("EMBEDDING_DIMENSIONS", "1536"))


def upgrade() -> None:
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Document chunks table
    op.create_table(
        "document_chunks",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("namespace", sa.String(255),
                  nullable=False, server_default="default"),
        sa.Column("source", sa.String(512), nullable=False),
        sa.Column("chunk_index", sa.Integer, nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("embedding", Vector(EMBEDDING_DIM), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_index("ix_document_chunks_namespace",
                    "document_chunks", ["namespace"])
    op.create_index("ix_document_chunks_source", "document_chunks", ["source"])
    op.execute(
        "CREATE INDEX ix_document_chunks_embedding ON document_chunks "
        "USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )

    # Conversation messages table
    op.create_table(
        "conversation_messages",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("thread_id", sa.String(64), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_conversation_messages_thread_id",
                    "conversation_messages", ["thread_id"])


def downgrade() -> None:
    op.drop_table("conversation_messages")
    op.drop_table("document_chunks")
    op.execute("DROP EXTENSION IF EXISTS vector")
