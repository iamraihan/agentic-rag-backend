import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.db.session import get_db
from app.modules.agent.schemas import ChatRequest, ChatResponse, CitationSchema
from app.modules.agent.service import AgentService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent", tags=["Agent Chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    settings: Settings = Depends(get_settings),
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    service = AgentService(settings, db)
    result = await service.chat(
        body.message,
        thread_id=body.thread_id,
        namespace=body.namespace,
    )
    return ChatResponse(
        answer=result.answer,
        thread_id=result.thread_id,
        citations=[
            CitationSchema(
                source=c.source,
                chunk_index=c.chunk_index,
                preview=c.preview,
            )
            for c in result.citations
        ],
    )
