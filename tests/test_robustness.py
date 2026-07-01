"""Tests for robustness perturbation scenario builders."""

from __future__ import annotations

import unittest
from datetime import date

from src.contracts.domain import Candidate, CandidateProfile, CareerRecord, Skill
from src.evaluation.robustness import (
    perturb_duplicate_candidates,
    perturb_missing_behavioral_signals,
    perturb_missing_education,
    perturb_missing_skills,
)


def _candidate(candidate_id: str) -> Candidate:
    return Candidate(
        candidate_id=candidate_id,
        profile=CandidateProfile(
            anonymized_name=candidate_id,
            headline="ML Engineer",
            summary="Works on retrieval ranking",
            location="Noida",
            country="India",
            years_of_experience=6.0,
            current_title="ML Engineer",
            current_company="ProductCo",
            current_company_size="201-500",
            current_industry="IT",
        ),
        career_history=[
            CareerRecord(
                company="ProductCo",
                title="ML Engineer",
                start_date=date(2021, 1, 1),
                end_date=None,
                duration_months=42,
                is_current=True,
                industry="IT",
                company_size="201-500",
                description="Builds systems",
            )
        ],
        education=[],
        skills=[Skill(name="python", proficiency="advanced", endorsements=5, duration_months=30)],
    )


class TestRobustnessPerturbations(unittest.TestCase):
    def test_missing_skills_perturbation(self) -> None:
        candidates = [_candidate(f"CAND_{i:07d}") for i in range(6)]
        perturbed = perturb_missing_skills(candidates)
        self.assertEqual(len(perturbed[0].skills), 0)
        self.assertGreater(len(perturbed[1].skills), 0)

    def test_missing_education_and_behavioral(self) -> None:
        candidates = [_candidate(f"CAND_{i:07d}") for i in range(6)]
        without_education = perturb_missing_education(candidates)
        without_behavior = perturb_missing_behavioral_signals(candidates)
        self.assertEqual(without_education[0].education, [])
        self.assertIsNone(without_behavior[0].redrob_signals)

    def test_duplicate_candidates(self) -> None:
        candidates = [_candidate(f"CAND_{i:07d}") for i in range(4)]
        duplicated = perturb_duplicate_candidates(candidates)
        self.assertGreaterEqual(len(duplicated), len(candidates))


if __name__ == "__main__":
    unittest.main()
