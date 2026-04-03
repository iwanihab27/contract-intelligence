import logging
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.controllers.report_controller import ReportController
from app.core.database import get_db
from app.core.config import Settings, get_settings
from app.enums import ResponseEnums

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/contracts", tags=["Contracts"])

@router.get("/{contract_id}/report")
async def get_report(contract_id: str, db: AsyncSession = Depends(get_db),
                     settings: Settings = Depends(get_settings)):

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