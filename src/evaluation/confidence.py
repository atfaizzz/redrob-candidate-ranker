"""Confidence quality evaluation utilities."""

from __future__ import annotations

from typing import Dict, Sequence

from src.contracts.domain import RankedCandidate


def confidence_relevance_correlation(
    ranked: Sequence[RankedCandidate],
    binary_relevance: Dict[str, int],
) -> float:
    """Compute point-biserial style correlation between confidence and relevance."""

    if not ranked:
        return 0.0

    confidences = [row.evidence.confidence for row in ranked]
    labels = [1 if binary_relevance.get(row.candidate_id, 0) > 0 else 0 for row in ranked]

    if len(set(labels)) <= 1:
        return 0.0

    mean_conf = sum(confidences) / len(confidences)
    mean_pos = sum(c for c, y in zip(confidences, labels) if y == 1) / max(sum(labels), 1)
    mean_neg = sum(c for c, y in zip(confidences, labels) if y == 0) / max(len(labels) - sum(labels), 1)

    variance = sum((c - mean_conf) ** 2 for c in confidences) / len(confidences)
    std = variance**0.5
    if std == 0:
        return 0.0

    p = sum(labels) / len(labels)
    q = 1.0 - p
    return ((mean_pos - mean_neg) / std) * (p * q) ** 0.5


def confidence_bucket_summary(ranked: Sequence[RankedCandidate]) -> dict:
    """Bucket confidence scores for interpretability diagnostics."""

    buckets = {"high": 0, "medium": 0, "low": 0}
    for row in ranked:
        c = row.evidence.confidence
        if c >= 0.75:
            buckets["high"] += 1
        elif c >= 0.5:
            buckets["medium"] += 1
        else:
            buckets["low"] += 1
    return buckets
