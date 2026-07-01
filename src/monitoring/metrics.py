"""Operational metrics models for backend observability."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(frozen=True)
class StageMetric:
    """Metric emitted for a single stage execution."""

    stage_name: str
    duration_ms: float
    processed_records: int
    warnings: int = 0
    failures: int = 0
    extras: Dict[str, float] = field(default_factory=dict)


@dataclass
class PipelineMetrics:
    """Aggregates stage-level metrics."""

    stages: List[StageMetric] = field(default_factory=list)

    def add(self, metric: StageMetric) -> None:
        self.stages.append(metric)

    def summary(self) -> Dict[str, float]:
        total_duration = sum(stage.duration_ms for stage in self.stages)
        total_processed = sum(stage.processed_records for stage in self.stages)
        total_warnings = sum(stage.warnings for stage in self.stages)
        total_failures = sum(stage.failures for stage in self.stages)
        return {
            "total_duration_ms": total_duration,
            "total_processed_records": float(total_processed),
            "total_warnings": float(total_warnings),
            "total_failures": float(total_failures),
        }
