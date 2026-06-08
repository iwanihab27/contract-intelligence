import logging
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from src.controllers.query_controller import QueryController
from src.core.database import get_db
from src.core.config import settings
from src.core.security import get_current_user
from src.enums import ResponseEnums
from src.models.user import User
from src.schemas.chat_history import ChatRequest
from src.core.limiter import limiter
from fastapi import Request

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/contracts", tags=["Contracts"])


@router.post("/query")
@limiter.limit("30/minute")
async def query_contract(request: Request, body: ChatRequest, db: AsyncSession = Depends(get_db),
                         current_user: User = Depends(get_current_user)):
    logger.info(f"Query received for contract: {body.contract_id}")
    controller = QueryController(db=db, settings=settings)

    is_valid, result_signal, answer = await controller.query(body.contract_id, body.question)

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