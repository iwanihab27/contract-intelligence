import logging
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.controllers.query_controller import QueryController
from app.core.database import get_db
from app.core.config import Settings, get_settings
from app.enums import ResponseEnums
from app.schemas.chat_history import ChatRequest

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/contracts", tags=["Contracts"])


@router.post("/query")
async def query_contract(request: ChatRequest, db: AsyncSession = Depends(get_db),
                         settings: Settings = Depends(get_settings)):

    logger.info(f"Query received for contract: {request.contract_id}")
    controller = QueryController(db=db, settings=settings)

    is_valid, result_signal, answer = await controller.query(request.contract_id, request.question)

    if not is_valid:
        logger.error(f"Query failed: {result_signal}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"signal": result_signal}
        )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "signal": ResponseEnums.QUERY_SUCCESS.value,
            "answer": answer.get("answer"),
            "sources": answer.get("sources"),
            "query_type": answer.get("query_type"),
            "risk_score": answer.get("risk_score")
        }
    )