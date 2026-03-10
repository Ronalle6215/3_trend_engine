"""
Compare route — compare trends between runs
"""

import json

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pathlib import Path

from trend_engine.storage.sqlite_store import SQLiteStore

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))


@router.get("/", response_class=HTMLResponse)
async def compare_page(request: Request, run1: int = 0, run2: int = 0):
    db = SQLiteStore()
    runs = db.get_run_history(limit=20)

    trends_run1 = []
    trends_run2 = []
    comparison = []

    if run1 and run2:
        trends_run1 = db.get_trends_by_run(run1)
        trends_run2 = db.get_trends_by_run(run2)

        # Build comparison: topic → (score_run1, score_run2, change)
        scores_1 = {t["topic"]: t["trend_score"] for t in trends_run1}
        scores_2 = {t["topic"]: t["trend_score"] for t in trends_run2}
        all_topics = set(scores_1.keys()) | set(scores_2.keys())

        for topic in sorted(all_topics):
            s1 = scores_1.get(topic, 0)
            s2 = scores_2.get(topic, 0)
            diff = s2 - s1
            comparison.append({
                "topic": topic,
                "score_run1": round(s1, 2),
                "score_run2": round(s2, 2),
                "change": round(diff, 2),
                "direction": "up" if diff > 0 else ("down" if diff < 0 else "same"),
            })

        comparison.sort(key=lambda x: abs(x["change"]), reverse=True)

    return templates.TemplateResponse("compare.html", {
        "request": request,
        "page": "compare",
        "runs": runs,
        "run1": run1,
        "run2": run2,
        "comparison": comparison,
    })
