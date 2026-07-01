"""Experiment tracking utilities for reproducible evaluation runs."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class ExperimentRecord:
    """Serializable metadata and metrics for one evaluation experiment."""

    experiment_id: str
    timestamp_utc: str
    config_snapshot: Dict[str, Any]
    dataset_version: str
    model_summary: Dict[str, Any]
    hyperparameters: Dict[str, Any]
    metrics: Dict[str, Any]
    observations: str
    decision: str
    git_commit: Optional[str] = None


class ExperimentTracker:
    """Appends experiment records to JSONL registry."""

    def __init__(self, output_path: Path) -> None:
        self._output_path = output_path
        self._output_path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, record: ExperimentRecord) -> None:
        with self._output_path.open("a", encoding="utf-8") as fp:
            fp.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")

    @staticmethod
    def build_record(
        experiment_id: str,
        config_snapshot: Dict[str, Any],
        dataset_version: str,
        model_summary: Dict[str, Any],
        hyperparameters: Dict[str, Any],
        metrics: Dict[str, Any],
        observations: str,
        decision: str,
        git_commit: Optional[str] = None,
    ) -> ExperimentRecord:
        return ExperimentRecord(
            experiment_id=experiment_id,
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
            config_snapshot=config_snapshot,
            dataset_version=dataset_version,
            model_summary=model_summary,
            hyperparameters=hyperparameters,
            metrics=metrics,
            observations=observations,
            decision=decision,
            git_commit=git_commit,
        )
