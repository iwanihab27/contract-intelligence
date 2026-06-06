from fastapi import FastAPI
from src.core.database import Base, engine
from src.routes.health import router as health_router
from src.routes.upload import router as upload_router
from src.routes.process import router as process_router
from src.routes.query import router as query_router
from src.routes.contracts import router as contracts_router
from src.routes.report import router as report_router
from src.routes.user import router as user_router

async def include_routers(app: FastAPI):
    app.include_router(health_router)
    app.include_router(user_router)
    app.include_router(upload_router)
    app.include_router(process_router)
    app.include_router(query_router)
    app.include_router(contracts_router)
    app.include_router(report_router)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def start_app(app: FastAPI):
    await init_db()
    await include_routers(app)