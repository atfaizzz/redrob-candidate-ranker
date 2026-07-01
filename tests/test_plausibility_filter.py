"""Tests for profile plausibility penalty used by ranking."""

from __future__ import annotations

import unittest
from datetime import date

from src.contracts.domain import (
    Candidate,
    CandidateProfile,
    CareerRecord,
    EducationRecord,
    EvidenceBreakdown,
    RedrobSignals,
    SalaryRangeINRLPA,
    Skill,
)
from src.ranking.evidence_ranker import EvidenceBasedRanker
from src.ranking.plausibility import find_plausibility_issues, plausibility_penalty


def _candidate(
    candidate_id: str,
    *,
    skill_name: str = "python",
    skill_duration_months: int = 36,
    career_company: str = "ProductCo",
    career_start: date = date(2021, 1, 1),
    yoe: float = 6.0,
) -> Candidate:
    return Candidate(
        candidate_id=candidate_id,
        profile=CandidateProfile(
            anonymized_name="Anon",
            headline="ML Engineer",
            summary="Builds ranking systems",
            location="Noida",
            country="India",
            years_of_experience=yoe,
            current_title="ML Engineer",
            current_company=career_company,
            current_company_size="201-500",
            current_industry="IT",
        ),
        career_history=[
            CareerRecord(
                company=career_company,
                title="ML Engineer",
                start_date=career_start,
                end_date=None,
                duration_months=36,
                is_current=True,
                industry="IT",
                company_size="201-500",
                description="Ranker work",
            )
        ],
        education=[
            EducationRecord(
                institution="IIT",
                degree="B.Tech",
                field_of_study="CSE",
                start_year=2014,
                end_year=2018,
            )
        ],
        skills=[Skill(name=skill_name, proficiency="advanced", endorsements=10, duration_months=skill_duration_months)],
        redrob_signals=RedrobSignals(
            profile_completeness_score=80.0,
            signup_date=date(2024, 1, 1),
            last_active_date=date(2024, 2, 1),
            open_to_work_flag=True,
            profile_views_received_30d=10,
            applications_submitted_30d=4,
            recruiter_response_rate=0.7,
            avg_response_time_hours=10.0,
            skill_assessment_scores={"python": 80.0},
            connection_count=100,
            endorsements_received=20,
            notice_period_days=30,
            expected_salary_range_inr_lpa=SalaryRangeINRLPA(min_lpa=10.0, max_lpa=20.0),
            preferred_work_mode="hybrid",
            willing_to_relocate=True,
            github_activity_score=50.0,
            search_appearance_30d=10,
            saved_by_recruiters_30d=2,
            interview_completion_rate=0.7,
            offer_acceptance_rate=0.6,
            verified_email=True,
            verified_phone=True,
            linkedin_connected=True,
        ),
    )


class TestPlausibilityFilter(unittest.TestCase):
    def test_impossible_technology_duration_penalty_zero(self) -> None:
        # LangChain available from 2022; 7 years is impossible in 2025.
        candidate = _candidate("CAND_0000999", skill_name="LangChain", skill_duration_months=84)
        penalty = plausibility_penalty(candidate, reference_year=2025)
        issues = find_plausibility_issues(candidate, reference_year=2025)
        self.assertEqual(penalty, 0.0)
        self.assertTrue(any(issue.startswith("tech_duration:") for issue in issues))

    def test_normal_candidate_penalty_one(self) -> None:
        candidate = _candidate("CAND_0001000", skill_name="Python", skill_duration_months=48)
        penalty = plausibility_penalty(candidate, reference_year=2025)
        self.assertEqual(penalty, 1.0)

    def test_company_before_founding_penalty_zero(self) -> None:
        # OpenAI founded 2015.
        candidate = _candidate(
            "CAND_0001001",
            career_company="OpenAI",
            career_start=date(2010, 1, 1),
            yoe=9.0,
        )
        penalty = plausibility_penalty(candidate, reference_year=2025)
        self.assertEqual(penalty, 0.0)

    def test_final_score_applies_penalty(self) -> None:
        ranker = EvidenceBasedRanker()
        evidence = EvidenceBreakdown(
            semantic_alignment=1.0,
            experience_alignment=1.0,
            career_progression=1.0,
            behavioral_availability=1.0,
            trust_signals=1.0,
            confidence=1.0,
        )
        impossible = _candidate("CAND_0001002", skill_name="LlamaIndex", skill_duration_months=60)
        normal = _candidate("CAND_0001003", skill_name="Python", skill_duration_months=60)

        self.assertEqual(ranker._final_score(evidence, impossible), 0.0)
        self.assertGreater(ranker._final_score(evidence, normal), 0.0)


if __name__ == "__main__":
    unittest.main()
