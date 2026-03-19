from pydantic import BaseModel, ConfigDict, Field, field_validator


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1, max_length=4000)
    thread_id: str | None = None
    namespace: str = "default"

    @field_validator("message")
    @classmethod
    def message_not_whitespace(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Message cannot be empty or whitespace only")
        return v


class CitationSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: str
    chunk_index: int
    preview: str


class ChatResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ok: bool = True
    answer: str
    thread_id: str
    citations: list[CitationSchema]
