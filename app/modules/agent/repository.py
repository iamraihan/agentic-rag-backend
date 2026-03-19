from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.agent.models import ConversationMessage


class ConversationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_message(self, thread_id: str, role: str, content: str) -> ConversationMessage:
        msg = ConversationMessage(thread_id=thread_id, role=role, content=content)
        self._session.add(msg)
        await self._session.flush()
        return msg

    async def get_history(
        self,
        thread_id: str,
        *,
        limit: int = 20,
    ) -> list[ConversationMessage]:
        stmt = (
            select(ConversationMessage)
            .where(ConversationMessage.thread_id == thread_id)
            .order_by(ConversationMessage.created_at.asc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def thread_exists(self, thread_id: str) -> bool:
        stmt = (
            select(ConversationMessage.id)
            .where(ConversationMessage.thread_id == thread_id)
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None
