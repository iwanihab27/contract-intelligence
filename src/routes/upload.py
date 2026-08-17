import logging
from fastapi import APIRouter, UploadFile, File, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from src.controllers.upload_controller import UploadController
from src.core.database import get_db
from src.core.config import Settings, get_settings
from src.core.security import get_current_user
from src.enums import ResponseEnums
from src.models.user import User
from src.schemas.contract import ContractCreate
from src.core.limiter import limiter
from fastapi import Request

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/contracts", tags=["Contracts"])


@router.post("/upload")
@limiter.limit("10/minute")
async def upload_contract(request: Request, contract: ContractCreate = Depends(),file: UploadFile = File(...),
                          db: AsyncSession = Depends(get_db),settings: Settings = Depends(get_settings),
                          current_user: User = Depends(get_current_user)):
    logger.info(f"Uploading contract: {contract.name}")
    controller = UploadController(db=db, settings=settings)

    is_valid, result_signal = await controller.validate_file(file)
    if not is_valid:
        logger.error(f"File validation failed: {result_signal}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"signal": result_signal})

    file_name, file_path = await controller.save_file(file)
    logger.info(f"File saved: {file_name}")

    result = await controller.create_contract(
        name=contract.name,
        file_name=file_name,
        file_path=file_path,
        user_id=current_user.id
    )
    logger.info(f"Contract created: {result.id}")

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"signal": ResponseEnums.FILE_UPLOAD_SUCCESS.value, "contract_id": str(result.uuid)}
    )