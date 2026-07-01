"""Unit tests for dashboard view-model helpers."""

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
from src.dashboard.view_models import (
    apply_candidate_filters,
    build_candidate_cards,
    build_explainability_panel,
    compare_candidates,
    semantic_search_candidates,
)


def _candidate(cid: str, title: str, location: str, years: float, skill: str) -> Candidate:
    return Candidate(
        candidate_id=cid,
        profile=CandidateProfile(
            anonymized_name=f"Name {cid}",
            headline=title,
            summary=f"Works on {skill}",
            location=location,
            country="India",
            years_of_experience=years,
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
                description="Built systems",
            )
        ],
        education=[],
        skills=[Skill(name=skill, proficiency="advanced", endorsements=10, duration_months=36)],
    )


class TestDashboardViewModels(unittest.TestCase):
    def test_search_filter_and_compare(self) -> None:
        c1 = _candidate("CAND_0000001", "Senior AI Engineer", "Noida", 7.0, "retrieval")
        c2 = _candidate("CAND_0000002", "Backend Engineer", "Pune", 5.0, "python")

        ranked = [
            RankedCandidate(
                candidate_id=c1.candidate_id,
                rank=1,
                score=0.92,
                reasoning="Reason 1",
                evidence=EvidenceBreakdown(0.8, 0.8, 0.7, 0.6, 0.7, 0.82),
            ),
            RankedCandidate(
                candidate_id=c2.candidate_id,
                rank=2,
                score=0.75,
                reasoning="Reason 2",
                evidence=EvidenceBreakdown(0.6, 0.6, 0.5, 0.4, 0.5, 0.58),
            ),
        ]
        by_id = {c1.candidate_id: c1, c2.candidate_id: c2}

        cards = build_candidate_cards(ranked, by_id)
        searched = semantic_search_candidates(cards, "retrieval ai")
        self.assertTrue(searched)

        filtered = apply_candidate_filters(cards, min_experience=6.0, location_contains="Noida", min_confidence=0.7)
        self.assertEqual(len(filtered), 1)

        panel = build_explainability_panel(ranked[0], c1)
        self.assertTrue(panel.overall_match)

        comparison = compare_candidates(c1, ranked[0], c2, ranked[1])
        self.assertIn("overall_score", comparison)


if __name__ == "__main__":
    unittest.main()
