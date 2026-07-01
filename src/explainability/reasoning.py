"""Evidence-grounded explanation generation for ranked candidates."""

from __future__ import annotations

from typing import Dict

from src.contracts.domain import Candidate, RankedCandidate


def _confidence_label(score: float) -> str:
    if score >= 0.75:
        return "high"
    if score >= 0.5:
        return "medium"
    return "low"


class ExplanationGenerator:
    """Generates concise evidence-grounded reasoning statements."""

    def generate(self, candidate: Candidate, ranked: RankedCandidate) -> str:
        evidence = ranked.evidence

        top_signals = sorted(
            [
                ("semantic alignment", evidence.semantic_alignment),
                ("experience alignment", evidence.experience_alignment),
                ("career progression", evidence.career_progression),
                ("behavioral availability", evidence.behavioral_availability),
                ("trust signals", evidence.trust_signals),
            ],
            key=lambda pair: pair[1],
            reverse=True,
        )

        strongest = ", ".join(name for name, _ in top_signals[:2])
        confidence = _confidence_label(evidence.confidence)
        years = candidate.profile.years_of_experience
        current_title = candidate.profile.current_title
        skills_count = len(candidate.skills)

        return (
            f"{current_title} with {years:.1f} years experience shows strongest evidence in "
            f"{strongest}; profile includes {skills_count} listed skills and confidence is {confidence}."
        )

    def attach_reasoning(
        self,
        ranked_by_id: Dict[str, Candidate],
        ranked_candidates: list[RankedCandidate],
    ) -> list[RankedCandidate]:
        enriched: list[RankedCandidate] = []
        for row in ranked_candidates:
            candidate = ranked_by_id[row.candidate_id]
            reasoning = self.generate(candidate, row)
            enriched.append(
                RankedCandidate(
                    candidate_id=row.candidate_id,
                    rank=row.rank,
                    score=row.score,
                    reasoning=reasoning,
                    evidence=row.evidence,
                )
            )
        return enriched
