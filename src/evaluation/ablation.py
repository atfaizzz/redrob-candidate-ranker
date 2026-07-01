"""Ablation runners for ranking component contribution analysis."""

from __future__ import annotations

from dataclasses import replace
from typing import Dict, Sequence

from src.contracts.domain import JobDescription, RankedCandidate
from src.ranking.evidence_ranker import EvidenceBasedRanker, RankerWeights
from src.retrieval.strategies import RetrievalCandidate


class AblationRunner:
    """Runs controlled ablations by mutating ranker weights."""

    def run(
        self,
        job: JobDescription,
        retrieved: Sequence[RetrievalCandidate],
        top_n: int,
    ) -> Dict[str, Sequence[RankedCandidate]]:
        baseline_weights = RankerWeights()
        baseline = EvidenceBasedRanker(weights=baseline_weights).rank(job, retrieved, top_n)

        no_behavioral = EvidenceBasedRanker(
            weights=replace(baseline_weights, behavioral_availability=0.0)
        ).rank(job, retrieved, top_n)

        no_career = EvidenceBasedRanker(
            weights=replace(baseline_weights, career_progression=0.0)
        ).rank(job, retrieved, top_n)

        no_trust = EvidenceBasedRanker(
            weights=replace(baseline_weights, trust_signals=0.0)
        ).rank(job, retrieved, top_n)

        semantic_only = EvidenceBasedRanker(
            weights=RankerWeights(
                semantic_alignment=1.0,
                experience_alignment=0.0,
                career_progression=0.0,
                behavioral_availability=0.0,
                trust_signals=0.0,
            )
        ).rank(job, retrieved, top_n)

        return {
            "baseline": baseline,
            "ablation_no_behavioral": no_behavioral,
            "ablation_no_career": no_career,
            "ablation_no_trust": no_trust,
            "ablation_semantic_only": semantic_only,
        }
