"""
Telegram bot — sends trend alerts
"""

import asyncio

from trend_engine.core.logging import get_logger
from trend_engine.config.settings import settings

logger = get_logger(__name__)


def send_trend_alert(trends: list[dict], max_trends: int = 5) -> bool:
    token = settings.telegram_bot_token
    chat_id = settings.telegram_chat_id

    if not token or not chat_id:
        logger.warning("Telegram not configured (TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID)")
        return False

    try:
        from telegram import Bot

        message = "🔥 *Trend Engine Alert*\n\n"
        for i, t in enumerate(trends[:max_trends], 1):
            topic = t.get("topic", t.topic if hasattr(t, "topic") else "?")
            score = t.get("trend_score", t.trend_score if hasattr(t, "trend_score") else 0)
            trend_type = t.get("trend_type", t.trend_type if hasattr(t, "trend_type") else "?")
            sources = t.get("sources", t.sources if hasattr(t, "sources") else [])
            if isinstance(sources, str):
                import json
                sources = json.loads(sources)
            src_text = ", ".join(sources) if isinstance(sources, list) else str(sources)
            message += f"{i}. *{topic}* ({trend_type})\n"
            message += f"   📊 Score: {score} | Sources: {src_text}\n"

            why = t.get("why_trending", [])
            if isinstance(why, str):
                import json
                why = json.loads(why)
            if why and isinstance(why, list) and len(why) > 0:
                message += f"   💡 {why[0][:80]}\n"
            message += "\n"

        message += "🔗 Dashboard: http://localhost:8000"

        async def _send():
            bot = Bot(token=token)
            await bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode="Markdown",
            )

        asyncio.run(_send())
        logger.info(f"Telegram alert sent ({len(trends[:max_trends])} trends)")
        return True

    except Exception as e:
        logger.error(f"Telegram alert failed: {e}")
        return False


def test_connection() -> dict:
    token = settings.telegram_bot_token
    chat_id = settings.telegram_chat_id

    if not token:
        return {"ok": False, "error": "TELEGRAM_BOT_TOKEN not set"}
    if not chat_id:
        return {"ok": False, "error": "TELEGRAM_CHAT_ID not set"}

    try:
        from telegram import Bot

        async def _test():
            bot = Bot(token=token)
            await bot.send_message(
                chat_id=chat_id,
                text="✅ Trend Engine — Telegram connection test OK!",
            )

        asyncio.run(_test())
        return {"ok": True, "message": "Test message sent!"}

    except Exception as e:
        return {"ok": False, "error": str(e)}
