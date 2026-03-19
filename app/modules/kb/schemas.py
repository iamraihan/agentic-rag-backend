from pydantic import BaseModel, ConfigDict, Field


class IngestionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ok: bool = True
    namespace: str
    source: str
    total_chunks: int = Field(ge=0)


class ErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ok: bool = False
    message: str
