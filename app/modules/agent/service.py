import json
import logging
from dataclasses import dataclass
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.modules.agent.memory import ConversationMemory
from app.modules.agent.policy import SYSTEM_PROMPT
from app.modules.agent.tools import build_kb_search_tool_definition, execute_kb_search
from app.modules.kb.retriever import RetrieverService
from app.providers.base import LLMProvider
from app.providers.factory import create_llm_provider

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Citation:
    source: str
    chunk_index: int
    preview: str


@dataclass(frozen=True)
class AgentResponse:
    answer: str
    thread_id: str
    citations: list[Citation]


class AgentService:
    def __init__(self, settings: Settings, session: AsyncSession) -> None:
        self._provider: LLMProvider = create_llm_provider(settings)
        self._temperature = settings.chat_temperature
        self._memory = ConversationMemory(session)
        self._retriever = RetrieverService(settings, session, provider=self._provider)
        self._tools = [build_kb_search_tool_definition()]

    async def chat(
        self,
        user_message: str,
        *,
        thread_id: str | None = None,
        namespace: str = "default",
    ) -> AgentResponse:
        thread_id = await self._memory.get_or_create_thread(thread_id)

        history = await self._memory.load_history(thread_id)
        await self._memory.save_message(thread_id, "user", user_message)

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            *history,
            {"role": "user", "content": user_message},
        ]

        response = await self._run_agent_loop(messages, namespace)

        await self._memory.save_message(thread_id, "assistant", response["answer"])

        citations = [
            Citation(
                source=c.get("source", ""),
                chunk_index=c.get("chunk_index", 0),
                preview=c.get("preview", ""),
            )
            for c in response.get("citations", [])
        ]

        return AgentResponse(
            answer=response["answer"],
            thread_id=thread_id,
            citations=citations,
        )

    async def _run_agent_loop(
        self,
        messages: list[dict[str, Any]],
        namespace: str,
    ) -> dict[str, Any]:
        max_iterations = 5

        for _ in range(max_iterations):
            llm_response = await self._provider.chat_completion(
                messages,
                self._tools,
                temperature=self._temperature,
            )

            if llm_response.has_tool_calls:
                if llm_response.raw_message is not None:
                    messages.append(llm_response.raw_message)  # type: ignore[arg-type]
                else:
                    messages.append({
                        "role": "assistant",
                        "content": llm_response.content or "",
                    })

                for tool_call in llm_response.tool_calls:
                    if tool_call.function_name == "kb_search":
                        result = await execute_kb_search(
                            self._retriever,
                            tool_call.arguments,
                            namespace=namespace,
                        )
                    else:
                        result = json.dumps(
                            {"error": f"Unknown tool: {tool_call.function_name}"}
                        )

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result,
                    })
            else:
                raw = llm_response.content or ""
                return self._parse_response(raw)

        return {"answer": "I was unable to process your request.", "citations": []}

    def _parse_response(self, raw: str) -> dict[str, Any]:
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

        try:
            parsed: dict[str, Any] = json.loads(cleaned)
            if "answer" in parsed:
                return parsed
        except json.JSONDecodeError:
            pass

        return {"answer": raw.strip(), "citations": []}
