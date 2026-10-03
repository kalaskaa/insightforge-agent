from fastapi import FastAPI

from backend.app.api.health import router as health_router
from backend.app.api.research import router as research_router
from backend.app.config import settings


app = FastAPI(title=settings.app_name)
app.include_router(health_router)
app.include_router(research_router)
