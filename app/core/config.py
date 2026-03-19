from functools import lru_cache
from typing import Literal

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5434/rag_db"

    # LLM Provider: "openai" or "gemini"
    llm_provider: Literal["openai", "gemini"] = "openai"

    # OpenAI (required when llm_provider=openai)
    openai_api_key: SecretStr = SecretStr("")

    # Gemini (required when llm_provider=gemini)
    gemini_api_key: SecretStr = SecretStr("")

    # Application
    app_env: str = "development"
    log_level: str = "INFO"
    allowed_origins: list[str] = ["http://localhost:3000"]

    # RAG configuration
    chunk_size: int = 800
    chunk_overlap: int = 150
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536
    chat_model: str = "gpt-4o-mini"
    chat_temperature: float = 0.2
    retrieval_top_k: int = 4
    agent_max_iterations: int = 5

    # Upload
    max_upload_size_mb: int = 10

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @model_validator(mode="after")
    def validate_provider_keys(self) -> "Settings":
        if self.llm_provider == "openai" and not self.openai_api_key.get_secret_value():
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
        if self.llm_provider == "gemini" and not self.gemini_api_key.get_secret_value():
            raise ValueError("GEMINI_API_KEY is required when LLM_PROVIDER=gemini")

        # Set sensible defaults per provider if user hasn't overridden
        if self.llm_provider == "gemini":
            if self.embedding_model == "text-embedding-3-small":
                self.embedding_model = "text-embedding-004"
            if self.chat_model == "gpt-4o-mini":
                self.chat_model = "gemini-2.0-flash"
            if self.embedding_dimensions == 1536:
                self.embedding_dimensions = 768

        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
