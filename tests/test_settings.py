"""Unit tests for config parsing and runtime settings."""

from __future__ import annotations

import unittest

from src.config.settings import parse_app_settings, parse_runtime_settings


class TestRuntimeSettings(unittest.TestCase):
    def test_parse_runtime_settings_success(self) -> None:
        raw = {
            "paths": {
                "repository_root": "repo",
                "dataset_dir": "dataset",
                "candidates_path": "candidates.jsonl",
                "job_description_path": "job.docx",
                "submission_output_path": "submission.csv",
            },
            "runtime": {"top_n": 100},
        }

        settings = parse_runtime_settings(raw)

        self.assertEqual(settings.top_n, 100)
        self.assertEqual(settings.candidates_path, "candidates.jsonl")
        self.assertEqual(settings.random_seed, 42)
        self.assertTrue(settings.strict_validation)
        self.assertIsNone(settings.max_candidates_to_process)

    def test_parse_runtime_settings_missing_keys(self) -> None:
        raw = {
            "paths": {
                "repository_root": "repo",
                "dataset_dir": "dataset",
                "candidates_path": "candidates.jsonl",
            },
            "runtime": {"top_n": 100},
        }

        with self.assertRaises(ValueError):
            parse_runtime_settings(raw)

    def test_parse_app_settings_success(self) -> None:
        raw = {
            "paths": {
                "repository_root": "repo",
                "dataset_dir": "dataset",
                "candidates_path": "candidates.jsonl",
                "job_description_path": "job.docx",
                "submission_output_path": "submission.csv",
            },
            "runtime": {
                "top_n": 100,
                "random_seed": 7,
                "strict_validation": False,
                "max_candidates_to_process": 200,
            },
            "logging": {"level": "DEBUG"},
            "retrieval": {"strategy": "hybrid", "initial_k": 1234},
            "ranking": {"strategy": "rule_based", "confidence_threshold": 0.6},
            "dashboard": {
                "default_page_size": 50,
                "max_comparison_candidates": 3,
                "enable_engineering_view": True,
                "shortlist_output_path": "outputs/shortlist.csv",
            },
        }

        app = parse_app_settings(raw)

        self.assertEqual(app.runtime.random_seed, 7)
        self.assertFalse(app.runtime.strict_validation)
        self.assertEqual(app.runtime.max_candidates_to_process, 200)
        self.assertEqual(app.logging.level, "DEBUG")
        self.assertEqual(app.retrieval.initial_k, 1234)
        self.assertAlmostEqual(app.ranking.confidence_threshold, 0.6)
        self.assertEqual(app.dashboard.default_page_size, 50)
        self.assertEqual(app.dashboard.max_comparison_candidates, 3)
        self.assertTrue(app.dashboard.enable_engineering_view)

    def test_parse_runtime_settings_invalid_top_n(self) -> None:
        raw = {
            "paths": {
                "repository_root": "repo",
                "dataset_dir": "dataset",
                "candidates_path": "candidates.jsonl",
                "job_description_path": "job.docx",
                "submission_output_path": "submission.csv",
            },
            "runtime": {"top_n": 0},
        }

        with self.assertRaises(ValueError):
            parse_runtime_settings(raw)


if __name__ == "__main__":
    unittest.main()
