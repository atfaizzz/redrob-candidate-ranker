"""Tests for lightweight QA performance and memory profiling."""

from __future__ import annotations

import unittest

from src.config.settings import parse_app_settings
from src.qa.performance import profile_ranking_pipeline


class TestQAPerformance(unittest.TestCase):
    def test_profile_ranking_pipeline(self) -> None:
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
                "max_candidates_to_process": 80,
            },
            "logging": {"level": "INFO"},
            "retrieval": {"strategy": "hybrid", "initial_k": 60},
            "ranking": {"strategy": "evidence_weighted", "confidence_threshold": 0.5},
        }

        settings = parse_app_settings(raw_config)
        profile = profile_ranking_pipeline(settings)

        self.assertGreater(profile.total_duration_ms, 0.0)
        self.assertGreaterEqual(profile.peak_memory_mb, 0.0)
        self.assertGreater(profile.scanned_candidates, 0)
        self.assertGreater(profile.ranked_candidates, 0)


if __name__ == "__main__":
    unittest.main()
