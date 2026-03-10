"""
API routes — JSON endpoints for AJAX calls
"""

import json

from fastapi import APIRouter

from trend_engine.storage.sqlite_store import SQLiteStore

router = APIRouter()


@router.get("/trends/latest")
async def api_latest_trends(limit: int = 20):
    db = SQLiteStore()
    trends = db.get_latest_trends(limit=limit)
    for t in trends:
        for key in ("why_trending_json", "sources_json", "evidence_json", "suggested_actions_json"):
            if key in t and isinstance(t[key], str):
                try:
                    t[key.replace("_json", "")] = json.loads(t[key])
                except Exception:
                    t[key.replace("_json", "")] = []
                del t[key]
    return {"trends": trends}


@router.get("/trends/history")
async def api_trend_history(topic: str, limit: int = 10):
    db = SQLiteStore()
    return {"history": db.get_trend_history(topic, limit)}


@router.get("/runs")
async def api_runs(limit: int = 10):
    db = SQLiteStore()
    return {"runs": db.get_run_history(limit)}


@router.get("/chart/scores")
async def api_chart_scores(topic: str = ""):
    db = SQLiteStore()
    data = db.get_score_timeline(topic=topic if topic else None)
    return {"data": data}


@router.get("/chart/sources")
async def api_chart_sources(run_id: int = 0):
    db = SQLiteStore()
    data = db.get_source_distribution(run_id=run_id if run_id else None)
    return {"data": data}
