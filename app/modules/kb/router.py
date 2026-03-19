import logging

from fastapi import APIRouter, Depends, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.db.session import get_db
from app.modules.kb.schemas import ErrorResponse, IngestionResponse
from app.modules.kb.service import IngestionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/kb", tags=["Knowledge Base"])


@router.post(
    "/upload",
    response_model=IngestionResponse,
    responses={
        400: {"model": ErrorResponse},
        413: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
    },
)
async def upload_document(
    file: UploadFile,
    namespace: str = Query(default="default", max_length=255),
    settings: Settings = Depends(get_settings),
    db: AsyncSession = Depends(get_db),
) -> IngestionResponse:
    service = IngestionService(settings, db)
    result = await service.ingest_file(file, namespace=namespace)
    return IngestionResponse(
        namespace=str(result["namespace"]),
        source=str(result["source"]),
        total_chunks=int(result["total_chunks"]),  # type: ignore[arg-type]
    )
