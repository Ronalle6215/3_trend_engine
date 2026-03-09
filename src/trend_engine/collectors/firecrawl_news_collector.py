"""
News collector — uses Firecrawl API to search and scrape news
"""

from datetime import datetime

from trend_engine.collectors.base import BaseCollector
from trend_engine.core.exceptions import CollectorError
from trend_engine.core.logging import get_logger
from trend_engine.core.models import RawSignal
from trend_engine.config.settings import settings

logger = get_logger(__name__)


class FirecrawlNewsCollector(BaseCollector):
    def collect(self, window: str) -> RawSignal:
        api_key = settings.firecrawl_api_key
        if not api_key:
            raise CollectorError("FIRECRAWL_API_KEY not set in .env")

        try:
            from firecrawl import FirecrawlApp
        except ImportError:
            raise CollectorError("firecrawl-py not installed. Run: pip install firecrawl-py")

        app = FirecrawlApp(api_key=api_key)
        items: list[dict] = []
        keywords = settings.seed_keywords

        for keyword in keywords:
            try:
                query = f"{keyword} xu hướng tin tức Việt Nam"
                logger.info(f"Firecrawl: searching '{query}'...")

                results = app.search(
                    query=query,
                    limit=5,
                )

                if results and isinstance(results, dict):
                    data = results.get("data", results.get("results", []))
                elif isinstance(results, list):
                    data = results
                else:
                    data = []

                for result in data:
                    if isinstance(result, dict):
                        items.append({
                            "title": result.get("title", result.get("metadata", {}).get("title", "")),
                            "url": result.get("url", result.get("sourceURL", "")),
                            "snippet": result.get("description", result.get("markdown", ""))[:300],
                            "keyword": keyword,
                            "type": "news_article",
                        })

                logger.info(f"Firecrawl: got {len(data)} results for '{keyword}'")

            except Exception as e:
                logger.warning(f"Firecrawl search failed for '{keyword}': {e}")
                continue

        return RawSignal(
            source="news_firecrawl",
            collected_at=datetime.now().isoformat(),
            items=items,
        )
