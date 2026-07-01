"""Tests for candidate and job parsing layers."""

from __future__ import annotations

import unittest
from pathlib import Path

from src.parsing.candidate_parser import CandidateParser
from src.parsing.job_parser import JobDescriptionParser


class TestParsing(unittest.TestCase):
    def test_candidate_parser_minimal_record(self) -> None:
        raw = {
            "candidate_id": "CAND_0000001",
            "profile": {
                "anonymized_name": "A",
                "headline": "H",
                "summary": "S",
                "location": "L",
                "country": "India",
                "years_of_experience": 5.0,
                "current_title": "T",
                "current_company": "C",
                "current_company_size": "201-500",
                "current_industry": "IT",
            },
            "career_history": [
                {
                    "company": "C",
                    "title": "T",
                    "start_date": "2020-01-01",
                    "end_date": None,
                    "duration_months": 50,
                    "is_current": True,
                    "industry": "IT",
                    "company_size": "201-500",
                    "description": "D",
                }
            ],
            "education": [],
            "skills": [],
            "certifications": [],
            "languages": [],
            "redrob_signals": {
                "profile_completeness_score": 90,
                "signup_date": "2024-01-01",
                "last_active_date": "2024-02-01",
                "open_to_work_flag": True,
                "profile_views_received_30d": 1,
                "applications_submitted_30d": 1,
                "recruiter_response_rate": 0.5,
                "avg_response_time_hours": 2.0,
                "skill_assessment_scores": {},
                "connection_count": 1,
                "endorsements_received": 1,
                "notice_period_days": 30,
                "expected_salary_range_inr_lpa": {"min": 10.0, "max": 20.0},
                "preferred_work_mode": "hybrid",
                "willing_to_relocate": False,
                "github_activity_score": -1,
                "search_appearance_30d": 1,
                "saved_by_recruiters_30d": 1,
                "interview_completion_rate": 0.5,
                "offer_acceptance_rate": -1,
                "verified_email": True,
                "verified_phone": True,
                "linkedin_connected": False,
            },
        }

        candidate = CandidateParser().parse(raw)
        self.assertEqual(candidate.candidate_id, "CAND_0000001")
        self.assertEqual(candidate.profile.country, "India")

    def test_job_parser_docx(self) -> None:
        path = Path("c:/Users/Faiz Abid/Desktop/India_Runs/India_runs_data_and_ai_challenge/job_description.docx")
        job = JobDescriptionParser().parse(path)
        self.assertTrue(job.role_title)
        self.assertIn("AI", job.raw_text)


if __name__ == "__main__":
    unittest.main()
