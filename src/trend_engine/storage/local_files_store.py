"""
Local file storage (JSON)
"""

import json
from pathlib import Path
from typing import Any

from trend_engine.storage.base_store import BaseStore


class LocalFilesStore(BaseStore):

    def save(self, data: Any, path: str):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load(self, path: str) -> Any:
        p = Path(path)
        if not p.exists():
            return None
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
