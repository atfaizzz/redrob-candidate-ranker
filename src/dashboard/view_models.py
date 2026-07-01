"""View model helpers for recruiter-facing dashboard interactions."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence

from src.contracts.domain import Candidate, RankedCandidate


TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9+#.-]+")


def _tokenize(text: str) -> set[str]:
    return {token.lower() for token in TOKEN_PATTERN.findall(text)}


def confidence_label(value: float) -> str:
    """Map numeric confidence into readable labels."""

    if value >= 0.75:
        return "High"
    if value >= 0.5:
        return "Medium"
    return "Low"


@dataclass(frozen=True)
class CandidateCard:
    """Candidate card data for top-ranked listing."""

    candidate_id: str
    rank: int
    score: float
    confidence: float
    confidence_label: str
    name: str
    title: str
    location: str
    years_of_experience: float
    summary: str


@dataclass(frozen=True)
class ExplainabilityPanel:
    """Structured explainability panel sections."""

    overall_match: str
    strongest_evidence: List[str]
    potential_gaps: List[str]
    career_analysis: str
    skill_analysis: str
    behavior_analysis: str
    confidence_analysis: str
    reasoning_summary: str


def build_candidate_cards(
    ranked: Sequence[RankedCandidate],
    candidates_by_id: Dict[str, Candidate],
) -> List[CandidateCard]:
    """Build card-like representations for ranked candidates."""

    cards: List[CandidateCard] = []
    for row in ranked:
        candidate = candidates_by_id[row.candidate_id]
        cards.append(
            CandidateCard(
                candidate_id=row.candidate_id,
                rank=row.rank,
                score=row.score,
                confidence=row.evidence.confidence,
                confidence_label=confidence_label(row.evidence.confidence),
                name=candidate.profile.anonymized_name,
                title=candidate.profile.current_title,
                location=candidate.profile.location,
                years_of_experience=candidate.profile.years_of_experience,
                summary=candidate.profile.summary,
            )
        )
    return cards


def semantic_search_candidates(
    cards: Sequence[CandidateCard],
    query: str,
) -> List[CandidateCard]:
    """Perform lightweight semantic-like search via token overlap scoring."""

    query_tokens = _tokenize(query)
    if not query_tokens:
        return list(cards)

    scored: List[tuple[float, CandidateCard]] = []
    for card in cards:
        candidate_tokens = _tokenize(" ".join([card.title, card.summary, card.location]))
        overlap = len(query_tokens & candidate_tokens)
        score = overlap / max(len(query_tokens), 1)
        if score > 0:
            scored.append((score, card))

    scored.sort(key=lambda item: (item[0], -item[1].rank), reverse=True)
    return [item[1] for item in scored]


def apply_candidate_filters(
    cards: Sequence[CandidateCard],
    min_experience: float | None = None,
    location_contains: str | None = None,
    min_confidence: float | None = None,
) -> List[CandidateCard]:
    """Apply recruiter filters without changing ranking semantics."""

    filtered: List[CandidateCard] = []
    for card in cards:
        if min_experience is not None and card.years_of_experience < min_experience:
            continue
        if location_contains and location_contains.lower() not in card.location.lower():
            continue
        if min_confidence is not None and card.confidence < min_confidence:
            continue
        filtered.append(card)
    return filtered


def build_explainability_panel(
    ranked: RankedCandidate,
    candidate: Candidate,
) -> ExplainabilityPanel:
    """Build structured explanation panel from ranking evidence."""

    evidence = ranked.evidence
    strongest: List[str] = []
    gaps: List[str] = []

    if evidence.semantic_alignment >= 0.4:
        strongest.append("Strong semantic match to role requirements")
    if evidence.experience_alignment >= 0.6:
        strongest.append("Experience level aligns with target seniority")
    if evidence.career_progression >= 0.6:
        strongest.append("Career progression indicates role maturity")
    if evidence.behavioral_availability >= 0.6:
        strongest.append("Behavioral availability supports recruiter outreach")
    if evidence.trust_signals >= 0.6:
        strongest.append("Profile trust/completeness is strong")

    if evidence.experience_alignment < 0.5:
        gaps.append("Experience alignment is below desired range")
    if evidence.behavioral_availability < 0.4:
        gaps.append("Behavioral responsiveness may slow hiring")
    if evidence.trust_signals < 0.4:
        gaps.append("Trust/completeness signals are limited")

    overall_match = (
        f"Score {ranked.score:.3f} with {confidence_label(evidence.confidence)} confidence."
    )
    career_analysis = (
        f"Current role: {candidate.profile.current_title}; "
        f"career records: {len(candidate.career_history)}"
    )
    skill_analysis = (
        f"Skills listed: {len(candidate.skills)}; "
        f"top skills: {', '.join(skill.name for skill in candidate.skills[:5])}"
    )
    behavior_analysis = (
        f"Behavioral availability={evidence.behavioral_availability:.2f}, "
        f"trust={evidence.trust_signals:.2f}"
    )
    confidence_analysis = (
        f"Confidence is {confidence_label(evidence.confidence)} ({evidence.confidence:.2f}) "
        "based on evidence completeness and consistency."
    )

    return ExplainabilityPanel(
        overall_match=overall_match,
        strongest_evidence=strongest or ["No dominant evidence; mixed moderate signals"],
        potential_gaps=gaps,
        career_analysis=career_analysis,
        skill_analysis=skill_analysis,
        behavior_analysis=behavior_analysis,
        confidence_analysis=confidence_analysis,
        reasoning_summary=ranked.reasoning,
    )


def compare_candidates(
    first: Candidate,
    first_ranked: RankedCandidate,
    second: Candidate,
    second_ranked: RankedCandidate,
) -> Dict[str, str]:
    """Return side-by-side comparison narrative for recruiters."""

    comparisons = {
        "experience": (
            f"{first.profile.current_title} ({first.profile.years_of_experience:.1f}y) vs "
            f"{second.profile.current_title} ({second.profile.years_of_experience:.1f}y)"
        ),
        "skills": f"{len(first.skills)} skills vs {len(second.skills)} skills",
        "career_progression": (
            f"{first_ranked.evidence.career_progression:.2f} vs "
            f"{second_ranked.evidence.career_progression:.2f}"
        ),
        "confidence": (
            f"{confidence_label(first_ranked.evidence.confidence)} "
            f"({first_ranked.evidence.confidence:.2f}) vs "
            f"{confidence_label(second_ranked.evidence.confidence)} "
            f"({second_ranked.evidence.confidence:.2f})"
        ),
        "overall_score": f"{first_ranked.score:.3f} vs {second_ranked.score:.3f}",
    }
    return comparisons
