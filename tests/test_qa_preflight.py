"""Tests for repository preflight health checks."""

from __future__ import annotations

import unittest

from src.config.settings import parse_app_settings
from src.qa.preflight import RepositoryHealthChecker


class TestRepositoryHealthChecker(unittest.TestCase):
    def test_preflight_healthy_paths(self) -> None:
        raw_config = {
            "paths": {
                "repository_root": "c:/Users/Faiz Abid/Desktop/India_Runs",
                "dataset_dir": "c:/Users/Faiz Abid/Desktop/India_Runs/India_runs_data_and_ai_challenge",
                "candidates_path": "c:/Users/Faiz Abid/Desktop/India_Runs/India_runs_data_and_ai_challenge/candidates.jsonl",
                "job_description_path": "c:/Users/Faiz Abid/Desktop/India_Runs/India_runs_data_and_ai_challenge/job_description.docx",
                "submission_output_path": "c:/Users/Faiz Abid/Desktop/India_Runs/outputs/submission.csv",
            },
            "runtime": {
                "top_n": 20,
                "strict_validation": False,
                "random_seed": 42,
                "max_candidates_to_process": 100,
            },
            "logging": {"level": "INFO"},
            "retrieval": {"strategy": "hybrid", "initial_k": 50},
            "ranking": {"strategy": "evidence_weighted", "confidence_threshold": 0.5},
        }

        settings = parse_app_settings(raw_config)
        result = RepositoryHealthChecker().run(settings)
        self.assertTrue(result.ok)
        self.assertFalse(result.errors)

    def test_preflight_detects_missing_inputs(self) -> None:
        raw_config = {
            "paths": {
                "repository_root": "c:/Users/Faiz Abid/Desktop/India_Runs",
                "dataset_dir": "c:/Users/Faiz Abid/Desktop/India_Runs/India_runs_data_and_ai_challenge",
                "candidates_path": "c:/Users/Faiz Abid/Desktop/India_Runs/India_runs_data_and_ai_challenge/does_not_exist.jsonl",
                "job_description_path": "c:/Users/Faiz Abid/Desktop/India_Runs/India_runs_data_and_ai_challenge/missing.docx",
                "submission_output_path": "c:/Users/Faiz Abid/Desktop/India_Runs/outputs/submission.csv",
            },
            "runtime": {
                "top_n": 20,
                "strict_validation": False,
                "random_seed": 42,
                "max_candidates_to_process": 100,
            },
            "logging": {"level": "INFO"},
            "retrieval": {"strategy": "hybrid", "initial_k": 50},
            "ranking": {"strategy": "evidence_weighted", "confidence_threshold": 0.5},
        }

        settings = parse_app_settings(raw_config)
        result = RepositoryHealthChecker().run(settings)
        self.assertFalse(result.ok)
        self.assertTrue(any("candidates_path" in err for err in result.errors))
        self.assertTrue(any("job_description_path" in err for err in result.errors))


if __name__ == "__main__":
    unittest.main()
