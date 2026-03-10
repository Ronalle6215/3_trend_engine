"""
Settings route — manage keywords, sources, telegram
"""

import yaml
from pathlib import Path

from fastapi import APIRouter, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse

from trend_engine.config.settings import settings
from trend_engine.services.telegram_bot import test_connection

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))
CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "sources.yaml"


@router.get("/", response_class=HTMLResponse)
async def settings_page(request: Request, msg: str = ""):
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    return templates.TemplateResponse("settings.html", {
        "request": request,
        "page": "settings",
        "config": config,
        "keywords": ", ".join(config.get("seed_keywords", [])),
        "sources": config.get("sources", {}),
        "telegram_configured": bool(settings.telegram_bot_token and settings.telegram_chat_id),
        "msg": msg,
    })


@router.post("/keywords", response_class=HTMLResponse)
async def update_keywords(request: Request, keywords: str = Form(...)):
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    keyword_list = [k.strip() for k in keywords.split(",") if k.strip()]
    config["seed_keywords"] = keyword_list

    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False)

    # Reload settings
    settings.sources["seed_keywords"] = keyword_list

    return RedirectResponse(url="/settings?msg=Keywords+updated!", status_code=303)


@router.post("/test-telegram")
async def telegram_test(request: Request):
    result = test_connection()
    msg = result.get("message", result.get("error", "Unknown"))
    return RedirectResponse(url=f"/settings?msg=Telegram:+{msg}", status_code=303)
