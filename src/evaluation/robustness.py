"""Robustness scenarios for ranking pipeline stress checks."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from typing import Dict, List, Sequence

from src.contracts.domain import Candidate


def perturb_missing_skills(candidates: Sequence[Candidate]) -> List[Candidate]:
    """Drop skills from every third candidate to simulate sparse profiles."""

    perturbed: List[Candidate] = []
    for idx, candidate in enumerate(candidates):
        if idx % 3 == 0:
            perturbed.append(replace(candidate, skills=[]))
        else:
            perturbed.append(candidate)
    return perturbed


def perturb_missing_education(candidates: Sequence[Candidate]) -> List[Candidate]:
    """Drop education from every fourth candidate."""

    perturbed: List[Candidate] = []
    for idx, candidate in enumerate(candidates):
        if idx % 4 == 0:
            perturbed.append(replace(candidate, education=[]))
        else:
            perturbed.append(candidate)
    return perturbed


def perturb_missing_behavioral_signals(candidates: Sequence[Candidate]) -> List[Candidate]:
    """Drop behavioral signals from every fifth candidate."""

    perturbed: List[Candidate] = []
    for idx, candidate in enumerate(candidates):
        if idx % 5 == 0:
            perturbed.append(replace(candidate, redrob_signals=None))
        else:
            perturbed.append(candidate)
    return perturbed


def perturb_duplicate_candidates(candidates: Sequence[Candidate]) -> List[Candidate]:
    """Inject duplicates to test ranking stability against repeated rows."""

    result = list(candidates)
    if candidates:
        result.extend(candidates[: min(5, len(candidates))])
    return result
