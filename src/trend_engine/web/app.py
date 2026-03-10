"""
FastAPI application — Trend Engine Web UI
"""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

WEB_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Trend Engine", description="Trend Intelligence Dashboard")

# Static files & templates
app.mount("/static", StaticFiles(directory=str(WEB_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(WEB_DIR / "templates"))

# Import and include routers
from trend_engine.web.routes.dashboard import router as dashboard_router
from trend_engine.web.routes.analyze import router as analyze_router
from trend_engine.web.routes.generate import router as generate_router
from trend_engine.web.routes.compare import router as compare_router
from trend_engine.web.routes.settings_page import router as settings_router
from trend_engine.web.routes.api import router as api_router

app.include_router(dashboard_router)
app.include_router(analyze_router, prefix="/analyze")
app.include_router(generate_router, prefix="/generate")
app.include_router(compare_router, prefix="/compare")
app.include_router(settings_router, prefix="/settings")
app.include_router(api_router, prefix="/api")
