"""
TikTok collector — scrapes TikTok Creative Center (free, no API key)
Fallback: use Gemini web search for TikTok trends
"""

from datetime import datetime

from trend_engine.collectors.base import BaseCollector
from trend_engine.core.exceptions import CollectorError
from trend_engine.core.logging import get_logger
from trend_engine.core.models import RawSignal
from trend_engine.config.settings import settings
from trend_engine.utils.http import create_session

logger = get_logger(__name__)

CREATIVE_CENTER_URL = "https://ads.tiktok.com/business/creativecenter/inspiration/popular/hashtag/pc/en"


class TikTokCollector(BaseCollector):
    def collect(self, window: str) -> RawSignal:
        items: list[dict] = []

        # Strategy 1: Try Creative Center scraping
        try:
            items = self._scrape_creative_center()
            if items:
                logger.info(f"TikTok Creative Center: got {len(items)} trending hashtags")
        except Exception as e:
            logger.warning(f"TikTok Creative Center scraping failed: {e}")

        # Strategy 2: Fallback to Gemini search
        if not items:
            try:
                items = self._gemini_fallback()
                if items:
                    logger.info(f"TikTok (Gemini fallback): got {len(items)} trends")
            except Exception as e:
                logger.warning(f"TikTok Gemini fallback failed: {e}")

        return RawSignal(
            source="tiktok",
            collected_at=datetime.now().isoformat(),
            items=items,
        )

    def _scrape_creative_center(self) -> list[dict]:
        session = create_session()
        resp = session.get(CREATIVE_CENTER_URL, timeout=15)
        resp.raise_for_status()

        from bs4 import BeautifulSoup

        soup = BeautifulSoup(resp.text, "html.parser")
        items = []

        # TikTok Creative Center uses dynamic rendering, but we can try
        # to extract from initial HTML or from embedded JSON data
        import json
        import re

        # Look for embedded JSON data in script tags
        for script in soup.find_all("script"):
            text = script.string or ""
            # Look for data patterns
            match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', text, re.DOTALL)
            if not match:
                match = re.search(r'"hashtag_list"\s*:\s*(\[.*?\])', text, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(1))
                    if isinstance(data, list):
                        for item in data[:20]:
                            if isinstance(item, dict):
                                items.append({
                                    "tag": item.get("hashtag_name", item.get("name", "")),
                                    "views": item.get("publish_cnt", item.get("video_count", 0)),
                                    "type": "trending_hashtag",
                                })
                except json.JSONDecodeError:
                    continue

        # Also try direct HTML extraction
        if not items:
            for tag_el in soup.select("[class*='hashtag'], [class*='CardPc']"):
                name_el = tag_el.select_one("[class*='name'], [class*='title']")
                count_el = tag_el.select_one("[class*='count'], [class*='num']")
                if name_el:
                    items.append({
                        "tag": name_el.get_text(strip=True),
                        "views": count_el.get_text(strip=True) if count_el else "0",
                        "type": "trending_hashtag",
                    })

        return items[:20]

    def _gemini_fallback(self) -> list[dict]:
        api_key = settings.gemini_api_key
        if not api_key:
            logger.warning("No GEMINI_API_KEY for TikTok fallback")
            return []

        try:
            import google.generativeai as genai

            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-2.5-flash")

            prompt = (
                "List the top 15 trending TikTok hashtags in Vietnam right now. "
                "For each, provide the hashtag name and estimated view count. "
                "Return ONLY a JSON array like: "
                '[{"tag": "#hashtag", "views": 1000000, "type": "trending_hashtag"}]'
            )

            response = model.generate_content(prompt)
            text = response.text.strip()

            # Extract JSON from response
            import json
            import re

            json_match = re.search(r'\[.*\]', text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))

        except Exception as e:
            logger.warning(f"Gemini TikTok fallback error: {e}")

        return []
