"""
Trend feature extractors — compute scoring features for each TopicCluster
"""

from typing import Any

from trend_engine.core.models import TopicCluster


def volume_score(cluster: TopicCluster) -> float:
    """Score based on total signal volume (log-scaled)."""
    import math
    total = cluster.signals_summary.get("total_volume", 0)
    if total <= 0:
        return 0.0
    return min(100.0, math.log10(max(total, 1)) * 25)


def source_diversity(cluster: TopicCluster) -> float:
    """Score based on how many data sources mention this topic (0-100)."""
    count = len(cluster.sources_present)
    # 1 source = 33, 2 = 66, 3 = 100
    return min(100.0, count * 33.3)


def mention_density(cluster: TopicCluster) -> float:
    """Score based on total number of mentions across items."""
    mentions = cluster.signals_summary.get("total_mentions", 0)
    if mentions <= 0:
        return 0.0
    return min(100.0, mentions * 10)


def recency_boost(cluster: TopicCluster) -> float:
    """Boost for recently collected signals. For now, all signals are recent (just collected)."""
    # In future, compare collected_at vs now() for time-decay
    return 50.0


def compute_features(cluster: TopicCluster) -> dict[str, float]:
    """Compute all features for a cluster."""
    return {
        "volume": volume_score(cluster),
        "diversity": source_diversity(cluster),
        "mentions": mention_density(cluster),
        "recency": recency_boost(cluster),
    }
