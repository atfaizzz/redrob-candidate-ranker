"""Core retrieval and ranking metrics for offline evaluation."""

from __future__ import annotations

import math
from typing import Dict, Iterable, Sequence


def precision_at_k(predicted: Sequence[str], relevant: set[str], k: int) -> float:
    """Compute Precision@K."""

    top_k = predicted[:k]
    if not top_k:
        return 0.0
    hits = sum(1 for cid in top_k if cid in relevant)
    return hits / len(top_k)


def recall_at_k(predicted: Sequence[str], relevant: set[str], k: int) -> float:
    """Compute Recall@K."""

    if not relevant:
        return 0.0
    top_k = predicted[:k]
    hits = sum(1 for cid in top_k if cid in relevant)
    return hits / len(relevant)


def mrr(predicted: Sequence[str], relevant: set[str]) -> float:
    """Compute mean reciprocal rank for one ranked list."""

    for idx, cid in enumerate(predicted, start=1):
        if cid in relevant:
            return 1.0 / idx
    return 0.0


def average_precision(predicted: Sequence[str], relevant: set[str], k: int | None = None) -> float:
    """Compute average precision for a ranked list."""

    if not relevant:
        return 0.0

    limit = len(predicted) if k is None else min(k, len(predicted))
    running_hits = 0
    score_sum = 0.0
    for idx, cid in enumerate(predicted[:limit], start=1):
        if cid in relevant:
            running_hits += 1
            score_sum += running_hits / idx

    denom = min(len(relevant), limit) if limit > 0 else 1
    if denom == 0:
        return 0.0
    return score_sum / denom


def ndcg_at_k(predicted: Sequence[str], graded_relevance: Dict[str, int], k: int) -> float:
    """Compute NDCG@K using graded relevance mapping."""

    def dcg(items: Sequence[str]) -> float:
        total = 0.0
        for idx, cid in enumerate(items, start=1):
            rel = max(0, int(graded_relevance.get(cid, 0)))
            gain = (2**rel - 1) / math.log2(idx + 1)
            total += gain
        return total

    top_k = predicted[:k]
    ideal_ids = sorted(graded_relevance.keys(), key=lambda cid: graded_relevance[cid], reverse=True)[:k]
    ideal = dcg(ideal_ids)
    if ideal == 0:
        return 0.0
    return dcg(top_k) / ideal


def candidate_coverage(predicted: Sequence[str]) -> float:
    """Fraction of unique candidates in a ranked list."""

    if not predicted:
        return 0.0
    return len(set(predicted)) / len(predicted)


def candidate_diversity(labels: Sequence[str]) -> float:
    """Simple diversity proxy from categorical labels in ranked order."""

    if not labels:
        return 0.0
    return len(set(labels)) / len(labels)
