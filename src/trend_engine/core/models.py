"""
Core data models (data contracts)
"""

from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class RawSignal:
    source: str
    collected_at: str
    items: List[Dict[str, Any]]


@dataclass
class TopicCluster:
    topic_id: str
    canonical_name: str
    keywords: List[str]
    sources_present: List[str]
    signals_summary: Dict[str, Any]


@dataclass
class TrendResult:
    trend_id: str
    topic: str
    trend_type: str
    trend_score: float
    confidence: float
    time_window: str
    why_trending: List[str]
    sources: List[str]
    evidence: List[Dict[str, Any]]
    suggested_actions: Dict[str, List[str]]
