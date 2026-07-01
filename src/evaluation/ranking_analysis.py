"""Lightweight ranking evaluation utilities for architecture comparison."""

from __future__ import annotations

from typing import Sequence

from src.contracts.domain import RankedCandidate
from src.retrieval.strategies import RetrievalCandidate


def top_k_id_overlap(a: Sequence[str], b: Sequence[str], k: int) -> float:
    """Compute overlap ratio in top-k sets."""

    a_set = set(a[:k])
    b_set = set(b[:k])
    return len(a_set & b_set) / max(k, 1)


def summarize_retrieval_candidates(rows: Sequence[RetrievalCandidate]) -> dict:
    """Aggregate retrieval scores for quick architecture sanity checks."""

    count = len(rows)
    if count == 0:
        return {
            "count": 0,
            "avg_lexical": 0.0,
            "avg_semantic": 0.0,
            "avg_metadata": 0.0,
            "avg_hybrid": 0.0,
        }

    return {
        "count": count,
        "avg_lexical": sum(row.lexical_score for row in rows) / count,
        "avg_semantic": sum(row.semantic_score for row in rows) / count,
        "avg_metadata": sum(row.metadata_score for row in rows) / count,
        "avg_hybrid": sum(row.hybrid_score for row in rows) / count,
    }


def summarize_ranked_candidates(rows: Sequence[RankedCandidate]) -> dict:
    """Aggregate ranking evidence and confidence signals."""

    count = len(rows)
    if count == 0:
        return {
            "count": 0,
            "avg_score": 0.0,
            "avg_confidence": 0.0,
        }

    avg_score = sum(row.score for row in rows) / count
    avg_confidence = sum(row.evidence.confidence for row in rows) / count
    return {
        "count": count,
        "avg_score": avg_score,
        "avg_confidence": avg_confidence,
    }
