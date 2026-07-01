"""Retrieval strategies for candidate shortlisting and comparison."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, List, Sequence

from src.contracts.domain import Candidate, JobDescription


TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9+#.-]+")


def _tokenize(text: str) -> set[str]:
    return {token.lower() for token in TOKEN_PATTERN.findall(text)}


def _candidate_text(candidate: Candidate) -> str:
    skill_text = " ".join(skill.name for skill in candidate.skills)
    career_titles = " ".join(item.title for item in candidate.career_history)
    return " ".join(
        [
            candidate.profile.headline,
            candidate.profile.summary,
            candidate.profile.current_title,
            skill_text,
            career_titles,
        ]
    )


def _job_query_text(job: JobDescription) -> str:
    return " ".join(
        [
            job.role_title,
            " ".join(job.must_have_requirements),
            " ".join(job.preferred_requirements),
            job.raw_text,
        ]
    )


@dataclass(frozen=True)
class RetrievalCandidate:
    """Candidate with retrieval-level score decomposition."""

    candidate: Candidate
    lexical_score: float
    semantic_score: float
    metadata_score: float
    hybrid_score: float


class CandidateRetriever:
    """Provides lexical, semantic-like and hybrid retrieval methods."""

    def retrieve_lexical(
        self,
        job: JobDescription,
        candidates: Iterable[Candidate],
        k: int,
    ) -> List[RetrievalCandidate]:
        query_tokens = _tokenize(_job_query_text(job))
        scored: List[RetrievalCandidate] = []
        for candidate in candidates:
            candidate_tokens = _tokenize(_candidate_text(candidate))
            overlap = len(query_tokens & candidate_tokens)
            lexical = overlap / max(len(query_tokens), 1)
            metadata = self._metadata_alignment(job, candidate)
            semantic = self._semantic_alignment(job, candidate)
            scored.append(
                RetrievalCandidate(
                    candidate=candidate,
                    lexical_score=lexical,
                    semantic_score=semantic,
                    metadata_score=metadata,
                    hybrid_score=lexical,
                )
            )
        scored.sort(key=lambda item: item.hybrid_score, reverse=True)
        return scored[:k]

    def retrieve_semantic(
        self,
        job: JobDescription,
        candidates: Iterable[Candidate],
        k: int,
    ) -> List[RetrievalCandidate]:
        scored: List[RetrievalCandidate] = []
        for candidate in candidates:
            semantic = self._semantic_alignment(job, candidate)
            metadata = self._metadata_alignment(job, candidate)
            lexical = self._lexical_alignment(job, candidate)
            scored.append(
                RetrievalCandidate(
                    candidate=candidate,
                    lexical_score=lexical,
                    semantic_score=semantic,
                    metadata_score=metadata,
                    hybrid_score=semantic,
                )
            )
        scored.sort(key=lambda item: item.hybrid_score, reverse=True)
        return scored[:k]

    def retrieve_hybrid(
        self,
        job: JobDescription,
        candidates: Iterable[Candidate],
        k: int,
        lexical_weight: float = 0.35,
        semantic_weight: float = 0.45,
        metadata_weight: float = 0.20,
    ) -> List[RetrievalCandidate]:
        scored: List[RetrievalCandidate] = []
        for candidate in candidates:
            lexical = self._lexical_alignment(job, candidate)
            semantic = self._semantic_alignment(job, candidate)
            metadata = self._metadata_alignment(job, candidate)
            hybrid = (
                lexical * lexical_weight
                + semantic * semantic_weight
                + metadata * metadata_weight
            )
            scored.append(
                RetrievalCandidate(
                    candidate=candidate,
                    lexical_score=lexical,
                    semantic_score=semantic,
                    metadata_score=metadata,
                    hybrid_score=hybrid,
                )
            )
        scored.sort(key=lambda item: item.hybrid_score, reverse=True)
        return scored[:k]

    def compare_retrieval_strategies(
        self,
        job: JobDescription,
        candidates: Sequence[Candidate],
        k: int,
    ) -> dict:
        lexical = self.retrieve_lexical(job, candidates, k)
        semantic = self.retrieve_semantic(job, candidates, k)
        hybrid = self.retrieve_hybrid(job, candidates, k)

        lexical_ids = {item.candidate.candidate_id for item in lexical}
        semantic_ids = {item.candidate.candidate_id for item in semantic}
        hybrid_ids = {item.candidate.candidate_id for item in hybrid}

        return {
            "k": k,
            "lexical_vs_semantic_overlap": len(lexical_ids & semantic_ids),
            "lexical_vs_hybrid_overlap": len(lexical_ids & hybrid_ids),
            "semantic_vs_hybrid_overlap": len(semantic_ids & hybrid_ids),
            "hybrid_avg_score": (
                sum(item.hybrid_score for item in hybrid) / max(len(hybrid), 1)
            ),
        }

    def _lexical_alignment(self, job: JobDescription, candidate: Candidate) -> float:
        query_tokens = _tokenize(_job_query_text(job))
        candidate_tokens = _tokenize(_candidate_text(candidate))
        overlap = len(query_tokens & candidate_tokens)
        return overlap / max(len(query_tokens), 1)

    def _semantic_alignment(self, job: JobDescription, candidate: Candidate) -> float:
        must_have_tokens = _tokenize(" ".join(job.must_have_requirements))
        preferred_tokens = _tokenize(" ".join(job.preferred_requirements))
        candidate_tokens = _tokenize(_candidate_text(candidate))

        must_overlap = len(must_have_tokens & candidate_tokens)
        preferred_overlap = len(preferred_tokens & candidate_tokens)

        must_ratio = must_overlap / max(len(must_have_tokens), 1)
        preferred_ratio = preferred_overlap / max(len(preferred_tokens), 1)

        title_bonus = 0.0
        role_tokens = _tokenize(job.role_title)
        title_tokens = _tokenize(candidate.profile.current_title)
        if role_tokens and (role_tokens & title_tokens):
            title_bonus = 0.1

        return min(1.0, 0.7 * must_ratio + 0.2 * preferred_ratio + title_bonus)

    def _metadata_alignment(self, job: JobDescription, candidate: Candidate) -> float:
        location_score = 0.5
        if job.location_constraints:
            candidate_loc = candidate.profile.location.lower()
            loc_hits = [loc for loc in job.location_constraints if loc.lower() in candidate_loc]
            location_score = 1.0 if loc_hits else 0.2

        exp_score = 0.5
        if job.seniority_range_years is not None:
            min_exp, max_exp = job.seniority_range_years
            years = candidate.profile.years_of_experience
            if min_exp <= years <= max_exp:
                exp_score = 1.0
            elif years < min_exp:
                exp_score = max(0.0, years / max(min_exp, 1.0))
            else:
                exp_score = max(0.0, max_exp / max(years, 1.0))

        return 0.5 * location_score + 0.5 * exp_score


def select_retriever(name: str):
    """Return retriever instance by strategy name."""

    normalized = name.strip().lower()
    if normalized in {"lexical", "semantic", "hybrid", "behavioral_hybrid", "sparse"}:
        return CandidateRetriever()
    raise ValueError(f"Unsupported retriever strategy family: {name}")
