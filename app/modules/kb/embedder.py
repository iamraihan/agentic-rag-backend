import logging

from app.core.config import Settings
from app.providers.base import LLMProvider
from app.providers.factory import create_llm_provider

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self, settings: Settings, provider: LLMProvider | None = None) -> None:
        self._provider = provider or create_llm_provider(settings)

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return await self._provider.embed_texts(texts)

    async def embed_query(self, text: str) -> list[float]:
        return await self._provider.embed_query(text)
