import logging

from fastapi import APIRouter, Depends, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.db.session import get_db
from app.modules.kb.schemas import ErrorResponse, IngestionResponse
from app.modules.kb.service import IngestionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/kb", tags=["Knowledge Base"])

ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "text/plain",
    "text/markdown",
    "application/octet-stream",
}


@router.post(
    "/upload",
    response_model=IngestionResponse,
    status_code=201,
    responses={
        400: {"model": ErrorResponse},
        413: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
    },
)
async def upload_document(
    file: UploadFile,
    namespace: str = Query(default="default", min_length=1, max_length=255),
    settings: Settings = Depends(get_settings),
    db: AsyncSession = Depends(get_db),
) -> IngestionResponse:
    service = IngestionService(settings, db)
    result = await service.ingest_file(file, namespace=namespace)
    return IngestionResponse(
        namespace=result.namespace,
        source=result.source,
        total_chunks=result.total_chunks,
    )
