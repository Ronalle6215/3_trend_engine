"""
Export pipeline — saves trend results to JSON + SQLite
"""

from datetime import datetime
from typing import List
from dataclasses import asdict

from trend_engine.core.models import TrendResult
from trend_engine.core.logging import get_logger
from trend_engine.config.settings import settings
from trend_engine.storage.local_files_store import LocalFilesStore

logger = get_logger(__name__)


class ExportPipeline:
    def __init__(self):
        self.store = LocalFilesStore()

    def run(self, trends: List[TrendResult]) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        data = [asdict(t) for t in trends]

        # Always save latest
        latest_path = str(settings.data_dir / "trends_latest.json")
        self.store.save(data, latest_path)

        # Also save timestamped copy
        archive_path = str(settings.data_dir / f"trends_{timestamp}.json")
        self.store.save(data, archive_path)

        logger.info(f"Exported {len(trends)} trends → {latest_path}")
        return latest_path
