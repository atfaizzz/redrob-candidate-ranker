"""End-to-end tests for competition-compliant submission generation."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

# Allow the validate_submission module to be imported from the dataset folder
_DATASET_DIR = Path("c:/Users/Faiz Abid/Desktop/India_Runs/India_runs_data_and_ai_challenge")
if str(_DATASET_DIR) not in sys.path:
    sys.path.insert(0, str(_DATASET_DIR))

from validate_submission import validate_submission  # type: ignore

from src.config.settings import parse_app_settings
from src.pipelines.ranking_pipeline import RankingPipeline
from src.submission.writer import SubmissionWriter


class TestSubmissionWriter(unittest.TestCase):
    def test_submission_passes_official_validator(self) -> None:
        # Use a bounded corpus (5 000 candidates) so the test remains fast while
        # still exercising the full ranking → write → validate path.
        raw_config = {
            "paths": {
                "repository_root": "c:/Users/Faiz Abid/Desktop/India_Runs",
                "dataset_dir": "c:/Users/Faiz Abid/Desktop/India_Runs/India_runs_data_and_ai_challenge",
                "candidates_path": "c:/Users/Faiz Abid/Desktop/India_Runs/India_runs_data_and_ai_challenge/candidates.jsonl",
                "job_description_path": "c:/Users/Faiz Abid/Desktop/India_Runs/India_runs_data_and_ai_challenge/job_description.docx",
                "submission_output_path": "c:/Users/Faiz Abid/Desktop/India_Runs/outputs/test_submission.csv",
            },
            "runtime": {
                "top_n": 100,
                "strict_validation": False,
                "random_seed": 42,
                "max_candidates_to_process": 5000,
            },
            "logging": {"level": "INFO"},
            "retrieval": {"strategy": "hybrid", "initial_k": 2000},
            "ranking": {"strategy": "evidence_weighted", "confidence_threshold": 0.5},
        }

        settings = parse_app_settings(raw_config)
        ranked, summary = RankingPipeline(settings).execute()

        self.assertGreaterEqual(len(ranked), 100, "Pipeline must produce at least 100 ranked candidates")

        output_path = Path(settings.runtime.submission_output_path)
        SubmissionWriter().write(ranked, output_path)

        self.assertTrue(output_path.exists())

        errors = validate_submission(str(output_path))
        self.assertEqual(
            errors,
            [],
            f"Official validator found {len(errors)} issue(s):\n" + "\n".join(f"  - {e}" for e in errors),
        )

    def test_writer_rejects_too_few_candidates(self) -> None:
        from datetime import date

        from src.contracts.domain import (
            CandidateProfile,
            EvidenceBreakdown,
            RankedCandidate,
        )

        short_list = [
            RankedCandidate(
                candidate_id=f"CAND_{i:07d}",
                rank=i + 1,
                score=1.0 - i * 0.01,
                reasoning="test",
                evidence=EvidenceBreakdown(0.5, 0.5, 0.5, 0.5, 0.5, 0.5),
            )
            for i in range(50)
        ]

        with self.assertRaises(ValueError):
            SubmissionWriter().write(short_list, Path("c:/Users/Faiz Abid/Desktop/India_Runs/outputs/should_not_exist.csv"))


if __name__ == "__main__":
    unittest.main()
