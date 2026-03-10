"""
Generate route — AI content generation from trends
"""

import json

from fastapi import APIRouter, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pathlib import Path

from trend_engine.storage.sqlite_store import SQLiteStore
from trend_engine.services.content_generator import (
    generate_blog_draft,
    generate_facebook_post,
    generate_tiktok_hashtags,
)

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))


@router.get("/", response_class=HTMLResponse)
async def generate_form(request: Request):
    db = SQLiteStore()
    trends = db.get_latest_trends(limit=20)
    for t in trends:
        if isinstance(t.get("why_trending_json"), str):
            try:
                t["why_trending"] = json.loads(t["why_trending_json"])
            except Exception:
                t["why_trending"] = []
    return templates.TemplateResponse("generate.html", {
        "request": request,
        "page": "generate",
        "trends": trends,
        "content": None,
        "content_type": None,
    })


@router.post("/", response_class=HTMLResponse)
async def generate_content(
    request: Request,
    topic: str = Form(...),
    content_type: str = Form("blog"),
):
    db = SQLiteStore()
    trends = db.get_latest_trends(limit=20)

    # Find the selected trend
    why_trending = []
    sources = []
    for t in trends:
        if t.get("topic") == topic:
            try:
                why_trending = json.loads(t.get("why_trending_json", "[]"))
                sources = json.loads(t.get("sources_json", "[]"))
            except Exception:
                pass
            break

    # Parse all trends for dropdown
    for t in trends:
        if isinstance(t.get("why_trending_json"), str):
            try:
                t["why_trending"] = json.loads(t["why_trending_json"])
            except Exception:
                t["why_trending"] = []

    # Generate content
    if content_type == "blog":
        content = generate_blog_draft(topic, why_trending, sources)
    elif content_type == "facebook":
        content = generate_facebook_post(topic, why_trending)
    elif content_type == "tiktok":
        content = generate_tiktok_hashtags(topic)
    else:
        content = "Invalid content type"

    return templates.TemplateResponse("generate.html", {
        "request": request,
        "page": "generate",
        "trends": trends,
        "content": content,
        "content_type": content_type,
        "selected_topic": topic,
    })
