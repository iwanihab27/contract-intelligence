import logging
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from src.controllers.report_controller import ReportController
from src.core.database import get_db
from src.core.config import Settings, get_settings
from src.core.security import get_current_user
from src.enums import ResponseEnums
from src.models.user import User
from src.core.limiter import limiter
from fastapi import Request

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/contracts", tags=["Contracts"])


@router.get("/{contract_id}/report")
@limiter.limit("10/minute")
async def get_report(request: Request, contract_id: str,db: AsyncSession = Depends(get_db),
                     settings: Settings = Depends(get_settings),
                     current_user: User = Depends(get_current_user)):
    logger.info(f"Generating report for contract: {contract_id}")
    controller = ReportController(db=db, settings=settings)

    file_path = await controller.generate(contract_id)

    if not file_path:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"signal": ResponseEnums.CONTRACT_NOT_FOUND.value}
        )

    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=f"contract_report_{contract_id}.pdf"
    )