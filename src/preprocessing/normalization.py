"""Deterministic normalization utilities for candidate records."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict


def normalize_whitespace(value: str) -> str:
    """Normalize internal whitespace and strip outer spaces."""

    return " ".join(value.split())


def normalize_candidate_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize raw candidate dictionary into deterministic representation."""

    normalized = deepcopy(record)

    profile = normalized.get("profile")
    if isinstance(profile, dict):
        for key, value in list(profile.items()):
            if isinstance(value, str):
                profile[key] = normalize_whitespace(value)

    career = normalized.get("career_history")
    if isinstance(career, list):
        for item in career:
            if not isinstance(item, dict):
                continue
            for key, value in list(item.items()):
                if isinstance(value, str):
                    item[key] = normalize_whitespace(value)

    skills = normalized.get("skills")
    if isinstance(skills, list):
        for skill in skills:
            if not isinstance(skill, dict):
                continue
            if isinstance(skill.get("name"), str):
                skill["name"] = normalize_whitespace(skill["name"])

    signals = normalized.get("redrob_signals")
    if isinstance(signals, dict):
        salary = signals.get("expected_salary_range_inr_lpa")
        if isinstance(salary, dict):
            min_value = salary.get("min")
            max_value = salary.get("max")
            if isinstance(min_value, (int, float)) and isinstance(max_value, (int, float)):
                salary["min"] = float(min(min_value, max_value))
                salary["max"] = float(max(min_value, max_value))

    return normalized
