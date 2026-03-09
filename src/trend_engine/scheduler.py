"""
Scheduler — auto-runs the full pipeline at configured intervals
"""

import signal
import sys
from datetime import datetime

from apscheduler.schedulers.blocking import BlockingScheduler

from trend_engine.core.logging import get_logger
from trend_engine.config.settings import settings
from trend_engine.pipelines.collect_pipeline import CollectPipeline
from trend_engine.pipelines.detect_pipeline import DetectPipeline
from trend_engine.pipelines.export_pipeline import ExportPipeline
from trend_engine.storage.sqlite_store import SQLiteStore

logger = get_logger(__name__)


def _parse_interval(interval_str: str) -> dict:
    """Parse interval string like '6h', '30m', '1d' into APScheduler kwargs."""
    val = int(interval_str[:-1])
    unit = interval_str[-1].lower()
    if unit == "h":
        return {"hours": val}
    elif unit == "m":
        return {"minutes": val}
    elif unit == "d":
        return {"days": val}
    raise ValueError(f"Invalid interval format: {interval_str}. Use e.g. 6h, 30m, 1d")


class TrendScheduler:
    def __init__(self, window: str = "24h", top_n: int = 20, interval_str: str = "6h"):
        self.window = window
        self.top_n = top_n
        self.interval_str = interval_str
        self.db = SQLiteStore()
        self.scheduler = BlockingScheduler()

    def _run_pipeline(self):
        """Execute the full pipeline once."""
        run_start = datetime.now()
        logger.info(f"{'='*60}")
        logger.info(f"Scheduled run started at {run_start.isoformat()}")
        logger.info(f"{'='*60}")

        run_id = self.db.start_run(self.window)

        try:
            # Collect
            collect = CollectPipeline()
            signals = collect.run(self.window)
            self.db.save_signals(run_id, signals)

            # Detect
            detect = DetectPipeline()
            trends = detect.run(signals, top_n=self.top_n)
            self.db.save_trends(run_id, trends)

            # Export
            export = ExportPipeline()
            export.run(trends)

            # Complete
            total_items = sum(len(s.items) for s in signals)
            self.db.complete_run(run_id, total_items, len(trends))

            elapsed = (datetime.now() - run_start).total_seconds()
            logger.info(f"Run #{run_id} complete: {total_items} items → {len(trends)} trends ({elapsed:.1f}s)")

        except Exception as e:
            logger.error(f"Run #{run_id} failed: {e}")
            self.db.complete_run(run_id, 0, 0)

    def start(self):
        """Start the scheduler."""
        interval_kwargs = _parse_interval(self.interval_str)

        logger.info(f"Trend Engine Scheduler starting...")
        logger.info(f"  Window: {self.window}")
        logger.info(f"  Top N: {self.top_n}")
        logger.info(f"  Interval: {self.interval_str}")
        logger.info(f"  Press Ctrl+C to stop")

        # Run once immediately
        self._run_pipeline()

        # Schedule recurring runs
        self.scheduler.add_job(
            self._run_pipeline,
            "interval",
            **interval_kwargs,
            id="trend_pipeline",
            name="Trend Engine Pipeline",
        )

        # Graceful shutdown
        def _shutdown(signum, frame):
            logger.info("Shutting down scheduler...")
            self.scheduler.shutdown(wait=False)
            sys.exit(0)

        signal.signal(signal.SIGINT, _shutdown)
        signal.signal(signal.SIGTERM, _shutdown)

        try:
            self.scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            logger.info("Scheduler stopped.")
