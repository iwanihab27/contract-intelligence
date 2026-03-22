from fastapi import FastAPI
from app.core.database import Base, engine
from app.models.contract import Contract
from app.models.chunk import Chunk
from app.models.chat_history import ChatHistory
from app.models.risk_score import RiskScore
from app.routes.health import router as health_router
from app.routes.upload import router as upload_router
from app.routes.process import router as process_router
from app.routes.query import router as query_router
from app.routes.contracts import router as contracts_router
from app.routes.report import router as report_router

def include_routers(app: FastAPI):
    app.include_router(health_router)
    app.include_router(upload_router)
    app.include_router(process_router)
    app.include_router(query_router)
    app.include_router(contracts_router)
    app.include_router(report_router)


def init_db():
    Base.metadata.create_all(bind=engine)


def start_app(app: FastAPI):
    init_db()
    include_routers(app)