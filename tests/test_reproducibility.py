"""Reproducibility tests for deterministic ranking behavior."""

from __future__ import annotations

import unittest

from src.config.settings import parse_app_settings
from src.pipelines.ranking_pipeline import RankingPipeline


class TestReproducibility(unittest.TestCase):
    def test_ranking_pipeline_reproducible_top_ids(self) -> None:
        raw_config = {
            "paths": {
                "repository_root": "c:/Users/Faiz Abid/Desktop/India_Runs",
                "dataset_dir": "c:/Users/Faiz Abid/Desktop/India_Runs/India_runs_data_and_ai_challenge",
                "candidates_path": "c:/Users/Faiz Abid/Desktop/India_Runs/India_runs_data_and_ai_challenge/candidates.jsonl",
                "job_description_path": "c:/Users/Faiz Abid/Desktop/India_Runs/India_runs_data_and_ai_challenge/job_description.docx",
                "submission_output_path": "c:/Users/Faiz Abid/Desktop/India_Runs/outputs/submission.csv",
            },
            "runtime": {
                "top_n": 25,
                "strict_validation": False,
                "random_seed": 42,
                "max_candidates_to_process": 120,
            },
            "logging": {"level": "INFO"},
            "retrieval": {"strategy": "hybrid", "initial_k": 80},
            "ranking": {"strategy": "evidence_weighted", "confidence_threshold": 0.5},
        }

        settings = parse_app_settings(raw_config)
        first_ranked, _ = RankingPipeline(settings).execute()
        second_ranked, _ = RankingPipeline(settings).execute()

        first_ids = [row.candidate_id for row in first_ranked[:10]]
        second_ids = [row.candidate_id for row in second_ranked[:10]]

        self.assertEqual(first_ids, second_ids)
        self.assertEqual(len(first_ranked), len(second_ranked))


if __name__ == "__main__":
    unittest.main()
