"""Architecture-level pipeline contracts and execution context.

Phase 1 provides system architecture scaffolding only. Concrete ingestion,
retrieval, and ranking implementations are intentionally deferred to later
phases.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from src.config.settings import RuntimeSettings
from src.contracts.domain import RankedCandidate


@dataclass(frozen=True)
class PipelineContext:
    """Immutable context shared across pipeline stages."""

    settings: RuntimeSettings
    run_id: str
    job_document_path: Path


class SystemPipeline:
    """Top-level pipeline entry point.

    This class intentionally exposes only architecture-level behavior in
    README_01. Functional ranking logic is implemented in later phases.
    """

    def __init__(self, context: PipelineContext) -> None:
        self._context = context

    @property
    def context(self) -> PipelineContext:
        """Read-only pipeline context."""

        return self._context

    def execute(self) -> Sequence[RankedCandidate]:
        """Run pipeline.

        Raises:
            NotImplementedError: Phase 1 architecture scaffold only.
        """

        raise NotImplementedError(
            "SystemPipeline.execute is intentionally deferred to later phases "
            "after backend and ranking modules are implemented."
        )
