"""JSONL reading utilities for large candidate datasets."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Generator, Tuple


def iter_jsonl_records(path: Path) -> Generator[Tuple[int, Dict[str, object]], None, None]:
    """Yield line-numbered JSON objects from a JSONL file.

    Raises:
        FileNotFoundError: If the path does not exist.
        ValueError: If a non-empty line is not valid JSON.
    """

    if not path.exists():
        raise FileNotFoundError(f"JSONL file not found: {path}")

    with path.open("r", encoding="utf-8") as fp:
        for line_number, line in enumerate(fp, start=1):
            content = line.strip()
            if not content:
                continue
            try:
                obj = json.loads(content)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON at line {line_number} in {path}: {exc.msg}"
                ) from exc
            if not isinstance(obj, dict):
                raise ValueError(
                    f"Line {line_number} in {path} must decode to object, got {type(obj).__name__}"
                )
            yield line_number, obj
