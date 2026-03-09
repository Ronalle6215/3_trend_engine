"""
Google Trends collector — uses pytrends (free, no API key)
"""

from datetime import datetime
from typing import List

from trend_engine.collectors.base import BaseCollector
from trend_engine.core.exceptions import CollectorError
from trend_engine.core.logging import get_logger
from trend_engine.core.models import RawSignal
from trend_engine.config.settings import settings

logger = get_logger(__name__)

# Time window → pytrends timeframe mapping
_WINDOW_MAP = {
    "6h": "now 7-d",   # pytrends min is ~7 days for hourly
    "24h": "now 7-d",
    "72h": "today 1-m",
}


class GoogleTrendsCollector(BaseCollector):
    def collect(self, window: str) -> RawSignal:
        try:
            from pytrends.request import TrendReq
        except ImportError:
            raise CollectorError("pytrends not installed. Run: pip install pytrends")

        timeframe = _WINDOW_MAP.get(window, "now 7-d")
        items: list[dict] = []

        try:
            pytrends = TrendReq(hl="vi", tz=420, retries=3, backoff_factor=0.5)

            # 1. Trending searches in Vietnam
            try:
                trending = pytrends.trending_searches(pn="vietnam")
                for _, row in trending.head(20).iterrows():
                    query = str(row.iloc[0]).strip()
                    if query:
                        items.append({
                            "query": query,
                            "type": "trending_search",
                            "volume": None,
                        })
                logger.info(f"Google Trends: got {len(items)} trending searches")
            except Exception as e:
                logger.warning(f"Google Trends trending_searches failed: {e}")

            # 2. Interest over time for seed keywords
            seed_keywords = settings.seed_keywords[:5]  # pytrends max 5 per request
            if seed_keywords:
                try:
                    pytrends.build_payload(seed_keywords, timeframe=timeframe, geo="VN")
                    interest = pytrends.interest_over_time()

                    if not interest.empty and len(interest.columns) > 0:
                        for kw in seed_keywords:
                            if kw in interest.columns:
                                avg_interest = int(interest[kw].mean())
                                latest = int(interest[kw].iloc[-1]) if len(interest) > 0 else 0
                                items.append({
                                    "query": kw,
                                    "type": "seed_keyword",
                                    "volume": latest,
                                    "avg_volume": avg_interest,
                                })
                    logger.info(f"Google Trends: tracked {len(seed_keywords)} seed keywords")
                except Exception as e:
                    logger.warning(f"Google Trends interest_over_time failed: {e}")

            # 3. Related queries for top seed keyword
            if seed_keywords:
                try:
                    pytrends.build_payload([seed_keywords[0]], timeframe=timeframe, geo="VN")
                    related = pytrends.related_queries()
                    for kw, data in related.items():
                        if data.get("rising") is not None:
                            for _, row in data["rising"].head(5).iterrows():
                                items.append({
                                    "query": str(row.get("query", "")),
                                    "type": "related_rising",
                                    "volume": int(row.get("value", 0)) if row.get("value") else None,
                                })
                    logger.info(f"Google Trends: got related queries for '{seed_keywords[0]}'")
                except Exception as e:
                    logger.warning(f"Google Trends related_queries failed: {e}")

        except Exception as e:
            logger.error(f"Google Trends collector error: {e}")
            raise CollectorError(f"Google Trends failed: {e}")

        return RawSignal(
            source="google_trends",
            collected_at=datetime.now().isoformat(),
            items=items,
        )
