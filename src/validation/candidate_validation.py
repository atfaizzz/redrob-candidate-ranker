"""Validation for raw candidate records and canonical candidate objects."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from src.contracts.domain import Candidate


@dataclass(frozen=True)
class ValidationIssue:
    """A structured validation issue."""

    code: str
    message: str


class RawCandidateRecordValidator:
    """Validates raw candidate dictionaries before parsing."""

    REQUIRED_TOP_LEVEL = {
        "candidate_id",
        "profile",
        "career_history",
        "education",
        "skills",
        "redrob_signals",
    }

    def validate(self, record: Dict[str, object]) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []
        keys = set(record.keys())
        missing = sorted(self.REQUIRED_TOP_LEVEL - keys)
        if missing:
            issues.append(
                ValidationIssue(
                    code="missing_required_top_level",
                    message=f"Missing required fields: {missing}",
                )
            )

        cid = record.get("candidate_id")
        if not isinstance(cid, str) or not cid.startswith("CAND_"):
            issues.append(
                ValidationIssue(
                    code="invalid_candidate_id",
                    message="candidate_id must be string with CAND_ prefix",
                )
            )

        profile = record.get("profile")
        if not isinstance(profile, dict):
            issues.append(
                ValidationIssue(
                    code="invalid_profile",
                    message="profile must be an object",
                )
            )

        redrob_signals = record.get("redrob_signals")
        if not isinstance(redrob_signals, dict):
            issues.append(
                ValidationIssue(
                    code="invalid_redrob_signals",
                    message="redrob_signals must be an object",
                )
            )

        return issues


class CanonicalCandidateValidator:
    """Validates canonical candidate objects after parsing."""

    def validate(self, candidate: Candidate) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []

        if not candidate.career_history:
            issues.append(
                ValidationIssue(
                    code="empty_career_history",
                    message="Candidate must contain at least one career record",
                )
            )

        current_count = sum(1 for item in candidate.career_history if item.is_current)
        if current_count != 1:
            issues.append(
                ValidationIssue(
                    code="invalid_current_role_count",
                    message=f"Expected exactly one current role, got {current_count}",
                )
            )

        if candidate.redrob_signals is not None:
            salary = candidate.redrob_signals.expected_salary_range_inr_lpa
            if salary.min_lpa > salary.max_lpa:
                issues.append(
                    ValidationIssue(
                        code="invalid_salary_range",
                        message="salary min_lpa cannot be greater than max_lpa",
                    )
                )
            if candidate.redrob_signals.signup_date > candidate.redrob_signals.last_active_date:
                issues.append(
                    ValidationIssue(
                        code="invalid_activity_dates",
                        message="signup_date cannot be after last_active_date",
                    )
                )

        return issues


def summarize_issues(issues: List[ValidationIssue]) -> Dict[str, int]:
    """Aggregate issues by code for reporting."""

    summary: Dict[str, int] = {}
    for issue in issues:
        summary[issue.code] = summary.get(issue.code, 0) + 1
    return summary
