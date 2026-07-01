"""Unit tests for evaluation metrics and explainability evaluation."""

from __future__ import annotations

import unittest
from datetime import date

from src.contracts.domain import (
    Candidate,
    CandidateProfile,
    CareerRecord,
    EvidenceBreakdown,
    RankedCandidate,
    Skill,
)
from src.evaluation.confidence import confidence_bucket_summary
from src.evaluation.explainability_eval import evaluate_explanations
from src.evaluation.metrics import (
    average_precision,
    mrr,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
)


def _candidate(cid: str, title: str, skill: str) -> Candidate:
    return Candidate(
        candidate_id=cid,
        profile=CandidateProfile(
            anonymized_name="Anon",
            headline=title,
            summary=f"Worked on {skill}",
            location="Noida",
            country="India",
            years_of_experience=6.0,
            current_title=title,
            current_company="Prod",
            current_company_size="201-500",
            current_industry="IT",
        ),
        career_history=[
            CareerRecord(
                company="Prod",
                title=title,
                start_date=date(2020, 1, 1),
                end_date=None,
                duration_months=48,
                is_current=True,
                industry="IT",
                company_size="201-500",
                description="Built matching system",
            )
        ],
        education=[],
        skills=[Skill(name=skill, proficiency="advanced", endorsements=10, duration_months=36)],
    )


class TestEvaluationMetrics(unittest.TestCase):
    def test_ranking_metrics(self) -> None:
        predicted = ["A", "B", "C", "D"]
        relevant = {"A", "C"}
        graded = {"A": 3, "B": 1, "C": 2, "D": 0}

        self.assertAlmostEqual(precision_at_k(predicted, relevant, 2), 0.5)
        self.assertAlmostEqual(recall_at_k(predicted, relevant, 2), 0.5)
        self.assertAlmostEqual(mrr(predicted, relevant), 1.0)
        self.assertGreater(ndcg_at_k(predicted, graded, 3), 0.0)
        self.assertGreater(average_precision(predicted, relevant, 4), 0.0)

    def test_confidence_and_explainability_eval(self) -> None:
        ranked = [
            RankedCandidate(
                candidate_id="A",
                rank=1,
                score=0.9,
                reasoning="Senior AI Engineer with retrieval expertise.",
                evidence=EvidenceBreakdown(0.8, 0.8, 0.7, 0.6, 0.7, 0.85),
            ),
            RankedCandidate(
                candidate_id="B",
                rank=2,
                score=0.7,
                reasoning="Backend profile with partial fit.",
                evidence=EvidenceBreakdown(0.5, 0.6, 0.5, 0.4, 0.5, 0.55),
            ),
        ]

        buckets = confidence_bucket_summary(ranked)
        self.assertEqual(sum(buckets.values()), 2)

        candidates_by_id = {
            "A": _candidate("A", "Senior AI Engineer", "retrieval"),
            "B": _candidate("B", "Backend Engineer", "python"),
        }
        explainability = evaluate_explanations(ranked, candidates_by_id)
        self.assertEqual(explainability["count"], 2)
        self.assertGreaterEqual(explainability["coverage"], 0.5)


if __name__ == "__main__":
    unittest.main()
