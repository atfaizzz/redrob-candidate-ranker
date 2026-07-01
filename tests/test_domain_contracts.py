"""Unit tests for core domain contracts."""

from __future__ import annotations

import unittest
from datetime import date

from src.contracts.domain import CandidateProfile, SalaryRangeINRLPA


class TestDomainContracts(unittest.TestCase):
    def test_salary_range_dataclass(self) -> None:
        salary = SalaryRangeINRLPA(min_lpa=10.0, max_lpa=20.0)
        self.assertEqual(salary.min_lpa, 10.0)
        self.assertEqual(salary.max_lpa, 20.0)

    def test_candidate_profile_dataclass(self) -> None:
        profile = CandidateProfile(
            anonymized_name="Candidate",
            headline="AI Engineer",
            summary="Summary",
            location="Noida",
            country="India",
            years_of_experience=6.0,
            current_title="Senior AI Engineer",
            current_company="Redrob",
            current_company_size="201-500",
            current_industry="HR Tech",
        )
        self.assertEqual(profile.current_title, "Senior AI Engineer")
        self.assertEqual(profile.country, "India")


if __name__ == "__main__":
    unittest.main()
