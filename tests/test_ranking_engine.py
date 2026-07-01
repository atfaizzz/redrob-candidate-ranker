"""Tests for retrieval, ranking, and explainability components."""

from __future__ import annotations

import unittest
from datetime import date

from src.contracts.domain import (
    Candidate,
    CandidateProfile,
    CareerRecord,
    EducationRecord,
    JobDescription,
    RedrobSignals,
    SalaryRangeINRLPA,
    Skill,
)
from src.ranking.evidence_ranker import EvidenceBasedRanker
from src.retrieval.strategies import CandidateRetriever


def _build_candidate(
    candidate_id: str,
    title: str,
    skills: list[str],
    years: float,
    *,
    skill_duration_months: int = 36,
) -> Candidate:
    profile = CandidateProfile(
        anonymized_name="Anon",
        headline=title,
        summary="Built retrieval and ranking systems for hiring.",
        location="Noida, India",
        country="India",
        years_of_experience=years,
        current_title=title,
        current_company="ProductCo",
        current_company_size="201-500",
        current_industry="HR Tech",
    )
    career = [
        CareerRecord(
            company="ProductCo",
            title=title,
            start_date=date(2020, 1, 1),
            end_date=None,
            duration_months=54,
            is_current=True,
            industry="HR Tech",
            company_size="201-500",
            description="Owned retrieval and ranking for recruiter workflows.",
        )
    ]
    redrob = RedrobSignals(
        profile_completeness_score=90.0,
        signup_date=date(2024, 1, 1),
        last_active_date=date(2024, 6, 1),
        open_to_work_flag=True,
        profile_views_received_30d=10,
        applications_submitted_30d=2,
        recruiter_response_rate=0.7,
        avg_response_time_hours=12.0,
        skill_assessment_scores={name: 80.0 for name in skills[:2]},
        connection_count=200,
        endorsements_received=50,
        notice_period_days=30,
        expected_salary_range_inr_lpa=SalaryRangeINRLPA(min_lpa=20.0, max_lpa=30.0),
        preferred_work_mode="hybrid",
        willing_to_relocate=True,
        github_activity_score=60.0,
        search_appearance_30d=20,
        saved_by_recruiters_30d=5,
        interview_completion_rate=0.8,
        offer_acceptance_rate=0.7,
        verified_email=True,
        verified_phone=True,
        linkedin_connected=True,
    )
    return Candidate(
        candidate_id=candidate_id,
        profile=profile,
        career_history=career,
        education=[
            EducationRecord(
                institution="IIT",
                degree="B.Tech",
                field_of_study="Computer Science",
                start_year=2014,
                end_year=2018,
            )
        ],
        skills=[
            Skill(name=name, proficiency="advanced", endorsements=10, duration_months=skill_duration_months)
            for name in skills
        ],
        redrob_signals=redrob,
    )


class TestRankingEngine(unittest.TestCase):
    def setUp(self) -> None:
        self.job = JobDescription(
            role_title="Senior AI Engineer",
            raw_text="Need retrieval, ranking, embeddings, and recruiter-facing explainability.",
            location_constraints=["Noida", "Pune"],
            must_have_requirements=["retrieval", "ranking", "embeddings", "evaluation"],
            preferred_requirements=["product", "ab testing", "ml systems"],
            seniority_range_years=(5.0, 9.0),
        )
        self.candidates = [
            _build_candidate("CAND_0000001", "Senior AI Engineer", ["retrieval", "ranking", "python"], 7.0),
            _build_candidate("CAND_0000002", "Backend Engineer", ["sql", "airflow", "spark"], 6.0),
            _build_candidate("CAND_0000003", "ML Engineer", ["embeddings", "evaluation", "llm"], 5.5),
        ]

    def test_retrieval_and_ranking(self) -> None:
        retriever = CandidateRetriever()
        hybrid = retriever.retrieve_hybrid(self.job, self.candidates, k=3)
        self.assertEqual(len(hybrid), 3)
        self.assertGreaterEqual(hybrid[0].hybrid_score, hybrid[-1].hybrid_score)

        ranker = EvidenceBasedRanker()
        ranked = ranker.rank(self.job, hybrid, top_n=3)
        self.assertEqual(len(ranked), 3)
        self.assertEqual(ranked[0].rank, 1)
        self.assertGreaterEqual(ranked[0].score, ranked[-1].score)
        self.assertGreaterEqual(ranked[0].evidence.confidence, 0.0)
        self.assertLessEqual(ranked[0].evidence.confidence, 1.0)

    def test_retrieval_comparison(self) -> None:
        retriever = CandidateRetriever()
        comparison = retriever.compare_retrieval_strategies(self.job, self.candidates, k=3)
        self.assertIn("lexical_vs_semantic_overlap", comparison)
        self.assertIn("hybrid_avg_score", comparison)

    def test_impossible_profile_penalized_to_zero_score(self) -> None:
        impossible = _build_candidate(
            "CAND_0099999",
            "Senior AI Engineer",
            ["langchain", "retrieval", "ranking"],
            7.0,
            skill_duration_months=84,
        )

        retriever = CandidateRetriever()
        hybrid = retriever.retrieve_hybrid(self.job, [impossible], k=1)
        ranked = EvidenceBasedRanker().rank(self.job, hybrid, top_n=1)

        self.assertEqual(len(ranked), 0)


if __name__ == "__main__":
    unittest.main()
