"""
Detect pipeline — processes signals into scored trends
"""

from typing import List

from trend_engine.core.logging import get_logger
from trend_engine.core.models import RawSignal, TrendResult
from trend_engine.processing.deduplicator import Deduplicator
from trend_engine.scoring.trend_scorer import TrendScorer

logger = get_logger(__name__)


class DetectPipeline:
    def __init__(self):
        self.deduplicator = Deduplicator()
        self.scorer = TrendScorer()

    def run(self, signals: List[RawSignal], top_n: int = 20) -> List[TrendResult]:
        # Step 1: Deduplicate + cluster
        clusters = self.deduplicator.deduplicate(signals)

        if not clusters:
            logger.warning("No clusters found after deduplication")
            return []

        # Step 2: Score + rank + enrich
        trends = self.scorer.score(clusters, top_n=top_n)

        logger.info(f"Detect pipeline: {len(trends)} trends detected")
        return trends
