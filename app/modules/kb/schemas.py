from pydantic import BaseModel, Field


class IngestionResponse(BaseModel):
    ok: bool = True
    namespace: str
    source: str
    total_chunks: int = Field(ge=0)


class ErrorResponse(BaseModel):
    ok: bool = False
    message: str
