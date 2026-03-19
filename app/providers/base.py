from abc import ABC, abstractmethod
from typing import Any


class LLMProvider(ABC):
    """Abstract base for LLM chat + tool-calling providers."""

    @abstractmethod
    async def chat_completion(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        *,
        temperature: float = 0.2,
    ) -> "LLMResponse":
        ...

    @abstractmethod
    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        ...

    async def embed_query(self, text: str) -> list[float]:
        result = await self.embed_texts([text])
        return result[0]


class ToolCall:
    __slots__ = ("id", "function_name", "arguments")

    def __init__(self, id: str, function_name: str, arguments: str) -> None:
        self.id = id
        self.function_name = function_name
        self.arguments = arguments


class LLMResponse:
    __slots__ = ("content", "tool_calls", "raw_message")

    def __init__(
        self,
        content: str | None,
        tool_calls: list[ToolCall],
        raw_message: Any = None,
    ) -> None:
        self.content = content
        self.tool_calls = tool_calls
        self.raw_message = raw_message

    @property
    def has_tool_calls(self) -> bool:
        return len(self.tool_calls) > 0
