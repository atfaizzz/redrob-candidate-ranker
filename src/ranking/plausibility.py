"""Profile plausibility checks used to penalize impossible candidate claims."""

from __future__ import annotations

from datetime import date
from typing import Dict, Iterable, List, Sequence

from src.contracts.domain import Candidate, CareerRecord, Skill

COMPETITION_REFERENCE_YEAR = 2025

# Year each technology became practically available in industry workflows.
TECH_FIRST_AVAILABLE_YEAR: Dict[str, int] = {
    "langchain": 2022,
    "llamaindex": 2023,
    "pinecone": 2021,
    "weaviate": 2019,
    "chroma": 2022,
    "mistral": 2023,
    "gemini": 2023,
    "chatgpt": 2022,
    "stable diffusion": 2022,
    "sentence-transformers": 2019,
}

# A small curated company founding-year map. We only validate companies we can verify.
COMPANY_FOUNDING_YEAR: Dict[str, int] = {
    "openai": 2015,
    "anthropic": 2021,
    "databricks": 2013,
    "snowflake": 2012,
    "google": 1998,
    "microsoft": 1975,
    "amazon": 1994,
    "meta": 2004,
    "facebook": 2004,
    "mindtree": 1999,
}


def plausibility_penalty(candidate: Candidate, reference_year: int | None = None) -> float:
    """Return 0.0 for clearly impossible profiles, otherwise 1.0.

    The filter is intentionally strict and only penalizes hard contradictions.
    """

    issues = find_plausibility_issues(candidate, reference_year=reference_year)
    return 0.0 if issues else 1.0


def find_plausibility_issues(candidate: Candidate, reference_year: int | None = None) -> List[str]:
    """Collect deterministic plausibility issues for unit tests and audits."""

    year = reference_year or COMPETITION_REFERENCE_YEAR
    issues: List[str] = []

    issues.extend(_technology_duration_issues(candidate.skills, year))
    issues.extend(_company_founding_issues(candidate.career_history, year))
    issues.extend(_career_chronology_issues(candidate.career_history, year))
    issues.extend(_experience_chronology_issues(candidate, year))

    return issues


def _technology_duration_issues(skills: Sequence[Skill], reference_year: int) -> List[str]:
    issues: List[str] = []
    for skill in skills:
        if skill.duration_months is None:
            continue
        duration_years = skill.duration_months / 12.0
        skill_name = skill.name.lower()
        for tech, start_year in TECH_FIRST_AVAILABLE_YEAR.items():
            if tech in skill_name:
                max_possible = max(0.0, float(reference_year - start_year))
                if duration_years > max_possible + 0.5:
                    issues.append(
                        f"tech_duration:{skill.name}:{duration_years:.2f}>{max_possible:.2f}"
                    )
                break
    return issues


def _company_founding_issues(career_history: Sequence[CareerRecord], reference_year: int) -> List[str]:
    issues: List[str] = []
    _ = reference_year
    for role in career_history:
        company_name = role.company.strip().lower()
        if not company_name:
            continue
        if company_name in COMPANY_FOUNDING_YEAR:
            founding_year = COMPANY_FOUNDING_YEAR[company_name]
            if role.start_date.year < founding_year:
                issues.append(
                    f"company_founding:{role.company}:{role.start_date.year}<{founding_year}"
                )
    return issues


def _career_chronology_issues(career_history: Sequence[CareerRecord], reference_year: int) -> List[str]:
    issues: List[str] = []
    current_roles = 0

    for role in career_history:
        if role.is_current:
            current_roles += 1

        if role.end_date is not None and role.end_date < role.start_date:
            issues.append(f"career_order:{role.company}:{role.end_date}<{role.start_date}")

        if role.duration_months < 0:
            issues.append(f"career_duration_negative:{role.company}:{role.duration_months}")

        # Compare declared duration vs elapsed timeline with a one-year tolerance.
        timeline_end = role.end_date if role.end_date is not None else date(reference_year, 12, 31)
        elapsed_months = max(
            0,
            (timeline_end.year - role.start_date.year) * 12 + (timeline_end.month - role.start_date.month),
        )
        if role.duration_months > elapsed_months + 12:
            issues.append(
                f"career_duration_mismatch:{role.company}:{role.duration_months}>{elapsed_months + 12}"
            )

    if current_roles > 1:
        issues.append(f"multiple_current_roles:{current_roles}")

    return issues


def _experience_chronology_issues(candidate: Candidate, reference_year: int) -> List[str]:
    issues: List[str] = []
    yoe = candidate.profile.years_of_experience

    if yoe < 0:
        issues.append(f"negative_yoe:{yoe}")
        return issues

    if candidate.career_history:
        earliest_start_year = min(role.start_date.year for role in candidate.career_history)
        max_possible = max(0.0, float(reference_year - earliest_start_year + 1))
        if yoe > max_possible + 1.0:
            issues.append(f"yoe_vs_career:{yoe:.2f}>{max_possible + 1.0:.2f}")

    if candidate.education:
        earliest_grad_year = min(item.end_year for item in candidate.education if item.end_year > 0)
        if earliest_grad_year:
            max_possible_since_grad = max(0.0, float(reference_year - earliest_grad_year + 1))
            # Allow broader buffer for mid-career education; only flag obvious impossibility.
            if yoe > max_possible_since_grad + 5.0:
                issues.append(f"yoe_vs_education:{yoe:.2f}>{max_possible_since_grad + 5.0:.2f}")

    return issues
