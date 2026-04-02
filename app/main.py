import logging
from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.startup import start_app
from app.enums import ResponseEnums

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.url}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"signal": ResponseEnums.ERROR.value}
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"HTTP error on {request.url}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"signal": exc.detail}
    )

start_app(app)