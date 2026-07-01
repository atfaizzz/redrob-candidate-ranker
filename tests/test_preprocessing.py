"""Tests for preprocessing normalization and feature extraction."""

from __future__ import annotations

import unittest

from src.contracts.domain import Candidate, CandidateProfile
from src.preprocessing.feature_extraction import CandidateFeatureExtractor
from src.preprocessing.normalization import normalize_candidate_record


class TestPreprocessing(unittest.TestCase):
    def test_normalize_candidate_record_salary_bounds(self) -> None:
        record = {
            "candidate_id": "CAND_0000001",
            "profile": {"headline": "  AI   Engineer  "},
            "career_history": [],
            "education": [],
            "skills": [],
            "redrob_signals": {
                "expected_salary_range_inr_lpa": {"min": 25.0, "max": 10.0}
            },
        }

        normalized = normalize_candidate_record(record)
        salary = normalized["redrob_signals"]["expected_salary_range_inr_lpa"]

        self.assertEqual(salary["min"], 10.0)
        self.assertEqual(salary["max"], 25.0)
        self.assertEqual(normalized["profile"]["headline"], "AI Engineer")

    def test_feature_extractor_basic(self) -> None:
        candidate = Candidate(
            candidate_id="CAND_0000001",
            profile=CandidateProfile(
                anonymized_name="Anon",
                headline="AI Engineer",
                summary="Summary",
                location="Noida",
                country="India",
                years_of_experience=6.5,
                current_title="Engineer",
                current_company="X",
                current_company_size="201-500",
                current_industry="IT",
            ),
            career_history=[],
            education=[],
            skills=[],
        )

        features = CandidateFeatureExtractor().extract(candidate)
        self.assertEqual(features.candidate_id, "CAND_0000001")
        self.assertIn("years_of_experience", features.features)


if __name__ == "__main__":
    unittest.main()
