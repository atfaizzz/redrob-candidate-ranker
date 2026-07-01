"""Explanation quality checks for ranked outputs."""

from __future__ import annotations

from typing import Dict, Sequence

from src.contracts.domain import Candidate, RankedCandidate


def _contains_any(text: str, tokens: Sequence[str]) -> bool:
    lowered = text.lower()
    return any(token.lower() in lowered for token in tokens if token)


def evaluate_explanations(
    ranked: Sequence[RankedCandidate],
    candidates_by_id: Dict[str, Candidate],
) -> dict:
    """Evaluate explanation consistency and evidence alignment heuristically."""

    if not ranked:
        return {
            "count": 0,
            "coverage": 0.0,
            "evidence_alignment": 0.0,
            "readability": 0.0,
        }

    non_empty = 0
    aligned = 0
    readable = 0

    for row in ranked:
        reasoning = (row.reasoning or "").strip()
        if reasoning:
            non_empty += 1

        candidate = candidates_by_id.get(row.candidate_id)
        if candidate is not None:
            anchors = [candidate.profile.current_title]
            anchors.extend(skill.name for skill in candidate.skills[:5])
            if _contains_any(reasoning, anchors):
                aligned += 1

        word_count = len(reasoning.split())
        if 10 <= word_count <= 80:
            readable += 1

    total = len(ranked)
    return {
        "count": total,
        "coverage": non_empty / total,
        "evidence_alignment": aligned / total,
        "readability": readable / total,
    }
