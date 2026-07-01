"""Performance and memory profiling helpers for QA validation."""

from __future__ import annotations

import time
import tracemalloc
from dataclasses import dataclass

from src.config.settings import AppSettings
from src.pipelines.ranking_pipeline import RankingPipeline


@dataclass(frozen=True)
class RankingProfile:
    """Runtime profile for one ranking pipeline execution."""

    total_duration_ms: float
    peak_memory_mb: float
    scanned_candidates: int
    ranked_candidates: int


def profile_ranking_pipeline(settings: AppSettings) -> RankingProfile:
    """Profile ranking runtime and memory usage under current settings."""

    tracemalloc.start()
    start = time.perf_counter()
    ranked, summary = RankingPipeline(settings).execute()
    duration_ms = (time.perf_counter() - start) * 1000
    _, peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return RankingProfile(
        total_duration_ms=duration_ms,
        peak_memory_mb=peak_bytes / (1024 * 1024),
        scanned_candidates=summary.scanned_candidates,
        ranked_candidates=len(ranked),
    )
