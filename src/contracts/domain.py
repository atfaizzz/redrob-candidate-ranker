"""Canonical domain models for recruiter intelligence workflows.

These dataclasses define stable internal objects shared across pipeline modules.
They are intentionally detached from raw dataset dictionaries to keep module
boundaries explicit and testable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Optional


@dataclass(frozen=True)
class SalaryRangeINRLPA:
    """Expected salary range in INR Lakhs Per Annum."""

    min_lpa: float
    max_lpa: float


@dataclass(frozen=True)
class Skill:
    """A candidate skill entry."""

    name: str
    proficiency: str
    endorsements: int
    duration_months: Optional[int] = None


@dataclass(frozen=True)
class Certification:
    """A candidate certification entry."""

    name: str
    issuer: str
    year: int


@dataclass(frozen=True)
class LanguageProficiency:
    """A candidate language and proficiency entry."""

    language: str
    proficiency: str


@dataclass(frozen=True)
class EducationRecord:
    """A single education history entry."""

    institution: str
    degree: str
    field_of_study: str
    start_year: int
    end_year: int
    grade: Optional[str] = None
    tier: Optional[str] = None


@dataclass(frozen=True)
class CareerRecord:
    """A single career history entry."""

    company: str
    title: str
    start_date: date
    end_date: Optional[date]
    duration_months: int
    is_current: bool
    industry: str
    company_size: str
    description: str


@dataclass(frozen=True)
class CandidateProfile:
    """Top-level profile information for a candidate."""

    anonymized_name: str
    headline: str
    summary: str
    location: str
    country: str
    years_of_experience: float
    current_title: str
    current_company: str
    current_company_size: str
    current_industry: str


@dataclass(frozen=True)
class RedrobSignals:
    """Behavioral and platform signals used for ranking confidence."""

    profile_completeness_score: float
    signup_date: date
    last_active_date: date
    open_to_work_flag: bool
    profile_views_received_30d: int
    applications_submitted_30d: int
    recruiter_response_rate: float
    avg_response_time_hours: float
    skill_assessment_scores: Dict[str, float]
    connection_count: int
    endorsements_received: int
    notice_period_days: int
    expected_salary_range_inr_lpa: SalaryRangeINRLPA
    preferred_work_mode: str
    willing_to_relocate: bool
    github_activity_score: float
    search_appearance_30d: int
    saved_by_recruiters_30d: int
    interview_completion_rate: float
    offer_acceptance_rate: float
    verified_email: bool
    verified_phone: bool
    linkedin_connected: bool


@dataclass(frozen=True)
class Candidate:
    """Canonical candidate object consumed by retrieval and ranking modules."""

    candidate_id: str
    profile: CandidateProfile
    career_history: List[CareerRecord]
    education: List[EducationRecord]
    skills: List[Skill]
    certifications: List[Certification] = field(default_factory=list)
    languages: List[LanguageProficiency] = field(default_factory=list)
    redrob_signals: Optional[RedrobSignals] = None


@dataclass(frozen=True)
class JobDescription:
    """Canonical job representation created after parsing the job document."""

    role_title: str
    raw_text: str
    location_constraints: List[str] = field(default_factory=list)
    must_have_requirements: List[str] = field(default_factory=list)
    preferred_requirements: List[str] = field(default_factory=list)
    disqualifiers: List[str] = field(default_factory=list)
    seniority_range_years: Optional[tuple[float, float]] = None


@dataclass(frozen=True)
class EvidenceBreakdown:
    """Explainable score decomposition per candidate."""

    semantic_alignment: float
    experience_alignment: float
    career_progression: float
    behavioral_availability: float
    trust_signals: float
    confidence: float


@dataclass(frozen=True)
class RankedCandidate:
    """Ranking output row before CSV rendering."""

    candidate_id: str
    rank: int
    score: float
    reasoning: str
    evidence: EvidenceBreakdown
