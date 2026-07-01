"""Integration-style tests for backend orchestration pipeline."""

from __future__ import annotations

import unittest

from src.config.settings import parse_app_settings
from src.pipelines.backend_pipeline import BackendPipeline


class TestBackendPipeline(unittest.TestCase):
    def test_backend_pipeline_runs_with_small_limit(self) -> None:
        raw_config = {
            "paths": {
                "repository_root": "c:/Users/Faiz Abid/Desktop/India_Runs",
                "dataset_dir": "c:/Users/Faiz Abid/Desktop/India_Runs/India_runs_data_and_ai_challenge",
                "candidates_path": "c:/Users/Faiz Abid/Desktop/India_Runs/India_runs_data_and_ai_challenge/candidates.jsonl",
                "job_description_path": "c:/Users/Faiz Abid/Desktop/India_Runs/India_runs_data_and_ai_challenge/job_description.docx",
                "submission_output_path": "c:/Users/Faiz Abid/Desktop/India_Runs/outputs/submission.csv",
            },
            "runtime": {
                "top_n": 100,
                "strict_validation": True,
                "random_seed": 42,
                "max_candidates_to_process": 50,
            },
            "logging": {"level": "INFO"},
            "retrieval": {"strategy": "hybrid", "initial_k": 2000},
            "ranking": {"strategy": "evidence_weighted", "confidence_threshold": 0.5},
        }

        settings = parse_app_settings(raw_config)
        pipeline = BackendPipeline(settings)
        summary = pipeline.execute()

        self.assertGreater(summary.inventory_dataset_files, 0)
        self.assertGreater(summary.schema_records_scanned, 0)
        self.assertEqual(summary.scanned_candidates, 50)
        self.assertGreaterEqual(summary.parsed_candidates, 0)


if __name__ == "__main__":
    unittest.main()
