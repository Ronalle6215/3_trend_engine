"""
Generate route — Content Studio with AI model selection, tone, templates, brand kit
"""

import json

from fastapi import APIRouter, Request, Form, UploadFile, File
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from pathlib import Path

from trend_engine.storage.sqlite_store import SQLiteStore
from trend_engine.services.content_generator import (
    generate_content,
    get_brand_kit_files,
    save_brand_kit_file,
    delete_brand_kit_file,
    TONE_PRESETS,
    TEMPLATES,
    AVAILABLE_MODELS,
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
        "tone_presets": TONE_PRESETS,
        "template_presets": TEMPLATES,
        "models": AVAILABLE_MODELS,
        "brand_files": get_brand_kit_files(),
    })


@router.post("/", response_class=HTMLResponse)
async def generate_content_route(
    request: Request,
    topic: str = Form(...),
    content_type: str = Form("blog"),
    tone: str = Form("professional"),
    word_count: int = Form(500),
    model_id: str = Form("gemini-2.5-flash"),
    custom_notes: str = Form(""),
    use_brand_kit: bool = Form(False),
):
    db = SQLiteStore()
    trends = db.get_latest_trends(limit=20)

    # Find trend data
    why_trending = []
    sources = []
    for t in trends:
        if isinstance(t.get("why_trending_json"), str):
            try:
                t["why_trending"] = json.loads(t["why_trending_json"])
            except Exception:
                t["why_trending"] = []
        if t.get("topic") == topic:
            why_trending = t.get("why_trending", [])
            try:
                sources = json.loads(t.get("sources_json", "[]"))
            except Exception:
                sources = []

    content = generate_content(
        topic=topic,
        why_trending=why_trending,
        sources=sources,
        content_type=content_type,
        tone=tone,
        word_count=word_count,
        model_id=model_id,
        custom_notes=custom_notes,
        use_brand_kit=use_brand_kit,
    )

    return templates.TemplateResponse("generate.html", {
        "request": request,
        "page": "generate",
        "trends": trends,
        "content": content,
        "content_type": content_type,
        "selected_topic": topic,
        "selected_tone": tone,
        "selected_model": model_id,
        "word_count": word_count,
        "custom_notes": custom_notes,
        "tone_presets": TONE_PRESETS,
        "template_presets": TEMPLATES,
        "models": AVAILABLE_MODELS,
        "brand_files": get_brand_kit_files(),
    })


@router.post("/upload-brand", response_class=HTMLResponse)
async def upload_brand_file(
    request: Request,
    brand_file: UploadFile = File(...),
):
    if brand_file.filename:
        content = await brand_file.read()
        save_brand_kit_file(brand_file.filename, content)
    return RedirectResponse(url="/generate?msg=File+uploaded!", status_code=303)


@router.post("/delete-brand", response_class=HTMLResponse)
async def delete_brand(request: Request, filename: str = Form(...)):
    delete_brand_kit_file(filename)
    return RedirectResponse(url="/generate?msg=File+deleted!", status_code=303)
