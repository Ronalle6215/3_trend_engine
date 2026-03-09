import sys
import os
import pytest
from unittest.mock import MagicMock

# Add src to path for import
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from trend_engine.core.models import RawSignal, TopicCluster
from trend_engine.processing.keyword_extractor import KeywordExtractor
from trend_engine.scoring.trend_scorer import TrendScorer

def test_keyword_extractor():
    extractor = KeywordExtractor()
    items = [
        {"text": "AI agents are the future"},
        {"text": "Future of AI agents"},
    ]
    keywords = extractor.extract(items)
    assert "agents" in keywords
    assert "future" in keywords

def test_trend_scorer():
    scorer = TrendScorer()
    cluster = TopicCluster(
        topic_id="test_topic",
        canonical_name="Test Topic",
        keywords=["test"],
        sources_present=["source1"],
        signals_summary={}
    )
    trends = scorer.score([cluster])
    assert len(trends) == 1
    assert trends[0].topic == "Test Topic"
    assert trends[0].trend_score > 0
