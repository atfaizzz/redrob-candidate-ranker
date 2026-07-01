"""Feature extraction isolated from retrieval and ranking."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from src.contracts.domain import Candidate


@dataclass(frozen=True)
class CandidateFeatures:
    """Interpretable feature view for a candidate."""

    candidate_id: str
    features: Dict[str, float]


class CandidateFeatureExtractor:
    """Creates deterministic candidate features for downstream use."""

    def extract(self, candidate: Candidate) -> CandidateFeatures:
        open_to_work = 0.0
        profile_completeness = 0.0
        if candidate.redrob_signals is not None:
            open_to_work = 1.0 if candidate.redrob_signals.open_to_work_flag else 0.0
            profile_completeness = candidate.redrob_signals.profile_completeness_score

        features = {
            "years_of_experience": candidate.profile.years_of_experience,
            "skills_count": float(len(candidate.skills)),
            "career_records_count": float(len(candidate.career_history)),
            "education_records_count": float(len(candidate.education)),
            "open_to_work": open_to_work,
            "profile_completeness_score": profile_completeness,
        }
        return CandidateFeatures(candidate_id=candidate.candidate_id, features=features)
