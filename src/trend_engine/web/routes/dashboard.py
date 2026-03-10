"""
Dashboard route — main overview page
"""

import json

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from pathlib import Path

from trend_engine.storage.sqlite_store import SQLiteStore

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))


@router.get("/")
async def dashboard(request: Request):
    db = SQLiteStore()
    latest = db.get_latest_trends(limit=20)
    runs = db.get_run_history(limit=5)
    source_dist = db.get_source_distribution()

    # Parse JSON strings in trends
    for t in latest:
        for key in ("why_trending_json", "sources_json", "evidence_json", "suggested_actions_json"):
            if key in t and isinstance(t[key], str):
                try:
                    t[key.replace("_json", "")] = json.loads(t[key])
                except (json.JSONDecodeError, TypeError):
                    t[key.replace("_json", "")] = []

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "trends": latest,
        "runs": runs,
        "source_dist": source_dist,
        "page": "dashboard",
    })
