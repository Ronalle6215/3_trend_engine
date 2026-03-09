"""
CLI entrypoint
"""

import argparse
import sys

from trend_engine.core.logging import get_logger
from trend_engine.core.time_window import validate_time_window
from trend_engine.config.settings import settings
from trend_engine.pipelines.collect_pipeline import CollectPipeline
from trend_engine.pipelines.detect_pipeline import DetectPipeline
from trend_engine.pipelines.export_pipeline import ExportPipeline

logger = get_logger(__name__)


def _run_collect(window: str):
    logger.info(f"Running Collect Pipeline (window={window})...")
    pipeline = CollectPipeline()
    signals = pipeline.run(window)
    logger.info(f"Collected {len(signals)} signal groups.")
    return signals


def _run_detect(signals, top_n: int):
    logger.info("Running Detect Pipeline...")
    pipeline = DetectPipeline()
    trends = pipeline.run(signals, top_n=top_n)
    logger.info(f"Detected {len(trends)} trends.")
    return trends


def _run_export(trends):
    logger.info("Running Export Pipeline...")
    pipeline = ExportPipeline()
    path = pipeline.run(trends)
    logger.info(f"Export complete → {path}")
    return path


def main():
    parser = argparse.ArgumentParser(description="Trend Engine CLI")
    parser.add_argument("command", choices=["collect", "detect", "export", "all", "schedule"])
    parser.add_argument("--window", default=settings.default_window)
    parser.add_argument("--top", type=int, default=settings.top_n)
    parser.add_argument("--interval", default=None, help="Schedule interval, e.g. 6h, 30m")

    args = parser.parse_args()

    try:
        window = validate_time_window(args.window)
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)

    if args.command == "all":
        signals = _run_collect(window)
        trends = _run_detect(signals, args.top)
        _run_export(trends)

    elif args.command == "collect":
        _run_collect(window)

    elif args.command == "detect":
        # Load latest signals from storage, or run collect as fallback
        logger.info("Standalone detect: running collect first...")
        signals = _run_collect(window)
        _run_detect(signals, args.top)

    elif args.command == "export":
        # Run full pipeline for standalone export
        logger.info("Standalone export: running full pipeline...")
        signals = _run_collect(window)
        trends = _run_detect(signals, args.top)
        _run_export(trends)

    elif args.command == "schedule":
        from trend_engine.scheduler import TrendScheduler

        interval_str = args.interval or f"{settings.schedule_interval_hours}h"
        scheduler = TrendScheduler(
            window=window,
            top_n=args.top,
            interval_str=interval_str,
        )
        scheduler.start()


if __name__ == "__main__":
    main()
