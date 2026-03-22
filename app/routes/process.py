import logging
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.controllers.processing_controller import ProcessingController
from app.core.database import get_db
from app.core.config import Settings, get_settings
from app.enums import ResponseEnums

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/contracts", tags=["Contracts"])

@router.post("/process/{contract_id}")
def process_contract(contract_id: str,db: Session = Depends(get_db),
                     settings: Settings = Depends(get_settings)):

    logger.info(f"Processing contract: {contract_id}")
    controller = ProcessingController(db=db, settings=settings)

    is_valid, result_signal = controller.process(contract_id)
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