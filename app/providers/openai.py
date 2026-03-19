import logging
from typing import Any

from openai import AsyncOpenAI

from app.core.config import Settings
from app.providers.base import LLMProvider, LLMResponse, ToolCall

logger = logging.getLogger(__name__)

EMBEDDING_BATCH_SIZE = 512


class OpenAIProvider(LLMProvider):
    def __init__(self, settings: Settings) -> None:
        self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        self._chat_model = settings.chat_model
        self._embedding_model = settings.embedding_model

    async def chat_completion(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        *,
        temperature: float = 0.2,
    ) -> LLMResponse:
        completion = await self._client.chat.completions.create(
            model=self._chat_model,
            temperature=temperature,
            messages=messages,  # type: ignore[arg-type]
            tools=tools,  # type: ignore[arg-type]
            tool_choice="auto",
        )
        choice = completion.choices[0]

        tool_calls: list[ToolCall] = []
        if choice.finish_reason == "tool_calls" and choice.message.tool_calls:
            tool_calls = [
                ToolCall(
                    id=tc.id,
                    function_name=tc.function.name,
                    arguments=tc.function.arguments,
                )
                for tc in choice.message.tool_calls
            ]

        return LLMResponse(
            content=choice.message.content,
            tool_calls=tool_calls,
            raw_message=choice.message,
        )

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        all_embeddings: list[list[float]] = []

        for i in range(0, len(texts), EMBEDDING_BATCH_SIZE):
            batch = texts[i : i + EMBEDDING_BATCH_SIZE]
            response = await self._client.embeddings.create(
                model=self._embedding_model, input=batch
            )
            all_embeddings.extend(item.embedding for item in response.data)
            logger.debug("OpenAI embedded batch %d-%d", i, i + len(batch))

        logger.info("OpenAI generated %d embeddings", len(all_embeddings))
        return all_embeddings
