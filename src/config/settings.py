"""Configuration loading and typed runtime settings.

Configuration is externalized and supports JSON and YAML files.
YAML loading requires PyYAML to be installed.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class RuntimeSettings:
    """Top-level runtime settings shared by all modules."""

    repository_root: str
    dataset_dir: str
    candidates_path: str
    submission_output_path: str
    job_description_path: str
    top_n: int
    random_seed: int
    strict_validation: bool
    max_candidates_to_process: Optional[int]


@dataclass(frozen=True)
class LoggingSettings:
    """Logging settings shared by pipeline stages."""

    level: str


@dataclass(frozen=True)
class RetrievalSettings:
    """Retrieval settings for later ranking phases."""

    strategy: str
    initial_k: int


@dataclass(frozen=True)
class RankingSettings:
    """Ranking settings for later ranking phases."""

    strategy: str
    confidence_threshold: float


@dataclass(frozen=True)
class DashboardSettings:
    """Dashboard behavior settings for recruiter and engineering views."""

    default_page_size: int
    max_comparison_candidates: int
    enable_engineering_view: bool
    shortlist_output_path: str


@dataclass(frozen=True)
class AppSettings:
    """All parsed application settings."""

    runtime: RuntimeSettings
    logging: LoggingSettings
    retrieval: RetrievalSettings
    ranking: RankingSettings
    dashboard: DashboardSettings


def _load_yaml(path: Path) -> Dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "PyYAML is required to load YAML configs. "
            "Install with: pip install pyyaml"
        ) from exc

    with path.open("r", encoding="utf-8") as fp:
        loaded = yaml.safe_load(fp)

    if not isinstance(loaded, dict):
        raise ValueError(f"Config must deserialize to a mapping: {path}")
    return loaded


def load_config(path: str | Path) -> Dict[str, Any]:
    """Load config file as a dictionary from JSON or YAML."""

    config_path = Path(path)
    suffix = config_path.suffix.lower()

    if suffix == ".json":
        with config_path.open("r", encoding="utf-8") as fp:
            loaded = json.load(fp)
        if not isinstance(loaded, dict):
            raise ValueError(f"Config must deserialize to a mapping: {config_path}")
        return loaded

    if suffix in {".yaml", ".yml"}:
        return _load_yaml(config_path)

    raise ValueError(f"Unsupported config format: {config_path}")


def _apply_environment_overrides(raw_config: Dict[str, Any]) -> Dict[str, Any]:
    """Apply optional environment variable overrides to known config keys."""

    paths = raw_config.setdefault("paths", {})
    runtime = raw_config.setdefault("runtime", {})

    env_map = {
        "AI_RECRUITER_REPOSITORY_ROOT": (paths, "repository_root"),
        "AI_RECRUITER_DATASET_DIR": (paths, "dataset_dir"),
        "AI_RECRUITER_CANDIDATES_PATH": (paths, "candidates_path"),
        "AI_RECRUITER_JOB_DESCRIPTION_PATH": (paths, "job_description_path"),
        "AI_RECRUITER_SUBMISSION_OUTPUT_PATH": (paths, "submission_output_path"),
        "AI_RECRUITER_TOP_N": (runtime, "top_n"),
        "AI_RECRUITER_MAX_CANDIDATES": (runtime, "max_candidates_to_process"),
        "AI_RECRUITER_STRICT_VALIDATION": (runtime, "strict_validation"),
    }

    for env_name, (target, key) in env_map.items():
        value = os.getenv(env_name)
        if value is None:
            continue
        if key in {"top_n", "max_candidates_to_process"}:
            target[key] = int(value)
        elif key == "strict_validation":
            target[key] = value.strip().lower() in {"1", "true", "yes"}
        else:
            target[key] = value

    return raw_config


def parse_runtime_settings(raw_config: Dict[str, Any]) -> RuntimeSettings:
    """Parse and validate runtime settings from raw config data."""

    paths = raw_config.get("paths")
    runtime = raw_config.get("runtime")
    if not isinstance(paths, dict) or not isinstance(runtime, dict):
        raise ValueError("Config must contain 'paths' and 'runtime' mappings")

    required_path_keys = [
        "repository_root",
        "dataset_dir",
        "candidates_path",
        "submission_output_path",
        "job_description_path",
    ]
    missing = [key for key in required_path_keys if key not in paths]
    if missing:
        raise ValueError(f"Missing path keys in config: {missing}")

    top_n = runtime.get("top_n")
    if not isinstance(top_n, int) or top_n <= 0:
        raise ValueError("runtime.top_n must be a positive integer")

    random_seed = runtime.get("random_seed", 42)
    if not isinstance(random_seed, int):
        raise ValueError("runtime.random_seed must be an integer")

    strict_validation = runtime.get("strict_validation", True)
    if not isinstance(strict_validation, bool):
        raise ValueError("runtime.strict_validation must be a boolean")

    max_candidates = runtime.get("max_candidates_to_process")
    if max_candidates is not None and (
        not isinstance(max_candidates, int) or max_candidates <= 0
    ):
        raise ValueError(
            "runtime.max_candidates_to_process must be a positive integer or null"
        )

    return RuntimeSettings(
        repository_root=str(paths["repository_root"]),
        dataset_dir=str(paths["dataset_dir"]),
        candidates_path=str(paths["candidates_path"]),
        submission_output_path=str(paths["submission_output_path"]),
        job_description_path=str(paths["job_description_path"]),
        top_n=top_n,
        random_seed=random_seed,
        strict_validation=strict_validation,
        max_candidates_to_process=max_candidates,
    )


def parse_app_settings(raw_config: Dict[str, Any]) -> AppSettings:
    """Parse all app settings with environment overrides."""

    resolved = _apply_environment_overrides(raw_config)
    runtime = parse_runtime_settings(resolved)

    logging_cfg = resolved.get("logging", {})
    retrieval_cfg = resolved.get("retrieval", {})
    ranking_cfg = resolved.get("ranking", {})
    dashboard_cfg = resolved.get("dashboard", {})

    logging = LoggingSettings(level=str(logging_cfg.get("level", "INFO")))
    retrieval = RetrievalSettings(
        strategy=str(retrieval_cfg.get("strategy", "hybrid")),
        initial_k=int(retrieval_cfg.get("initial_k", 1000)),
    )
    ranking = RankingSettings(
        strategy=str(ranking_cfg.get("strategy", "evidence_weighted")),
        confidence_threshold=float(ranking_cfg.get("confidence_threshold", 0.5)),
    )
    dashboard = DashboardSettings(
        default_page_size=int(dashboard_cfg.get("default_page_size", 25)),
        max_comparison_candidates=int(dashboard_cfg.get("max_comparison_candidates", 4)),
        enable_engineering_view=bool(dashboard_cfg.get("enable_engineering_view", True)),
        shortlist_output_path=str(
            dashboard_cfg.get(
                "shortlist_output_path",
                "c:/Users/Faiz Abid/Desktop/India_Runs/outputs/shortlist.csv",
            )
        ),
    )
    return AppSettings(
        runtime=runtime,
        logging=logging,
        retrieval=retrieval,
        ranking=ranking,
        dashboard=dashboard,
    )
