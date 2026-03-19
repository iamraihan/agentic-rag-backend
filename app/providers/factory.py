from app.core.config import Settings
from app.providers.base import LLMProvider


def create_llm_provider(settings: Settings) -> LLMProvider:
    provider = settings.llm_provider.lower()

    if provider == "openai":
        from app.providers.openai import OpenAIProvider

        return OpenAIProvider(settings)

    if provider == "gemini":
        from app.providers.gemini import GeminiProvider

        return GeminiProvider(settings)

    raise ValueError(
        f"Unknown LLM provider: '{provider}'. Supported: 'openai', 'gemini'"
    )
