"""Parser from normalized dictionaries to canonical candidate objects."""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional

from src.contracts.domain import (
    Candidate,
    CandidateProfile,
    CareerRecord,
    Certification,
    EducationRecord,
    LanguageProficiency,
    RedrobSignals,
    SalaryRangeINRLPA,
    Skill,
)


def _parse_date(value: str | None) -> Optional[date]:
    if value is None:
        return None
    parts = value.split("-")
    if len(parts) != 3:
        raise ValueError(f"Invalid date format: {value}")
    year, month, day = (int(part) for part in parts)
    return date(year, month, day)


class CandidateParser:
    """Parses candidate dictionaries into canonical Candidate objects."""

    def parse(self, record: Dict[str, Any]) -> Candidate:
        profile = self._parse_profile(record["profile"])
        career_history = [self._parse_career_item(item) for item in record.get("career_history", [])]
        education = [self._parse_education_item(item) for item in record.get("education", [])]
        skills = [self._parse_skill_item(item) for item in record.get("skills", [])]
        certifications = [self._parse_certification(item) for item in record.get("certifications", [])]
        languages = [self._parse_language(item) for item in record.get("languages", [])]
        signals = self._parse_redrob_signals(record.get("redrob_signals"))

        return Candidate(
            candidate_id=str(record["candidate_id"]),
            profile=profile,
            career_history=career_history,
            education=education,
            skills=skills,
            certifications=certifications,
            languages=languages,
            redrob_signals=signals,
        )

    def _parse_profile(self, raw: Dict[str, Any]) -> CandidateProfile:
        return CandidateProfile(
            anonymized_name=str(raw.get("anonymized_name", "")),
            headline=str(raw.get("headline", "")),
            summary=str(raw.get("summary", "")),
            location=str(raw.get("location", "")),
            country=str(raw.get("country", "")),
            years_of_experience=float(raw.get("years_of_experience", 0.0)),
            current_title=str(raw.get("current_title", "")),
            current_company=str(raw.get("current_company", "")),
            current_company_size=str(raw.get("current_company_size", "")),
            current_industry=str(raw.get("current_industry", "")),
        )

    def _parse_career_item(self, raw: Dict[str, Any]) -> CareerRecord:
        return CareerRecord(
            company=str(raw.get("company", "")),
            title=str(raw.get("title", "")),
            start_date=_parse_date(str(raw.get("start_date", "1970-01-01"))) or date(1970, 1, 1),
            end_date=_parse_date(raw.get("end_date")),
            duration_months=int(raw.get("duration_months", 0)),
            is_current=bool(raw.get("is_current", False)),
            industry=str(raw.get("industry", "")),
            company_size=str(raw.get("company_size", "")),
            description=str(raw.get("description", "")),
        )

    def _parse_education_item(self, raw: Dict[str, Any]) -> EducationRecord:
        return EducationRecord(
            institution=str(raw.get("institution", "")),
            degree=str(raw.get("degree", "")),
            field_of_study=str(raw.get("field_of_study", "")),
            start_year=int(raw.get("start_year", 1970)),
            end_year=int(raw.get("end_year", 1970)),
            grade=None if raw.get("grade") is None else str(raw.get("grade")),
            tier=None if raw.get("tier") is None else str(raw.get("tier")),
        )

    def _parse_skill_item(self, raw: Dict[str, Any]) -> Skill:
        duration = raw.get("duration_months")
        return Skill(
            name=str(raw.get("name", "")),
            proficiency=str(raw.get("proficiency", "beginner")),
            endorsements=int(raw.get("endorsements", 0)),
            duration_months=None if duration is None else int(duration),
        )

    def _parse_certification(self, raw: Dict[str, Any]) -> Certification:
        return Certification(
            name=str(raw.get("name", "")),
            issuer=str(raw.get("issuer", "")),
            year=int(raw.get("year", 0)),
        )

    def _parse_language(self, raw: Dict[str, Any]) -> LanguageProficiency:
        return LanguageProficiency(
            language=str(raw.get("language", "")),
            proficiency=str(raw.get("proficiency", "")),
        )

    def _parse_redrob_signals(self, raw: Dict[str, Any] | None) -> Optional[RedrobSignals]:
        if raw is None:
            return None

        salary_raw = raw.get("expected_salary_range_inr_lpa", {})
        salary = SalaryRangeINRLPA(
            min_lpa=float(salary_raw.get("min", 0.0)),
            max_lpa=float(salary_raw.get("max", 0.0)),
        )

        scores = raw.get("skill_assessment_scores", {})
        score_map: Dict[str, float] = {}
        if isinstance(scores, dict):
            for key, value in scores.items():
                score_map[str(key)] = float(value)

        signup_date = _parse_date(str(raw.get("signup_date", "1970-01-01")))
        last_active_date = _parse_date(str(raw.get("last_active_date", "1970-01-01")))

        return RedrobSignals(
            profile_completeness_score=float(raw.get("profile_completeness_score", 0.0)),
            signup_date=signup_date or date(1970, 1, 1),
            last_active_date=last_active_date or date(1970, 1, 1),
            open_to_work_flag=bool(raw.get("open_to_work_flag", False)),
            profile_views_received_30d=int(raw.get("profile_views_received_30d", 0)),
            applications_submitted_30d=int(raw.get("applications_submitted_30d", 0)),
            recruiter_response_rate=float(raw.get("recruiter_response_rate", 0.0)),
            avg_response_time_hours=float(raw.get("avg_response_time_hours", 0.0)),
            skill_assessment_scores=score_map,
            connection_count=int(raw.get("connection_count", 0)),
            endorsements_received=int(raw.get("endorsements_received", 0)),
            notice_period_days=int(raw.get("notice_period_days", 0)),
            expected_salary_range_inr_lpa=salary,
            preferred_work_mode=str(raw.get("preferred_work_mode", "")),
            willing_to_relocate=bool(raw.get("willing_to_relocate", False)),
            github_activity_score=float(raw.get("github_activity_score", -1.0)),
            search_appearance_30d=int(raw.get("search_appearance_30d", 0)),
            saved_by_recruiters_30d=int(raw.get("saved_by_recruiters_30d", 0)),
            interview_completion_rate=float(raw.get("interview_completion_rate", 0.0)),
            offer_acceptance_rate=float(raw.get("offer_acceptance_rate", -1.0)),
            verified_email=bool(raw.get("verified_email", False)),
            verified_phone=bool(raw.get("verified_phone", False)),
            linkedin_connected=bool(raw.get("linkedin_connected", False)),
        )
