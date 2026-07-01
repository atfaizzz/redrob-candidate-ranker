"""Utilities for generating recruiter-facing explanation payloads."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from src.contracts.domain import Candidate, RankedCandidate


@dataclass(frozen=True)
class CandidateExplanation:
    """Structured explainability artifact for one ranked candidate."""

    candidate_id: str
    summary: str
    strongest_evidence: List[str]
    potential_gaps: List[str]
    confidence_label: str


class ExplanationBuilder:
    """Builds grounded explanations from ranked outputs and source candidate data."""

    def build(self, ranked: RankedCandidate, candidate: Candidate) -> CandidateExplanation:
        evidence = ranked.evidence
        strong: List[str] = []
        gaps: List[str] = []

        if evidence.semantic_alignment >= 0.3:
            strong.append("Semantic alignment with role requirements")
        if evidence.experience_alignment >= 0.7:
            strong.append("Experience aligns with target seniority")
        if evidence.career_progression >= 0.6:
            strong.append("Career trajectory shows relevant progression")
        if evidence.behavioral_availability >= 0.6:
            strong.append("Behavioral availability suggests interview readiness")
        if evidence.trust_signals >= 0.6:
            strong.append("Trust signals and profile quality are strong")

        if evidence.behavioral_availability < 0.4:
            gaps.append("Behavioral responsiveness or availability is weak")
        if evidence.trust_signals < 0.4:
            gaps.append("Trust/completeness evidence is limited")
        if evidence.experience_alignment < 0.5:
            gaps.append("Experience fit for target role is uncertain")

        confidence = self._confidence_label(evidence.confidence)
        if not strong:
            strong.append("No dominant signal; ranking reflects blended moderate evidence")

        summary = (
            f"Rank {ranked.rank} for {candidate.profile.current_title}; "
            f"score {ranked.score:.3f} with {confidence} confidence."
        )

        return CandidateExplanation(
            candidate_id=ranked.candidate_id,
            summary=summary,
            strongest_evidence=strong,
            potential_gaps=gaps,
            confidence_label=confidence,
        )

    def _confidence_label(self, confidence: float) -> str:
        if confidence >= 0.75:
            return "High"
        if confidence >= 0.5:
            return "Medium"
        return "Low"
