"""
Deduplicator — normalizes signals then clusters into TopicClusters
"""

from typing import List

from trend_engine.core.logging import get_logger
from trend_engine.core.models import RawSignal, TopicCluster
from trend_engine.processing.normalizer import normalize_signals
from trend_engine.processing.clustering import cluster_items

logger = get_logger(__name__)


class Deduplicator:
    def deduplicate(self, signals: List[RawSignal]) -> List[TopicCluster]:
        # Step 1: Normalize all signal items into unified format
        normalized = normalize_signals(signals)

        # Step 2: Cluster similar items together
        clusters = cluster_items(normalized, similarity_threshold=0.6)

        # Step 3: Sort by total volume (highest first)
        clusters.sort(
            key=lambda c: c.signals_summary.get("total_volume", 0),
            reverse=True,
        )

        logger.info(f"Deduplication: {sum(len(s.items) for s in signals)} raw items → {len(clusters)} unique topics")
        return clusters
