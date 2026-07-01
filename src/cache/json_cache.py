"""Deterministic JSON file cache for reusable pipeline artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Optional


class JsonFileCache:
    """Simple hash-keyed JSON cache with deterministic invalidation."""

    def __init__(self, cache_dir: Path) -> None:
        self._cache_dir = cache_dir
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    def _cache_path(self, key: str) -> Path:
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
        return self._cache_dir / f"{digest}.json"

    def get(self, key: str) -> Optional[Any]:
        path = self._cache_path(key)
        if not path.exists():
            return None
        with path.open("r", encoding="utf-8") as fp:
            return json.load(fp)

    def set(self, key: str, value: Any) -> None:
        path = self._cache_path(key)
        with path.open("w", encoding="utf-8") as fp:
            json.dump(value, fp, ensure_ascii=False, indent=2)

    def invalidate(self, key: str) -> None:
        path = self._cache_path(key)
        if path.exists():
            path.unlink()

    def clear(self) -> None:
        for file_path in self._cache_dir.glob("*.json"):
            file_path.unlink()
