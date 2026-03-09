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
                query = f"{keyword} xu hướng Việt Nam"
                logger.info(f"Firecrawl: searching '{query}'...")

                results = app.search(query=query, limit=5)

                # Firecrawl v2 SDK returns SearchData object
                entries = []
                if hasattr(results, "web") and results.web:
                    entries = results.web
                elif hasattr(results, "data"):
                    entries = results.data if isinstance(results.data, list) else []
                elif isinstance(results, list):
                    entries = results
                elif isinstance(results, dict):
                    entries = results.get("data", results.get("results", []))

                for entry in entries:
                    title = ""
                    url = ""
                    snippet = ""

                    if hasattr(entry, "title"):
                        title = entry.title or ""
                        url = entry.url or ""
                        snippet = entry.description or ""
                    elif isinstance(entry, dict):
                        title = entry.get("title", "")
                        url = entry.get("url", "")
                        snippet = entry.get("description", entry.get("markdown", ""))

                    if title:
                        items.append({
                            "title": title,
                            "url": url,
                            "snippet": snippet[:300] if snippet else "",
                            "keyword": keyword,
                            "type": "news_article",
                        })

                logger.info(f"Firecrawl: got {len(entries)} results for '{keyword}'")

            except Exception as e:
                logger.warning(f"Firecrawl search failed for '{keyword}': {e}")
                continue

        return RawSignal(
            source="news_firecrawl",
            collected_at=datetime.now().isoformat(),
            items=items,
        )
