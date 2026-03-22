from fastapi import FastAPI
from app.core.config import settings
from app.core.startup import start_app

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
)

start_app(app)
