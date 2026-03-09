"""
Unit tests for collectors (with mocked API calls)
"""

import sys
import os
from unittest.mock import patch, MagicMock
from datetime import datetime

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from trend_engine.core.models import RawSignal


class TestGoogleTrendsCollector:
    @patch("trend_engine.collectors.google_trends_collector.settings")
    def test_collect_returns_raw_signal(self, mock_settings):
        mock_settings.seed_keywords = ["ai", "fnb"]

        with patch("pytrends.request.TrendReq") as MockTrendReq:
            import pandas as pd

            mock_pytrends = MockTrendReq.return_value

            # Mock trending_searches
            mock_pytrends.trending_searches.return_value = pd.DataFrame(
                {"0": ["AI agents", "ChatGPT", "Python 4"]}
            )

            # Mock interest_over_time
            mock_pytrends.interest_over_time.return_value = pd.DataFrame(
                {"ai": [50, 60, 70], "fnb": [30, 40, 50]}
            )

            # Mock related_queries
            mock_pytrends.related_queries.return_value = {
                "ai": {
                    "rising": pd.DataFrame({"query": ["ai agent tools"], "value": [500]}),
                    "top": None,
                }
            }

            from trend_engine.collectors.google_trends_collector import GoogleTrendsCollector

            collector = GoogleTrendsCollector()
            result = collector.collect("24h")

            assert isinstance(result, RawSignal)
            assert result.source == "google_trends"
            assert len(result.items) > 0


class TestFirecrawlNewsCollector:
    @patch("trend_engine.collectors.firecrawl_news_collector.settings")
    def test_collect_returns_raw_signal(self, mock_settings):
        mock_settings.firecrawl_api_key = "test-key"
        mock_settings.seed_keywords = ["ai"]

        with patch("firecrawl.FirecrawlApp") as MockApp:
            mock_app = MockApp.return_value
            mock_app.search.return_value = {
                "data": [
                    {"title": "AI News Article", "url": "https://example.com", "description": "Test article"}
                ]
            }

            from trend_engine.collectors.firecrawl_news_collector import FirecrawlNewsCollector

            collector = FirecrawlNewsCollector()
            result = collector.collect("24h")

            assert isinstance(result, RawSignal)
            assert result.source == "news_firecrawl"
            assert len(result.items) == 1
            assert result.items[0]["title"] == "AI News Article"


class TestTikTokCollector:
    @patch("trend_engine.collectors.tiktok_collector.settings")
    @patch("trend_engine.collectors.tiktok_collector.create_session")
    def test_fallback_to_gemini(self, mock_session, mock_settings):
        mock_settings.gemini_api_key = "test-key"

        # Make HTTP scraping fail
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = Exception("Connection error")
        mock_session.return_value.get.return_value = mock_resp

        with patch("google.generativeai.configure"), \
             patch("google.generativeai.GenerativeModel") as MockModel:

            mock_model = MockModel.return_value
            mock_model.generate_content.return_value = MagicMock(
                text='[{"tag": "#coding", "views": 5000, "type": "trending_hashtag"}]'
            )

            from trend_engine.collectors.tiktok_collector import TikTokCollector

            collector = TikTokCollector()
            result = collector.collect("24h")

            assert isinstance(result, RawSignal)
            assert result.source == "tiktok"
