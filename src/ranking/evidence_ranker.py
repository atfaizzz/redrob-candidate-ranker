"""Evidence-based candidate ranking with separate confidence estimation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from statistics import pstdev
from typing import Iterable, List, Sequence

from src.contracts.domain import Candidate, EvidenceBreakdown, JobDescription, RankedCandidate
from src.ranking.plausibility import plausibility_penalty
from src.retrieval.strategies import RetrievalCandidate


def _tokenize(text: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9]+", text.lower()) if len(token) >= 2}


def _candidate_tokens(candidate: Candidate) -> set[str]:
    parts = [candidate.profile.headline, candidate.profile.summary, candidate.profile.current_title]
    parts.extend(skill.name for skill in candidate.skills)
    parts.extend(item.title for item in candidate.career_history)
    return _tokenize(" ".join(parts))


@dataclass(frozen=True)
class RankerWeights:
    """Weights controlling evidence contribution to final ranking score."""

    semantic_alignment: float = 0.30
    experience_alignment: float = 0.20
    career_progression: float = 0.15
    behavioral_availability: float = 0.20
    trust_signals: float = 0.15


@dataclass(frozen=True)
class RankedWithDiagnostics:
    """Ranked output plus internal diagnostics for evaluation."""

    ranked: RankedCandidate
    overall_score: float


class EvidenceBasedRanker:
    """Ranks candidates from multiple evidence components."""

    def __init__(self, weights: RankerWeights | None = None) -> None:
        self._weights = weights or RankerWeights()

    def rank(
        self,
        job: JobDescription,
        retrieved_candidates: Sequence[RetrievalCandidate],
        top_n: int,
    ) -> Sequence[RankedCandidate]:
        job_tokens = _tokenize(" ".join([job.role_title, job.raw_text]))
        outputs: List[RankedWithDiagnostics] = []

        for item in retrieved_candidates:
            candidate = item.candidate
            evidence = self._build_evidence(job_tokens, job, candidate, item.hybrid_score)
            penalty = plausibility_penalty(candidate)
            score = self._final_score(evidence, candidate, penalty)
            if penalty == 0.0:
                continue
            reasoning = self._build_reasoning(candidate, evidence)
            outputs.append(
                RankedWithDiagnostics(
                    ranked=RankedCandidate(
                        candidate_id=candidate.candidate_id,
                        rank=0,
                        score=round(score, 6),
                        reasoning=reasoning,
                        evidence=evidence,
                    ),
                    overall_score=score,
                )
            )

        # Sort by score descending; for equal scores sort candidate_id ascending (competition tie-break rule).
        outputs.sort(key=lambda value: (-value.overall_score, value.ranked.candidate_id))
        top = outputs[:top_n]

        ranked: List[RankedCandidate] = []
        for index, item in enumerate(top, start=1):
            ranked.append(
                RankedCandidate(
                    candidate_id=item.ranked.candidate_id,
                    rank=index,
                    score=item.ranked.score,
                    reasoning=item.ranked.reasoning,
                    evidence=item.ranked.evidence,
                )
            )
        return ranked

    def _build_evidence(
        self,
        job_tokens: set[str],
        job: JobDescription,
        candidate: Candidate,
        retrieval_score: float,
    ) -> EvidenceBreakdown:
        semantic_alignment = self._semantic_alignment(job_tokens, candidate)
        experience_alignment = self._experience_alignment(job, candidate)
        career_progression = self._career_progression(candidate)
        behavioral = self._behavioral_alignment(candidate)
        trust = self._trust_alignment(candidate)

        confidence = self._confidence(
            candidate,
            [semantic_alignment, experience_alignment, career_progression, behavioral, trust, retrieval_score],
        )

        return EvidenceBreakdown(
            semantic_alignment=semantic_alignment,
            experience_alignment=experience_alignment,
            career_progression=career_progression,
            behavioral_availability=behavioral,
            trust_signals=trust,
            confidence=confidence,
        )

    def _semantic_alignment(self, job_tokens: set[str], candidate: Candidate) -> float:
        tokens = _candidate_tokens(candidate)
        if not tokens or not job_tokens:
            return 0.0
        return len(tokens & job_tokens) / len(job_tokens)

    def _experience_alignment(self, job: JobDescription, candidate: Candidate) -> float:
        yoe = candidate.profile.years_of_experience
        if job.seniority_range_years is None:
            return min(max(yoe / 10.0, 0.0), 1.0)

        minimum, maximum = job.seniority_range_years
        if minimum <= yoe <= maximum:
            return 1.0
        if yoe < minimum:
            return max(0.0, 1.0 - ((minimum - yoe) / max(minimum, 1.0)))
        return max(0.0, 1.0 - ((yoe - maximum) / max(maximum, 1.0)))

    def _career_progression(self, candidate: Candidate) -> float:
        depth = min(len(candidate.career_history) / 6.0, 1.0)
        seniority_terms = {"senior", "lead", "principal", "staff", "manager", "head"}
        title_tokens = _tokenize(candidate.profile.current_title)
        seniority = 1.0 if title_tokens & seniority_terms else 0.5
        return min((depth * 0.6) + (seniority * 0.4), 1.0)

    def _behavioral_alignment(self, candidate: Candidate) -> float:
        signals = candidate.redrob_signals
        if signals is None:
            return 0.0

        response_time_component = 1.0 / (1.0 + signals.avg_response_time_hours / 48.0)
        return min(
            max(
                (
                    (1.0 if signals.open_to_work_flag else 0.0) * 0.35
                    + signals.recruiter_response_rate * 0.25
                    + signals.interview_completion_rate * 0.2
                    + response_time_component * 0.2
                ),
                0.0,
            ),
            1.0,
        )

    def _trust_alignment(self, candidate: Candidate) -> float:
        signals = candidate.redrob_signals
        if signals is None:
            return 0.0

        verification = (
            (1.0 if signals.verified_email else 0.0)
            + (1.0 if signals.verified_phone else 0.0)
            + (1.0 if signals.linkedin_connected else 0.0)
        ) / 3.0
        completeness = min(max(signals.profile_completeness_score / 100.0, 0.0), 1.0)
        assessment_coverage = 0.0
        if candidate.skills:
            assessment_coverage = min(
                len(signals.skill_assessment_scores) / max(len(candidate.skills), 1),
                1.0,
            )
        return min((verification * 0.4) + (completeness * 0.4) + (assessment_coverage * 0.2), 1.0)

    def _confidence(self, candidate: Candidate, component_scores: Iterable[float]) -> float:
        components = list(component_scores)
        completeness = self._completeness(candidate)
        consistency = self._consistency(candidate)
        agreement = self._agreement(components)
        return min(max(completeness * 0.4 + consistency * 0.35 + agreement * 0.25, 0.0), 1.0)

    def _completeness(self, candidate: Candidate) -> float:
        populated = 0
        total = 6
        if candidate.profile.summary.strip():
            populated += 1
        if candidate.skills:
            populated += 1
        if candidate.career_history:
            populated += 1
        if candidate.education:
            populated += 1
        if candidate.redrob_signals is not None:
            populated += 1
        if candidate.profile.current_title.strip():
            populated += 1
        return populated / total

    def _consistency(self, candidate: Candidate) -> float:
        checks = []
        checks.append(1.0 if sum(1 for item in candidate.career_history if item.is_current) == 1 else 0.0)
        if candidate.redrob_signals is not None:
            salary = candidate.redrob_signals.expected_salary_range_inr_lpa
            checks.append(1.0 if salary.min_lpa <= salary.max_lpa else 0.0)
            checks.append(
                1.0
                if candidate.redrob_signals.signup_date <= candidate.redrob_signals.last_active_date
                else 0.0
            )
        if not checks:
            return 0.0
        return sum(checks) / len(checks)

    def _agreement(self, components: List[float]) -> float:
        bounded = [min(max(value, 0.0), 1.0) for value in components]
        if not bounded:
            return 0.0
        if len(bounded) == 1:
            return bounded[0]
        sigma = pstdev(bounded)
        return max(0.0, 1.0 - sigma)

    def _final_score(
        self,
        evidence: EvidenceBreakdown,
        candidate: Candidate,
        penalty: float | None = None,
    ) -> float:
        score = (
            evidence.semantic_alignment * self._weights.semantic_alignment
            + evidence.experience_alignment * self._weights.experience_alignment
            + evidence.career_progression * self._weights.career_progression
            + evidence.behavioral_availability * self._weights.behavioral_availability
            + evidence.trust_signals * self._weights.trust_signals
        )
        adjusted = score * (plausibility_penalty(candidate) if penalty is None else penalty)
        return min(max(adjusted, 0.0), 1.0)

    def _build_reasoning(self, candidate: Candidate, evidence: EvidenceBreakdown) -> str:
        strengths = []
        if evidence.semantic_alignment >= 0.3:
            strengths.append("strong job-skill semantic overlap")
        if evidence.experience_alignment >= 0.7:
            strengths.append("experience level aligned with JD")
        if evidence.behavioral_availability >= 0.6:
            strengths.append("healthy recruiter engagement signals")
        if evidence.trust_signals >= 0.6:
            strengths.append("high profile trust/completeness")

        if not strengths:
            strengths.append("partial evidence alignment")

        risk = ""
        if evidence.confidence < 0.5:
            risk = " Confidence is moderate because evidence consistency/completeness is limited."

        primary_skills = ", ".join(skill.name for skill in candidate.skills[:3]) or "listed skills"
        return (
            f"{candidate.profile.current_title} with {candidate.profile.years_of_experience:.1f} years; "
            f"key skills include {primary_skills}. "
            f"Ranking is driven by {', '.join(strengths)}."
            f" Confidence={evidence.confidence:.2f}."
            f"{risk}"
        )
