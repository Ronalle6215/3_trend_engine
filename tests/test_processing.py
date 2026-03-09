"""
Unit tests for processing pipeline
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from trend_engine.core.models import RawSignal, TopicCluster
from trend_engine.processing.normalizer import normalize_signals, normalize_signal_item, _parse_view_count
from trend_engine.processing.clustering import cluster_items
from trend_engine.processing.deduplicator import Deduplicator
from trend_engine.utils.text import clean_text, extract_words, is_similar, normalize_keyword


class TestTextUtils:
    def test_clean_text_removes_urls(self):
        result = clean_text("check this https://example.com")
        assert "check this" in result
        assert "https://" not in result

    def test_clean_text_removes_html(self):
        assert "<b>" not in clean_text("<b>bold</b>")

    def test_extract_words_filters_stop_words(self):
        words = extract_words("và các công nghệ mới trong lĩnh vực ai")
        assert "và" not in words
        assert "các" not in words
        assert "trong" not in words

    def test_is_similar(self):
        assert is_similar("ai agents", "ai agent", threshold=0.7)
        assert not is_similar("ai agents", "cooking recipe", threshold=0.7)

    def test_normalize_keyword(self):
        assert normalize_keyword("  AI Agents  ") == "ai agents"


class TestNormalizer:
    def test_normalize_google_trends(self):
        result = normalize_signal_item(
            {"query": "AI agents", "volume": 100, "type": "trending_search"},
            "google_trends",
        )
        assert result["text"] == "ai agents"
        assert result["volume"] == 100
        assert result["source"] == "google_trends"

    def test_normalize_news(self):
        result = normalize_signal_item(
            {"title": "New AI Model", "url": "https://ex.com", "snippet": "Details here"},
            "news_firecrawl",
        )
        assert result["text"] == "new ai model"
        assert result["url"] == "https://ex.com"

    def test_normalize_tiktok(self):
        result = normalize_signal_item(
            {"tag": "#coding", "views": "5.2M", "type": "trending_hashtag"},
            "tiktok",
        )
        assert result["text"] == "coding"
        assert result["volume"] == 5_200_000

    def test_parse_view_count(self):
        assert _parse_view_count("5.2M") == 5_200_000
        assert _parse_view_count("1.3K") == 1_300
        assert _parse_view_count("500") == 500
        assert _parse_view_count("2B") == 2_000_000_000

    def test_normalize_signals(self):
        signals = [
            RawSignal(source="google_trends", collected_at="2025-01-01", items=[
                {"query": "AI", "volume": 100, "type": "trending"},
            ]),
            RawSignal(source="tiktok", collected_at="2025-01-01", items=[
                {"tag": "#AI", "views": 5000, "type": "trending_hashtag"},
            ]),
        ]
        result = normalize_signals(signals)
        assert len(result) == 2
        assert all(r["text"] for r in result)


class TestClustering:
    def test_similar_items_cluster_together(self):
        items = [
            {"text": "ai agents", "volume": 100, "source": "google_trends"},
            {"text": "ai agent", "volume": 50, "source": "tiktok"},
            {"text": "cooking recipe", "volume": 30, "source": "news_firecrawl"},
        ]
        clusters = cluster_items(items, similarity_threshold=0.7)
        # "ai agents" and "ai agent" should cluster, "cooking recipe" separate
        assert len(clusters) == 2

    def test_identical_items_merge(self):
        items = [
            {"text": "python", "volume": 100, "source": "google_trends"},
            {"text": "python", "volume": 200, "source": "tiktok"},
        ]
        clusters = cluster_items(items)
        assert len(clusters) == 1
        assert clusters[0].signals_summary["total_volume"] == 300
        assert len(clusters[0].sources_present) == 2

    def test_empty_input(self):
        assert cluster_items([]) == []


class TestDeduplicator:
    def test_full_pipeline(self):
        signals = [
            RawSignal(source="google_trends", collected_at="2025-01-01", items=[
                {"query": "AI agents", "volume": 100, "type": "trending"},
                {"query": "coding", "volume": 80, "type": "trending"},
            ]),
            RawSignal(source="tiktok", collected_at="2025-01-01", items=[
                {"tag": "#AI", "views": 5000, "type": "trending_hashtag"},
                {"tag": "#python", "views": 3000, "type": "trending_hashtag"},
            ]),
        ]
        dedup = Deduplicator()
        clusters = dedup.deduplicate(signals)

        assert len(clusters) > 0
        assert all(isinstance(c, TopicCluster) for c in clusters)
        # Should be sorted by volume desc
        volumes = [c.signals_summary.get("total_volume", 0) for c in clusters]
        assert volumes == sorted(volumes, reverse=True)
