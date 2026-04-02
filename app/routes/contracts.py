import logging
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.controllers.contracts_controller import ContractsController
from app.core.database import get_db
from app.core.config import Settings, get_settings
from app.enums import ResponseEnums
from app.schemas.contract import ContractListResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/contracts", tags=["Contracts"])

@router.get("")
async def get_contracts(db: Session = Depends(get_db),settings: Settings = Depends(get_settings)):

    controller = ContractsController(db=db, settings=settings)
    contracts = controller.get_all()

    if not contracts:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"signal": ResponseEnums.CONTRACT_LIST_EMPTY.value}
        )

    return [ContractListResponse.model_validate(c) for c in contracts]


@router.delete("/{contract_id}")
async def delete_contract(contract_id: str,db: Session = Depends(get_db),
                    settings: Settings = Depends(get_settings)):

    logger.info(f"Deleting contract: {contract_id}")
    controller = ContractsController(db=db, settings=settings)

    is_valid, result_signal = controller.delete(contract_id)
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
async def reanalyze_contract(contract_id: str,db: Session = Depends(get_db),
                       settings: Settings = Depends(get_settings)):

    logger.info(f"Reanalyzing contract: {contract_id}")
    controller = ContractsController(db=db, settings=settings)

    is_valid, result_signal = controller.reanalyze(contract_id)
    if not is_valid:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"signal": result_signal}
        )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"signal": result_signal}
    )