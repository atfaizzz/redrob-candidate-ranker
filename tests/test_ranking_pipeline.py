"""Integration-style tests for README_03 ranking pipeline."""

from __future__ import annotations

import unittest

from src.config.settings import parse_app_settings
from src.pipelines.ranking_pipeline import RankingPipeline


class TestRankingPipeline(unittest.TestCase):
    def test_ranking_pipeline_small_run(self) -> None:
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
                "max_candidates_to_process": 120,
            },
            "logging": {"level": "INFO"},
            "retrieval": {"strategy": "hybrid", "initial_k": 60},
            "ranking": {"strategy": "evidence_weighted", "confidence_threshold": 0.5},
        }

        settings = parse_app_settings(raw_config)
        pipeline = RankingPipeline(settings)

        ranked, summary = pipeline.execute()

        self.assertEqual(summary.scanned_candidates, 120)
        self.assertGreater(summary.parsed_candidates, 0)
        self.assertGreater(summary.retrieved_candidates, 0)
        self.assertGreater(summary.ranked_candidates, 0)
        self.assertLessEqual(summary.ranked_candidates, 20)
        self.assertEqual(len(ranked), summary.ranked_candidates)


if __name__ == "__main__":
    unittest.main()
