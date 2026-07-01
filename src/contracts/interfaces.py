"""Typed interfaces for modular, swappable pipeline components."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, Protocol, Sequence

from .domain import Candidate, JobDescription, RankedCandidate


class DatasetInventoryProvider(Protocol):
    """Discovers available datasets and related docs in a repository."""

    def discover(self, repository_root: Path) -> dict:
        """Return inventory metadata for datasets and companion files."""


class CandidateLoader(Protocol):
    """Streams canonical candidates from raw candidate storage."""

    def load(self, dataset_path: Path) -> Iterable[Candidate]:
        """Yield candidate objects from a source dataset."""


class RawRecordLoader(Protocol):
    """Streams raw dictionary records from source datasets."""

    def load_raw(self, dataset_path: Path) -> Iterable[Dict[str, Any]]:
        """Yield raw object records from source dataset."""


class CandidateValidator(Protocol):
    """Validates candidate records and reports actionable issues."""

    def validate(self, candidate: Candidate) -> Sequence[str]:
        """Return validation issues for a candidate, empty sequence if valid."""


class CandidateNormalizer(Protocol):
    """Normalizes raw candidate dictionaries before parsing."""

    def normalize(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Return deterministic normalized dictionary representation."""


class FeatureExtractor(Protocol):
    """Extracts reusable features independent of ranking algorithm."""

    def extract(self, candidate: Candidate) -> Any:
        """Return feature object derived from the candidate."""


class JobParser(Protocol):
    """Parses a raw job document into a canonical JobDescription."""

    def parse(self, job_source: Path) -> JobDescription:
        """Parse a job document source path."""


class Retriever(Protocol):
    """Retrieves top-k candidate IDs for ranking."""

    def retrieve(self, job: JobDescription, candidates: Iterable[Candidate], k: int) -> Sequence[Candidate]:
        """Return top-k retrieved candidates for the job."""


class Ranker(Protocol):
    """Ranks retrieved candidates and returns explainable outputs."""

    def rank(self, job: JobDescription, candidates: Sequence[Candidate], top_n: int) -> Sequence[RankedCandidate]:
        """Return sorted ranked candidates with evidence and reasoning."""


class SubmissionWriter(Protocol):
    """Writes ranked candidates to challenge-compliant CSV format."""

    def write(self, ranked: Sequence[RankedCandidate], output_csv: Path) -> None:
        """Persist CSV output with header and 100 ranked rows."""
