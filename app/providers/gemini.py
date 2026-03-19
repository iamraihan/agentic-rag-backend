import json
import logging
from typing import Any

from google import genai
from google.genai import types

from app.core.config import Settings
from app.providers.base import LLMProvider, LLMResponse, ToolCall

logger = logging.getLogger(__name__)

EMBEDDING_BATCH_SIZE = 100


class GeminiProvider(LLMProvider):
    def __init__(self, settings: Settings) -> None:
        self._client = genai.Client(api_key=settings.gemini_api_key)
        self._chat_model = settings.chat_model
        self._embedding_model = settings.embedding_model

    async def chat_completion(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        *,
        temperature: float = 0.2,
    ) -> LLMResponse:
        gemini_contents = self._convert_messages(messages)
        gemini_tools = self._convert_tools(tools)

        response = await self._client.aio.models.generate_content(
            model=self._chat_model,
            contents=gemini_contents,
            config=types.GenerateContentConfig(
                temperature=temperature,
                tools=gemini_tools,
            ),
        )

        tool_calls: list[ToolCall] = []
        content: str | None = None

        if response.candidates and response.candidates[0].content:
            for part in response.candidates[0].content.parts or []:
                if part.function_call:
                    tool_calls.append(
                        ToolCall(
                            id=part.function_call.name or "call_0",
                            function_name=part.function_call.name or "",
                            arguments=json.dumps(dict(part.function_call.args or {})),
                        )
                    )
                elif part.text:
                    content = (content or "") + part.text

        return LLMResponse(content=content, tool_calls=tool_calls)

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        all_embeddings: list[list[float]] = []

        for i in range(0, len(texts), EMBEDDING_BATCH_SIZE):
            batch = texts[i : i + EMBEDDING_BATCH_SIZE]
            response = await self._client.aio.models.embed_content(
                model=self._embedding_model,
                contents=batch,
            )
            if response.embeddings:
                all_embeddings.extend(
                    list(emb.values) for emb in response.embeddings if emb.values
                )
            logger.debug("Gemini embedded batch %d-%d", i, i + len(batch))

        logger.info("Gemini generated %d embeddings", len(all_embeddings))
        return all_embeddings

    def _convert_messages(self, messages: list[dict[str, Any]]) -> list[types.Content]:
        contents: list[types.Content] = []
        system_instruction: str | None = None

        for msg in messages:
            role = msg.get("role", "user")
            text = msg.get("content", "")

            if role == "system":
                system_instruction = text
                continue

            if role == "tool":
                try:
                    result_data = json.loads(text)
                except (json.JSONDecodeError, TypeError):
                    result_data = {"result": text}

                function_name = msg.get("tool_call_id", "kb_search")
                contents.append(
                    types.Content(
                        role="function",
                        parts=[
                            types.Part(
                                function_response=types.FunctionResponse(
                                    name=function_name,
                                    response=result_data,
                                )
                            )
                        ],
                    )
                )
                continue

            gemini_role = "model" if role == "assistant" else "user"
            contents.append(
                types.Content(role=gemini_role, parts=[types.Part(text=text)])
            )

        # Prepend system instruction as a user message if present
        if system_instruction:
            contents.insert(
                0,
                types.Content(
                    role="user",
                    parts=[types.Part(text=f"[System Instructions]\n{system_instruction}")],
                ),
            )
            if len(contents) > 1:
                contents.insert(
                    1,
                    types.Content(
                        role="model",
                        parts=[types.Part(text="Understood. I will follow these instructions.")],
                    ),
                )

        return contents

    def _convert_tools(self, tools: list[dict[str, Any]]) -> list[types.Tool]:
        declarations: list[types.FunctionDeclaration] = []

        for tool in tools:
            func = tool.get("function", {})
            declarations.append(
                types.FunctionDeclaration(
                    name=func.get("name", ""),
                    description=func.get("description", ""),
                    parameters=func.get("parameters", {}),
                )
            )

        return [types.Tool(function_declarations=declarations)]
