"""Backend orchestration pipeline for ingestion through feature extraction."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

from src.cache.json_cache import JsonFileCache
from src.config.settings import AppSettings, load_config, parse_app_settings
from src.ingestion.discovery import RepositoryDiscovery
from src.ingestion.jsonl_reader import iter_jsonl_records
from src.monitoring.metrics import PipelineMetrics, StageMetric
from src.parsing.candidate_parser import CandidateParser
from src.parsing.job_parser import JobDescriptionParser
from src.preprocessing.feature_extraction import CandidateFeatureExtractor
from src.qa.preflight import RepositoryHealthChecker
from src.preprocessing.normalization import normalize_candidate_record
from src.validation.candidate_validation import (
    CanonicalCandidateValidator,
    RawCandidateRecordValidator,
)
from src.validation.schema_inference import infer_candidate_schema_stats


@dataclass(frozen=True)
class BackendPipelineSummary:
    """Summary artifact produced by backend pipeline execution."""

    scanned_candidates: int
    parsed_candidates: int
    validation_failures: int
    schema_records_scanned: int
    inventory_dataset_files: int
    job_title: str
    metrics: Dict[str, float]


class BackendPipeline:
    """Runs backend engineering stages in deterministic order."""

    def __init__(self, app_settings: AppSettings) -> None:
        self._settings = app_settings
        self._discovery = RepositoryDiscovery()
        self._raw_validator = RawCandidateRecordValidator()
        self._canonical_validator = CanonicalCandidateValidator()
        self._candidate_parser = CandidateParser()
        self._job_parser = JobDescriptionParser()
        self._feature_extractor = CandidateFeatureExtractor()
        self._preflight = RepositoryHealthChecker()
        self._metrics = PipelineMetrics()

    @classmethod
    def from_config_file(cls, config_path: Path) -> "BackendPipeline":
        raw = load_config(config_path)
        settings = parse_app_settings(raw)
        return cls(settings)

    def execute(self) -> BackendPipelineSummary:
        runtime = self._settings.runtime
        self._preflight.ensure_healthy(self._settings)
        cache = JsonFileCache(Path(runtime.repository_root) / "artifacts" / "cache")

        t0 = time.perf_counter()
        inventory = self._discovery.discover(Path(runtime.repository_root))
        self._metrics.add(
            StageMetric(
                stage_name="discovery",
                duration_ms=(time.perf_counter() - t0) * 1000,
                processed_records=len(inventory.datasets),
            )
        )

        schema_cache_key = f"schema::{runtime.candidates_path}"
        t1 = time.perf_counter()
        schema = cache.get(schema_cache_key)
        cache_hit = 1.0 if schema is not None else 0.0
        if schema is None:
            schema = infer_candidate_schema_stats(Path(runtime.candidates_path), sample_limit=5000)
            cache.set(schema_cache_key, schema)
        self._metrics.add(
            StageMetric(
                stage_name="schema_inference",
                duration_ms=(time.perf_counter() - t1) * 1000,
                processed_records=int(schema.get("records_scanned", 0)),
                extras={"cache_hit": cache_hit},
            )
        )

        t2 = time.perf_counter()
        job = self._job_parser.parse(Path(runtime.job_description_path))
        self._metrics.add(
            StageMetric(
                stage_name="job_parsing",
                duration_ms=(time.perf_counter() - t2) * 1000,
                processed_records=1,
            )
        )

        scanned = 0
        parsed = 0
        failures = 0

        t3 = time.perf_counter()
        for _, raw_record in iter_jsonl_records(Path(runtime.candidates_path)):
            scanned += 1
            normalized = normalize_candidate_record(raw_record)

            raw_issues = self._raw_validator.validate(normalized)
            if raw_issues:
                failures += 1
                if runtime.strict_validation:
                    continue

            candidate = self._candidate_parser.parse(normalized)
            candidate_issues = self._canonical_validator.validate(candidate)
            if candidate_issues:
                failures += 1
                if runtime.strict_validation:
                    continue

            _ = self._feature_extractor.extract(candidate)
            parsed += 1

            if runtime.max_candidates_to_process is not None and scanned >= runtime.max_candidates_to_process:
                break

        self._metrics.add(
            StageMetric(
                stage_name="candidate_processing",
                duration_ms=(time.perf_counter() - t3) * 1000,
                processed_records=scanned,
                failures=failures,
            )
        )

        return BackendPipelineSummary(
            scanned_candidates=scanned,
            parsed_candidates=parsed,
            validation_failures=failures,
            schema_records_scanned=int(schema.get("records_scanned", 0)),
            inventory_dataset_files=len(inventory.datasets),
            job_title=job.role_title,
            metrics=self._metrics.summary(),
        )
