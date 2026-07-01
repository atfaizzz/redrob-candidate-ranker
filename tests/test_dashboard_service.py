"""Integration-style tests for dashboard service operations."""

from __future__ import annotations

import unittest
from pathlib import Path

from src.config.settings import parse_app_settings
from src.dashboard.service import RecruiterDashboardService


class TestDashboardService(unittest.TestCase):
    def test_service_run_and_shortlist_export(self) -> None:
        raw_config = {
            "paths": {
                "repository_root": "c:/Users/Faiz Abid/Desktop/India_Runs",
                "dataset_dir": "c:/Users/Faiz Abid/Desktop/India_Runs/India_runs_data_and_ai_challenge",
                "candidates_path": "c:/Users/Faiz Abid/Desktop/India_Runs/India_runs_data_and_ai_challenge/candidates.jsonl",
                "job_description_path": "c:/Users/Faiz Abid/Desktop/India_Runs/India_runs_data_and_ai_challenge/job_description.docx",
                "submission_output_path": "c:/Users/Faiz Abid/Desktop/India_Runs/outputs/submission.csv",
            },
            "runtime": {
                "top_n": 15,
                "strict_validation": False,
                "random_seed": 42,
                "max_candidates_to_process": 100,
            },
            "logging": {"level": "INFO"},
            "retrieval": {"strategy": "hybrid", "initial_k": 60},
            "ranking": {"strategy": "evidence_weighted", "confidence_threshold": 0.5},
            "dashboard": {
                "default_page_size": 20,
                "max_comparison_candidates": 2,
                "enable_engineering_view": True,
                "shortlist_output_path": "c:/Users/Faiz Abid/Desktop/India_Runs/outputs/test_shortlist.csv",
            },
        }

        settings = parse_app_settings(raw_config)
        service = RecruiterDashboardService(settings)
        state = service.run_ranking()

        self.assertTrue(state.cards)
        self.assertTrue(state.ranked)
        self.assertIn("total_candidates", state.summary)

        selected = [row.candidate_id for row in state.ranked[:3]]
        output_path = service.export_shortlist(state.ranked, selected)

        self.assertTrue(output_path.exists())
        text = output_path.read_text(encoding="utf-8")
        self.assertIn("candidate_id,rank,score,confidence,reasoning", text)

        output_path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
