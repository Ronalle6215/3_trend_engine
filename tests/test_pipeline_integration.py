"""
Integration test — full pipeline with mocked collectors
"""

import sys
import os
import json
import tempfile
from unittest.mock import patch, MagicMock
from pathlib import Path

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from trend_engine.core.models import RawSignal


def _mock_signals():
    return [
        RawSignal(source="google_trends", collected_at="2025-01-01T00:00:00", items=[
            {"query": "AI agents", "volume": 100, "type": "trending_search"},
            {"query": "Python 4", "volume": 80, "type": "trending_search"},
            {"query": "giáo dục AI", "volume": 60, "type": "seed_keyword"},
        ]),
        RawSignal(source="news_firecrawl", collected_at="2025-01-01T00:00:00", items=[
            {"title": "AI Agent Revolution", "url": "https://ex.com/1", "snippet": "Big news"},
            {"title": "Python Future", "url": "https://ex.com/2", "snippet": "New version"},
        ]),
        RawSignal(source="tiktok", collected_at="2025-01-01T00:00:00", items=[
            {"tag": "#AI", "views": 5000000, "type": "trending_hashtag"},
            {"tag": "#coding", "views": 3000000, "type": "trending_hashtag"},
        ]),
    ]


class TestFullPipeline:
    @patch("trend_engine.config.settings.settings")
    def test_collect_detect_export(self, mock_settings):
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_settings.data_dir = Path(tmpdir)
            mock_settings.default_window = "24h"
            mock_settings.top_n = 10
            mock_settings.gemini_api_key = ""  # Skip Gemini

            from trend_engine.pipelines.detect_pipeline import DetectPipeline
            from trend_engine.pipelines.export_pipeline import ExportPipeline

            signals = _mock_signals()

            # Detect
            detect = DetectPipeline()
            trends = detect.run(signals, top_n=10)

            assert len(trends) > 0
            assert all(t.trend_score > 0 for t in trends)
            assert all(t.topic for t in trends)

            # Export
            export = ExportPipeline()
            export_path = export.run(trends)

            assert Path(export_path).exists()

            with open(export_path) as f:
                data = json.load(f)
            assert len(data) == len(trends)
            assert "trend_id" in data[0]
            assert "topic" in data[0]
            assert "trend_score" in data[0]

    def test_sqlite_persistence(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            from trend_engine.storage.sqlite_store import SQLiteStore

            store = SQLiteStore(db_path=db_path)
            run_id = store.start_run("24h")

            signals = _mock_signals()
            store.save_signals(run_id, signals)

            from trend_engine.pipelines.detect_pipeline import DetectPipeline

            with patch("trend_engine.scoring.trend_scorer.settings") as mock_s:
                mock_s.gemini_api_key = ""
                mock_s.default_window = "24h"
                detect = DetectPipeline()
                trends = detect.run(signals, top_n=5)

            store.save_trends(run_id, trends)
            store.complete_run(run_id, sum(len(s.items) for s in signals), len(trends))

            # Verify
            latest = store.get_latest_trends(limit=10)
            assert len(latest) > 0
            assert latest[0]["trend_score"] > 0

            runs = store.get_run_history()
            assert len(runs) == 1
            assert runs[0]["status"] == "completed"
