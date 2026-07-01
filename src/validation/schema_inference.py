"""Schema inference over JSONL candidate records."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Dict, Iterable

from src.ingestion.jsonl_reader import iter_jsonl_records


def infer_candidate_schema_stats(candidates_path: Path, sample_limit: int | None = None) -> Dict[str, object]:
    """Infer structural schema statistics from candidate JSONL data."""

    top_level_keys: Counter[str] = Counter()
    profile_keys: Counter[str] = Counter()
    signal_keys: Counter[str] = Counter()
    records = 0

    for _, record in iter_jsonl_records(candidates_path):
        records += 1
        for key in record.keys():
            top_level_keys[key] += 1

        profile = record.get("profile")
        if isinstance(profile, dict):
            for key in profile.keys():
                profile_keys[key] += 1

        signals = record.get("redrob_signals")
        if isinstance(signals, dict):
            for key in signals.keys():
                signal_keys[key] += 1

        if sample_limit is not None and records >= sample_limit:
            break

    return {
        "records_scanned": records,
        "top_level_keys": dict(sorted(top_level_keys.items())),
        "profile_keys": dict(sorted(profile_keys.items())),
        "redrob_signal_keys": dict(sorted(signal_keys.items())),
    }
