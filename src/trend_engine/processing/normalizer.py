"""
Signal normalizer — converts heterogeneous signal items into unified format
"""

from typing import Any

from trend_engine.core.logging import get_logger
from trend_engine.core.models import RawSignal
from trend_engine.utils.text import clean_text, normalize_keyword

logger = get_logger(__name__)


def normalize_signal_item(item: dict[str, Any], source: str) -> dict[str, Any]:
    """Normalize a single signal item into a unified schema."""
    if source == "google_trends":
        return {
            "text": normalize_keyword(item.get("query", "")),
            "volume": item.get("volume") or item.get("avg_volume") or 0,
            "source": source,
            "type": item.get("type", "keyword"),
            "url": None,
        }
    elif source == "news_firecrawl":
        title = item.get("title", "")
        snippet = item.get("snippet", "")
        return {
            "text": normalize_keyword(title),
            "description": clean_text(snippet),
            "volume": 1,  # each article = 1 mention
            "source": source,
            "type": "news_article",
            "url": item.get("url"),
            "keyword": item.get("keyword"),
        }
    elif source == "tiktok":
        tag = item.get("tag", "")
        views = item.get("views", 0)
        if isinstance(views, str):
            views = _parse_view_count(views)
        return {
            "text": normalize_keyword(tag.lstrip("#")),
            "volume": views,
            "source": source,
            "type": "trending_hashtag",
            "url": None,
        }
    else:
        return {
            "text": normalize_keyword(str(item.get("text", item.get("query", item.get("title", ""))))),
            "volume": item.get("volume", 0),
            "source": source,
            "type": "unknown",
            "url": item.get("url"),
        }


def normalize_signals(signals: list[RawSignal]) -> list[dict[str, Any]]:
    """Flatten and normalize all signal items across sources."""
    normalized = []
    for signal in signals:
        for item in signal.items:
            norm = normalize_signal_item(item, signal.source)
            if norm["text"]:  # skip empty
                normalized.append(norm)

    logger.info(f"Normalized {len(normalized)} items from {len(signals)} sources")
    return normalized


def _parse_view_count(text: str) -> int:
    """Parse view counts like '5.2M', '1.3K', '500' into integers."""
    text = text.strip().upper().replace(",", "")
    try:
        if text.endswith("B"):
            return int(float(text[:-1]) * 1_000_000_000)
        elif text.endswith("M"):
            return int(float(text[:-1]) * 1_000_000)
        elif text.endswith("K"):
            return int(float(text[:-1]) * 1_000)
        return int(float(text))
    except (ValueError, IndexError):
        return 0
