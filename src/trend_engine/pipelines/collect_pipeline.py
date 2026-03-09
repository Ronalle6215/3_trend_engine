"""
Collect pipeline — runs enabled collectors from config
"""

from typing import List

from trend_engine.core.models import RawSignal
from trend_engine.core.logging import get_logger
from trend_engine.config.settings import settings

logger = get_logger(__name__)

# Registry of available collectors
_COLLECTOR_MAP = {
    "google_trends": "trend_engine.collectors.google_trends_collector.GoogleTrendsCollector",
    "news_firecrawl": "trend_engine.collectors.firecrawl_news_collector.FirecrawlNewsCollector",
    "tiktok": "trend_engine.collectors.tiktok_collector.TikTokCollector",
}


def _load_collector(dotted_path: str):
    module_path, class_name = dotted_path.rsplit(".", 1)
    import importlib
    module = importlib.import_module(module_path)
    return getattr(module, class_name)()


class CollectPipeline:
    def __init__(self):
        self.collectors = []
        enabled = settings.enabled_sources

        for source_name, config in enabled.items():
            # config can be True or a dict like {"shopee": true, "lazada": true}
            if isinstance(config, bool) and config:
                if source_name in _COLLECTOR_MAP:
                    self.collectors.append((source_name, _COLLECTOR_MAP[source_name]))
                else:
                    logger.warning(f"No collector implemented for source: {source_name}")
            elif isinstance(config, dict):
                # Sub-sources (e.g. ecommerce.shopee) — skip for now
                logger.info(f"Sub-source '{source_name}' skipped (not yet implemented)")

        logger.info(f"Enabled collectors: {[name for name, _ in self.collectors]}")

    def run(self, window: str) -> List[RawSignal]:
        signals = []
        for name, dotted_path in self.collectors:
            try:
                logger.info(f"Collecting from '{name}'...")
                collector = _load_collector(dotted_path)
                signal = collector.collect(window)
                signals.append(signal)
                logger.info(f"'{name}': collected {len(signal.items)} items")
            except Exception as e:
                logger.error(f"Collector '{name}' failed: {e}")
                continue

        logger.info(f"Collection complete: {len(signals)} sources, {sum(len(s.items) for s in signals)} total items")
        return signals
