import logging
from fastapi import APIRouter, UploadFile, File, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.controllers.upload_controller import UploadController
from app.core.database import get_db
from app.core.config import Settings, get_settings
from app.enums import ResponseEnums
from app.schemas.contract import ContractCreate

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/contracts", tags=["Contracts"])

@router.post("/upload")
def upload_contract(contract: ContractCreate = Depends(),file: UploadFile = File(...),db: Session = Depends(get_db),
                    settings: Settings = Depends(get_settings)):

    logger.info(f"Uploading contract: {contract.name}")
    controller = UploadController(db=db, settings=settings)

    is_valid, result_signal = controller.validate_file(file)
    if not is_valid:
        logger.error(f"File validation failed: {result_signal}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"signal": result_signal})

    file_name, file_path = controller.save_file(file)
    logger.info(f"File saved: {file_name}")

    result = controller.create_contract(
        name=contract.name,
        file_name=file_name,
        file_path=file_path
    )
    logger.info(f"Contract created: {result.id}")

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"signal": ResponseEnums.FILE_UPLOAD_SUCCESS.value, "contract_id": str(result.uuid)}
    )
