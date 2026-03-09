"""
Application settings — loads .env + sources.yaml
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
CONFIG_DIR = Path(__file__).resolve().parent


def _load_sources_yaml() -> dict[str, Any]:
    path = CONFIG_DIR / "sources.yaml"
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


@dataclass
class Settings:
    app_name: str = os.getenv("APP_NAME", "Trend Engine")
    default_language: str = os.getenv("DEFAULT_LANGUAGE", "vi")

    # API keys
    firecrawl_api_key: str = os.getenv("FIRECRAWL_API_KEY", "")
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")

    # Scheduler
    schedule_interval_hours: int = int(os.getenv("SCHEDULE_INTERVAL_HOURS", "6"))

    # Paths
    project_root: Path = PROJECT_ROOT
    data_dir: Path = PROJECT_ROOT / "data"
    db_path: Path = PROJECT_ROOT / "data" / "trend_engine.db"

    # Sources config (loaded from YAML)
    sources: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        self.sources = _load_sources_yaml()
        self.data_dir.mkdir(parents=True, exist_ok=True)

    @property
    def seed_keywords(self) -> list[str]:
        return self.sources.get("seed_keywords", [])

    @property
    def enabled_sources(self) -> dict[str, Any]:
        return self.sources.get("sources", {})

    @property
    def top_n(self) -> int:
        return self.sources.get("ranking", {}).get("top_n", 20)

    @property
    def default_window(self) -> str:
        return self.sources.get("time_window", {}).get("default", "24h")


settings = Settings()
