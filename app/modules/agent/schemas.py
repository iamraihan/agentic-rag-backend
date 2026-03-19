from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    thread_id: str | None = None
    namespace: str = "default"


class CitationSchema(BaseModel):
    source: str
    chunk_index: int
    preview: str


class ChatResponse(BaseModel):
    ok: bool = True
    answer: str
    thread_id: str
    citations: list[CitationSchema]
