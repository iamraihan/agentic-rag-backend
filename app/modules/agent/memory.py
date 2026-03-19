import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.agent.repository import ConversationRepository


class ConversationMemory:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = ConversationRepository(session)

    async def get_or_create_thread(self, thread_id: str | None) -> str:
        if thread_id and await self._repo.thread_exists(thread_id):
            return thread_id
        return uuid.uuid4().hex[:16]

    async def load_history(self, thread_id: str) -> list[dict[str, str]]:
        messages = await self._repo.get_history(thread_id)
        return [{"role": msg.role, "content": msg.content} for msg in messages]

    async def save_message(self, thread_id: str, role: str, content: str) -> None:
        await self._repo.add_message(thread_id, role, content)
