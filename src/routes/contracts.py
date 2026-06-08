import logging
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from src.controllers.contracts_controller import ContractsController
from src.core.database import get_db
from src.core.config import Settings, get_settings
from src.core.security import get_current_user
from src.enums import ResponseEnums
from src.models.user import User
from src.schemas.contract import ContractListResponse
from src.core.limiter import limiter
from fastapi import Request

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/contracts", tags=["Contracts"])


@router.get("")
@limiter.limit("60/minute")
async def get_contracts(request: Request, db: AsyncSession = Depends(get_db),settings: Settings = Depends(get_settings),
                        current_user: User = Depends(get_current_user)):
    controller = ContractsController(db=db, settings=settings)
    contracts = await controller.get_all()

    if not contracts:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"signal": ResponseEnums.CONTRACT_LIST_EMPTY.value}
        )

    return [ContractListResponse.model_validate(c) for c in contracts]


@router.delete("/{contract_id}")
@limiter.limit("60/minute")
async def delete_contract(request: Request, contract_id: str,db: AsyncSession = Depends(get_db),
                          settings: Settings = Depends(get_settings),
                          current_user: User = Depends(get_current_user)):
    logger.info(f"Deleting contract: {contract_id}")
    controller = ContractsController(db=db, settings=settings)

    is_valid, result_signal = await controller.delete(contract_id)
    if not is_valid:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"signal": result_signal}
        )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"signal": result_signal}
    )


@router.post("/{contract_id}/reanalyze")
@limiter.limit("5/minute")
async def reanalyze_contract(request: Request, contract_id: str,db: AsyncSession = Depends(get_db),
                             settings: Settings = Depends(get_settings),
                             current_user: User = Depends(get_current_user)):
    logger.info(f"Reanalyzing contract: {contract_id}")
    controller = ContractsController(db=db, settings=settings)

    is_valid, result_signal = await controller.reanalyze(contract_id)
    if not is_valid:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"signal": result_signal}
        )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"signal": result_signal}
    )