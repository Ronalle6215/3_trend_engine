"""
Settings route — manage keywords, sources, telegram, API keys
"""

import os
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
ENV_PATH = settings.project_root / ".env"


def _read_env() -> dict[str, str]:
    """Read .env file into dict."""
    env = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, val = line.partition("=")
                env[key.strip()] = val.strip()
    return env


def _write_env(env: dict[str, str]):
    """Write dict back to .env file preserving comments."""
    lines = []
    existing = []
    if ENV_PATH.exists():
        existing = ENV_PATH.read_text().splitlines()

    written_keys = set()
    for line in existing:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key = stripped.split("=", 1)[0].strip()
            if key in env:
                lines.append(f"{key}={env[key]}")
                written_keys.add(key)
            else:
                lines.append(line)
        else:
            lines.append(line)

    # Append new keys not in original file
    for key, val in env.items():
        if key not in written_keys:
            lines.append(f"{key}={val}")

    ENV_PATH.write_text("\n".join(lines) + "\n")


def _mask_key(key: str) -> str:
    if not key or len(key) < 6:
        return key
    return "•" * (len(key) - 4) + key[-4:]


@router.get("/", response_class=HTMLResponse)
async def settings_page(request: Request, msg: str = ""):
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    env = _read_env()

    return templates.TemplateResponse("settings.html", {
        "request": request,
        "page": "settings",
        "config": config,
        "keywords": ", ".join(config.get("seed_keywords", [])),
        "sources": config.get("sources", {}),
        "telegram_configured": bool(settings.telegram_bot_token and settings.telegram_chat_id),
        "gemini_key_masked": _mask_key(env.get("GEMINI_API_KEY", "")),
        "firecrawl_key_masked": _mask_key(env.get("FIRECRAWL_API_KEY", "")),
        "telegram_token_masked": _mask_key(env.get("TELEGRAM_BOT_TOKEN", "")),
        "telegram_chat_id": env.get("TELEGRAM_CHAT_ID", ""),
        "has_gemini": bool(env.get("GEMINI_API_KEY")),
        "has_firecrawl": bool(env.get("FIRECRAWL_API_KEY")),
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

    settings.sources["seed_keywords"] = keyword_list
    return RedirectResponse(url="/settings?msg=Keywords+updated!", status_code=303)


@router.post("/api-keys")
async def update_api_keys(
    request: Request,
    gemini_key: str = Form(""),
    firecrawl_key: str = Form(""),
    telegram_token: str = Form(""),
    telegram_chat: str = Form(""),
):
    env = _read_env()

    if gemini_key and not gemini_key.startswith("•"):
        env["GEMINI_API_KEY"] = gemini_key
        settings.gemini_api_key = gemini_key
        os.environ["GEMINI_API_KEY"] = gemini_key

    if firecrawl_key and not firecrawl_key.startswith("•"):
        env["FIRECRAWL_API_KEY"] = firecrawl_key
        settings.firecrawl_api_key = firecrawl_key
        os.environ["FIRECRAWL_API_KEY"] = firecrawl_key

    if telegram_token and not telegram_token.startswith("•"):
        env["TELEGRAM_BOT_TOKEN"] = telegram_token
        settings.telegram_bot_token = telegram_token
        os.environ["TELEGRAM_BOT_TOKEN"] = telegram_token

    if telegram_chat:
        env["TELEGRAM_CHAT_ID"] = telegram_chat
        settings.telegram_chat_id = telegram_chat
        os.environ["TELEGRAM_CHAT_ID"] = telegram_chat

    _write_env(env)
    return RedirectResponse(url="/settings?msg=API+keys+saved!", status_code=303)


@router.post("/test-api")
async def test_api_key(request: Request, service: str = Form("gemini")):
    if service == "gemini":
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.gemini_api_key)
            model = genai.GenerativeModel("gemini-2.5-flash")
            model.generate_content("test")
            return RedirectResponse(url="/settings?msg=✅+Gemini+API+OK!", status_code=303)
        except Exception as e:
            return RedirectResponse(url=f"/settings?msg=❌+Gemini:+{str(e)[:60]}", status_code=303)

    elif service == "firecrawl":
        try:
            from firecrawl import FirecrawlApp
            app = FirecrawlApp(api_key=settings.firecrawl_api_key)
            app.search("test", limit=1)
            return RedirectResponse(url="/settings?msg=✅+Firecrawl+API+OK!", status_code=303)
        except Exception as e:
            return RedirectResponse(url=f"/settings?msg=❌+Firecrawl:+{str(e)[:60]}", status_code=303)

    return RedirectResponse(url="/settings?msg=Unknown+service", status_code=303)


@router.post("/test-telegram")
async def telegram_test(request: Request):
    result = test_connection()
    msg = result.get("message", result.get("error", "Unknown"))
    return RedirectResponse(url=f"/settings?msg=Telegram:+{msg}", status_code=303)
