"""
Analyze route — keyword input form + pipeline execution
"""

import json
from datetime import datetime

from fastapi import APIRouter, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pathlib import Path

from trend_engine.storage.sqlite_store import SQLiteStore

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))


@router.get("/", response_class=HTMLResponse)
async def analyze_form(request: Request):
    return templates.TemplateResponse("analyze.html", {
        "request": request,
        "page": "analyze",
        "results": None,
    })


@router.post("/", response_class=HTMLResponse)
async def analyze_run(
    request: Request,
    keywords: str = Form(...),
    window: str = Form("24h"),
):
    from trend_engine.config.settings import settings
    from trend_engine.pipelines.collect_pipeline import CollectPipeline
    from trend_engine.pipelines.detect_pipeline import DetectPipeline
    from trend_engine.pipelines.export_pipeline import ExportPipeline

    # Parse comma-separated keywords
    keyword_list = [k.strip() for k in keywords.split(",") if k.strip()]

    # Temporarily override seed_keywords
    original_keywords = settings.sources.get("seed_keywords", [])
    settings.sources["seed_keywords"] = keyword_list

    db = SQLiteStore()
    run_id = db.start_run(window)
    error = None
    trends = []

    try:
        # Run pipeline
        collect = CollectPipeline()
        signals = collect.run(window)
        db.save_signals(run_id, signals)

        detect = DetectPipeline()
        trends_obj = detect.run(signals, top_n=20)
        db.save_trends(run_id, trends_obj)

        export = ExportPipeline()
        export.run(trends_obj)

        total_items = sum(len(s.items) for s in signals)
        db.complete_run(run_id, total_items, len(trends_obj))

        # Convert to dicts for template
        for t in trends_obj:
            trends.append({
                "trend_id": t.trend_id,
                "topic": t.topic,
                "trend_type": t.trend_type,
                "trend_score": t.trend_score,
                "confidence": t.confidence,
                "time_window": t.time_window,
                "why_trending": t.why_trending,
                "sources": t.sources,
                "evidence": t.evidence,
                "suggested_actions": t.suggested_actions,
            })
    except Exception as e:
        error = str(e)
        db.complete_run(run_id, 0, 0)
    finally:
        # Restore original keywords
        settings.sources["seed_keywords"] = original_keywords

    return templates.TemplateResponse("analyze.html", {
        "request": request,
        "page": "analyze",
        "results": trends,
        "keywords": keywords,
        "window": window,
        "error": error,
        "run_id": run_id,
    })
