import logging
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from src.controllers.processing_controller import ProcessingController
from src.core.database import get_db
from src.core.config import Settings, get_settings
from src.core.security import get_current_user
from src.enums import ResponseEnums
from src.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/contracts", tags=["Contracts"])


@router.post("/process/{contract_id}")
async def process_contract(contract_id: str,db: AsyncSession = Depends(get_db),settings: Settings = Depends(get_settings),
                           current_user: User = Depends(get_current_user)):
    logger.info(f"Processing contract: {contract_id}")
    controller = ProcessingController(db=db, settings=settings)

    is_valid, result_signal = await controller.process(contract_id)
    if not is_valid:
        logger.error(f"Processing failed: {result_signal}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"signal": result_signal}
        )

    logger.info(f"Contract processed: {contract_id}")
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"signal": ResponseEnums.CONTRACT_PROCESSED.value}
    )