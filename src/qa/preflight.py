"""Repository and runtime health checks for QA phase readiness."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

from src.config.settings import AppSettings


@dataclass(frozen=True)
class HealthCheckResult:
    """Structured repository health check output."""

    ok: bool
    errors: List[str]
    warnings: List[str]


class RepositoryHealthChecker:
    """Fail-fast checks for runtime prerequisites and repository integrity."""

    def run(self, settings: AppSettings, required_env_vars: Iterable[str] | None = None) -> HealthCheckResult:
        runtime = settings.runtime
        errors: List[str] = []
        warnings: List[str] = []

        repo_root = Path(runtime.repository_root)
        dataset_dir = Path(runtime.dataset_dir)
        candidates_path = Path(runtime.candidates_path)
        job_path = Path(runtime.job_description_path)
        submission_path = Path(runtime.submission_output_path)

        if not repo_root.exists() or not repo_root.is_dir():
            errors.append(f"repository_root does not exist or is not a directory: {repo_root}")

        if not dataset_dir.exists() or not dataset_dir.is_dir():
            errors.append(f"dataset_dir does not exist or is not a directory: {dataset_dir}")

        if not candidates_path.exists() or not candidates_path.is_file():
            errors.append(f"candidates_path does not exist or is not a file: {candidates_path}")
        elif candidates_path.suffix.lower() != ".jsonl":
            warnings.append(f"candidates_path does not use .jsonl extension: {candidates_path}")

        if not job_path.exists() or not job_path.is_file():
            errors.append(f"job_description_path does not exist or is not a file: {job_path}")

        if submission_path.suffix.lower() != ".csv":
            warnings.append(f"submission_output_path does not use .csv extension: {submission_path}")

        self._check_cache_integrity(repo_root, warnings)

        env_vars = list(required_env_vars or [])
        missing_env = [name for name in env_vars if not os.getenv(name)]
        if missing_env:
            errors.append(f"missing required environment variables: {', '.join(missing_env)}")

        if settings.retrieval.initial_k <= 0:
            errors.append("retrieval.initial_k must be > 0")
        if settings.ranking.confidence_threshold < 0 or settings.ranking.confidence_threshold > 1:
            errors.append("ranking.confidence_threshold must be in [0, 1]")

        return HealthCheckResult(ok=not errors, errors=errors, warnings=warnings)

    def ensure_healthy(self, settings: AppSettings, required_env_vars: Iterable[str] | None = None) -> None:
        result = self.run(settings, required_env_vars=required_env_vars)
        if result.ok:
            return
        joined = " | ".join(result.errors)
        raise RuntimeError(f"Repository health checks failed: {joined}")

    def _check_cache_integrity(self, repo_root: Path, warnings: List[str]) -> None:
        cache_dir = repo_root / "artifacts" / "cache"
        if not cache_dir.exists():
            return

        json_files = list(cache_dir.rglob("*.json"))
        for path in json_files[:100]:
            try:
                json.loads(path.read_text(encoding="utf-8"))
            except Exception as exc:  # pragma: no cover - defensive safeguard
                warnings.append(f"cache file is not valid JSON: {path} ({exc})")
