"""Integration-style tests for README_04 evaluation pipeline."""

from __future__ import annotations

import unittest

from src.config.settings import parse_app_settings
from src.pipelines.evaluation_pipeline import EvaluationPipeline


class TestEvaluationPipeline(unittest.TestCase):
    def test_evaluation_pipeline_small_run(self) -> None:
        raw_config = {
            "paths": {
                "repository_root": "c:/Users/Faiz Abid/Desktop/India_Runs",
                "dataset_dir": "c:/Users/Faiz Abid/Desktop/India_Runs/India_runs_data_and_ai_challenge",
                "candidates_path": "c:/Users/Faiz Abid/Desktop/India_Runs/India_runs_data_and_ai_challenge/candidates.jsonl",
                "job_description_path": "c:/Users/Faiz Abid/Desktop/India_Runs/India_runs_data_and_ai_challenge/job_description.docx",
                "submission_output_path": "c:/Users/Faiz Abid/Desktop/India_Runs/outputs/submission.csv",
            },
            "runtime": {
                "top_n": 30,
                "strict_validation": False,
                "random_seed": 42,
                "max_candidates_to_process": 150,
            },
            "logging": {"level": "INFO"},
            "retrieval": {"strategy": "hybrid", "initial_k": 80},
            "ranking": {"strategy": "evidence_weighted", "confidence_threshold": 0.5},
        }

        settings = parse_app_settings(raw_config)
        summary = EvaluationPipeline(settings).execute()

        self.assertEqual(summary.scanned_candidates, 150)
        self.assertGreater(summary.parsed_candidates, 0)
        self.assertIn("precision_at_20", summary.retrieval_metrics)
        self.assertIn("ndcg_at_10", summary.ranking_metrics)
        self.assertIn("coverage", summary.explainability_metrics)
        self.assertTrue(summary.ablation_topk_overlap)
        self.assertTrue(summary.robustness_topk_overlap)


if __name__ == "__main__":
    unittest.main()
