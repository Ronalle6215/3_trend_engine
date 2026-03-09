"""
SQLite storage — persistent trend history
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from trend_engine.core.logging import get_logger
from trend_engine.config.settings import settings

logger = get_logger(__name__)


class SQLiteStore:
    def __init__(self, db_path: str | Path | None = None):
        self.db_path = str(db_path or settings.db_path)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    started_at TEXT NOT NULL,
                    completed_at TEXT,
                    window TEXT,
                    signals_count INTEGER DEFAULT 0,
                    trends_count INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'running'
                );

                CREATE TABLE IF NOT EXISTS signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id INTEGER NOT NULL,
                    source TEXT NOT NULL,
                    collected_at TEXT NOT NULL,
                    items_json TEXT NOT NULL,
                    items_count INTEGER DEFAULT 0,
                    FOREIGN KEY (run_id) REFERENCES runs(id)
                );

                CREATE TABLE IF NOT EXISTS trends (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id INTEGER NOT NULL,
                    trend_id TEXT NOT NULL,
                    topic TEXT NOT NULL,
                    trend_type TEXT,
                    trend_score REAL DEFAULT 0,
                    confidence REAL DEFAULT 0,
                    time_window TEXT,
                    why_trending_json TEXT,
                    sources_json TEXT,
                    evidence_json TEXT,
                    suggested_actions_json TEXT,
                    detected_at TEXT NOT NULL,
                    FOREIGN KEY (run_id) REFERENCES runs(id)
                );

                CREATE INDEX IF NOT EXISTS idx_trends_topic ON trends(topic);
                CREATE INDEX IF NOT EXISTS idx_trends_score ON trends(trend_score DESC);
                CREATE INDEX IF NOT EXISTS idx_trends_detected ON trends(detected_at);
            """)
        logger.info(f"SQLite DB ready: {self.db_path}")

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def start_run(self, window: str) -> int:
        with self._connect() as conn:
            cursor = conn.execute(
                "INSERT INTO runs (started_at, window) VALUES (?, ?)",
                (datetime.now().isoformat(), window),
            )
            return cursor.lastrowid

    def complete_run(self, run_id: int, signals_count: int, trends_count: int):
        with self._connect() as conn:
            conn.execute(
                "UPDATE runs SET completed_at=?, signals_count=?, trends_count=?, status='completed' WHERE id=?",
                (datetime.now().isoformat(), signals_count, trends_count, run_id),
            )

    def save_signals(self, run_id: int, signals: list[Any]):
        with self._connect() as conn:
            for signal in signals:
                conn.execute(
                    "INSERT INTO signals (run_id, source, collected_at, items_json, items_count) VALUES (?, ?, ?, ?, ?)",
                    (run_id, signal.source, signal.collected_at, json.dumps(signal.items, ensure_ascii=False), len(signal.items)),
                )

    def save_trends(self, run_id: int, trends: list[Any]):
        with self._connect() as conn:
            for trend in trends:
                conn.execute(
                    """INSERT INTO trends
                    (run_id, trend_id, topic, trend_type, trend_score, confidence,
                     time_window, why_trending_json, sources_json, evidence_json,
                     suggested_actions_json, detected_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        run_id, trend.trend_id, trend.topic, trend.trend_type,
                        trend.trend_score, trend.confidence, trend.time_window,
                        json.dumps(trend.why_trending, ensure_ascii=False),
                        json.dumps(trend.sources, ensure_ascii=False),
                        json.dumps(trend.evidence, ensure_ascii=False),
                        json.dumps(trend.suggested_actions, ensure_ascii=False),
                        datetime.now().isoformat(),
                    ),
                )

    def get_latest_trends(self, limit: int = 20) -> list[dict]:
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM trends ORDER BY detected_at DESC, trend_score DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(row) for row in rows]

    def get_trend_history(self, topic: str, limit: int = 10) -> list[dict]:
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM trends WHERE topic LIKE ? ORDER BY detected_at DESC LIMIT ?",
                (f"%{topic}%", limit),
            ).fetchall()
            return [dict(row) for row in rows]

    def get_run_history(self, limit: int = 10) -> list[dict]:
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM runs ORDER BY started_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(row) for row in rows]
