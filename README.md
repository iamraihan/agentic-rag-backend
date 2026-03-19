# Agentic RAG API

Production-grade Retrieval-Augmented Generation (RAG) API built with FastAPI, pgvector, and OpenAI/Gemini.

Upload documents (PDF, TXT, MD), chunk and embed them into pgvector, then chat with an AI agent that retrieves relevant context from your knowledge base before answering.

## Features

- **Document Ingestion** — Upload PDF, TXT, or Markdown files. Text is extracted, chunked (recursive character splitting), embedded, and stored in pgvector.
- **Agentic Chat** — An AI agent with a `kb_search` tool decides when to search your knowledge base and synthesizes answers with citations.
- **Multi-turn Conversations** — Thread-based conversation memory persisted in PostgreSQL.
- **Multi-Provider LLM** — Switch between OpenAI and Google Gemini via a single env var.
- **Vector Search** — Cosine similarity search using pgvector with IVFFlat indexing.

## Project Structure

```
app/
├── main.py                          # FastAPI app factory, lifespan, middleware
├── core/                            # Shared infrastructure
│   ├── config.py                    # Pydantic Settings (type-safe, provider-aware)
│   ├── exceptions.py                # Typed HTTP exceptions
│   ├── logging.py                   # Structured logging
│   └── db/                          # Database layer
│       ├── base.py                  # DeclarativeBase + UUID/Timestamp mixins
│       ├── engine.py                # Async engine + connection pool
│       └── session.py               # Session dependency injection
├── providers/                       # LLM provider abstraction
│   ├── base.py                      # Abstract LLMProvider interface
│   ├── factory.py                   # Provider factory (openai / gemini)
│   ├── openai.py                    # OpenAI implementation
│   └── gemini.py                    # Google Gemini implementation
├── modules/
│   ├── kb/                          # Knowledge Base module
│   │   ├── models.py                # DocumentChunk (pgvector embedding column)
│   │   ├── repository.py            # DB queries + cosine similarity search
│   │   ├── schemas.py               # Pydantic request/response models
│   │   ├── router.py                # POST /api/v1/kb/upload
│   │   ├── service.py               # Ingestion orchestrator
│   │   ├── loader.py                # PDF/TXT/MD text extraction
│   │   ├── splitter.py              # Recursive text chunking
│   │   ├── embedder.py              # Embedding via provider
│   │   └── retriever.py             # Similarity search service
│   └── agent/                       # Agent module
│       ├── models.py                # ConversationMessage model
│       ├── repository.py            # Thread history queries
│       ├── schemas.py               # Chat request/response models
│       ├── router.py                # POST /api/v1/agent/chat
│       ├── service.py               # Agent with tool-calling loop
│       ├── policy.py                # System prompt / agent rules
│       ├── tools.py                 # kb_search tool definition
│       └── memory.py                # Thread-based conversation memory
alembic/                             # Database migrations
docker-compose.yml                   # PostgreSQL 17 + pgvector
```

Each module is **self-contained** — it owns its model, repository, schema, service, and router.

## Prerequisites

- Python 3.12+
- Docker (for PostgreSQL with pgvector)
- OpenAI API key **or** Google Gemini API key

## Quick Start

### 1. Start PostgreSQL with pgvector

```bash
docker compose up -d
```

### 2. Install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 3. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and set your API key:

```env
# Use OpenAI (default)
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...

# Or use Gemini
# LLM_PROVIDER=gemini
# GEMINI_API_KEY=AIza...
```

### 4. Run database migrations

```bash
alembic upgrade head
```

### 5. Start the server

```bash
uvicorn app.main:app --reload --port 5000
```

The API is now running at `http://localhost:5000`. Swagger docs available at `http://localhost:5000/docs`.

## API Endpoints

### Health Check

```
GET /health
→ {"status": "healthy"}
```

### Upload Document

```bash
curl -X POST http://localhost:5000/api/v1/kb/upload \
  -F "file=@document.pdf" \
  -F "namespace=default"
```

```json
{
  "ok": true,
  "namespace": "default",
  "source": "document.pdf",
  "total_chunks": 42
}
```

Supported file types: `.pdf`, `.txt`, `.md` (max 10MB).

### Chat

```bash
curl -X POST http://localhost:5000/api/v1/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What does the document say about X?"}'
```

```json
{
  "ok": true,
  "answer": "According to the documentation...",
  "thread_id": "a1b2c3d4e5f67890",
  "citations": [
    {
      "source": "document.pdf",
      "chunk_index": 3,
      "preview": "Relevant text from the chunk..."
    }
  ]
}
```

To continue a conversation, pass the `thread_id`:

```bash
curl -X POST http://localhost:5000/api/v1/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Tell me more", "thread_id": "a1b2c3d4e5f67890"}'
```

## Configuration

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://...localhost:5434/rag_db` | PostgreSQL connection string |
| `LLM_PROVIDER` | `openai` | `openai` or `gemini` |
| `OPENAI_API_KEY` | — | Required when provider is openai |
| `GEMINI_API_KEY` | — | Required when provider is gemini |
| `CHAT_MODEL` | Auto per provider | `gpt-4o-mini` (openai) / `gemini-2.0-flash` (gemini) |
| `EMBEDDING_MODEL` | Auto per provider | `text-embedding-3-small` / `text-embedding-004` |
| `EMBEDDING_DIMENSIONS` | Auto per provider | `1536` (openai) / `768` (gemini) |
| `CHUNK_SIZE` | `800` | Characters per text chunk |
| `CHUNK_OVERLAP` | `150` | Overlap between chunks |
| `RETRIEVAL_TOP_K` | `4` | Number of chunks to retrieve |
| `APP_ENV` | `development` | `development` enables Swagger docs |
| `LOG_LEVEL` | `INFO` | Logging level |

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI + Uvicorn |
| Database | PostgreSQL 17 + pgvector |
| ORM | SQLAlchemy 2.0 (async) |
| Migrations | Alembic |
| Validation | Pydantic v2 |
| LLM | OpenAI / Google Gemini |
| PDF Parsing | pypdf |
