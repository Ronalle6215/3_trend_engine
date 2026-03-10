"""
Keyword extractor — Gemini-powered with naive fallback
"""

import json
import re
from collections import Counter
from typing import Any

from trend_engine.core.logging import get_logger
from trend_engine.config.settings import settings

logger = get_logger(__name__)


class KeywordExtractor:
    def extract(self, items: list[dict[str, Any]], max_keywords: int = 20) -> list[str]:
        """Extract top keywords from normalized signal items."""
        texts = [item.get("text", "") for item in items if item.get("text")]
        descriptions = [item.get("description", "") for item in items if item.get("description")]
        all_text = texts + descriptions

        if not all_text:
            return []

        # Try Gemini first
        if settings.gemini_api_key:
            try:
                return self._extract_with_gemini(all_text, max_keywords)
            except Exception as e:
                logger.warning(f"Gemini keyword extraction failed, using fallback: {e}")

        # Fallback to naive extraction
        return self._extract_naive(all_text, max_keywords)

    def _extract_with_gemini(self, texts: list[str], max_keywords: int) -> list[str]:
        import google.generativeai as genai

        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")

        combined = "\n".join(texts[:50])  # Limit to avoid token overflow
        prompt = (
            f"Analyze these trend signals from Vietnam and extract the top {max_keywords} "
            f"most important keywords/topics. Group similar concepts together. "
            f"Return ONLY a JSON array of strings, e.g. [\"keyword1\", \"keyword2\"]. "
            f"Signals:\n{combined}"
        )

        response = model.generate_content(prompt)
        text = response.text.strip()

        json_match = re.search(r'\[.*\]', text, re.DOTALL)
        if json_match:
            keywords = json.loads(json_match.group(0))
            logger.info(f"Gemini extracted {len(keywords)} keywords")
            return keywords[:max_keywords]

        return []

    def _extract_naive(self, texts: list[str], max_keywords: int) -> list[str]:
        from trend_engine.utils.text import extract_words

        words = []
        for text in texts:
            words.extend(extract_words(text))

        counts = Counter(words)
        return [word for word, _ in counts.most_common(max_keywords)]
