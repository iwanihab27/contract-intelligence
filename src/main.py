import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from src.core.config import settings, get_settings
from src.core.startup import include_routers
from src.core.cache import init_redis, close_redis
from src.core.database import engine, get_db
from src.controllers.qdrant_controller import QdrantController
from src.enums import ResponseEnums
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from src.core.limiter import limiter
from redis.exceptions import RedisError
from fastapi import status

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_redis()
    await include_routers(app)

    async for db in get_db():
        qdrant = QdrantController(db=db, settings=get_settings())
        await qdrant.ensure_collection()
        break

    logger.info("Application started")
    yield

    await close_redis()
    await engine.dispose()
    logger.info("Application stopped")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.url}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"signal": ResponseEnums.ERROR.value}
    )

@app.exception_handler(RedisError)
async def redis_exception_handler(request: Request, exc: RedisError):
    logger.error(f"Redis error on {request.url}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"signal": ResponseEnums.ERROR.value}
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"HTTP error on {request.url}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"signal": exc.detail}
    )