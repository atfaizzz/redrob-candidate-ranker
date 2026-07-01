"""Evaluation package exports."""

from .confidence import confidence_bucket_summary, confidence_relevance_correlation
from .experiment_tracking import ExperimentRecord, ExperimentTracker
from .explainability_eval import evaluate_explanations
from .metrics import (
	average_precision,
	candidate_coverage,
	candidate_diversity,
	mrr,
	ndcg_at_k,
	precision_at_k,
	recall_at_k,
)
from .ranking_analysis import (
	summarize_ranked_candidates,
	summarize_retrieval_candidates,
	top_k_id_overlap,
)

__all__ = [
	"average_precision",
	"candidate_coverage",
	"candidate_diversity",
	"confidence_bucket_summary",
	"confidence_relevance_correlation",
	"evaluate_explanations",
	"ExperimentRecord",
	"ExperimentTracker",
	"mrr",
	"ndcg_at_k",
	"precision_at_k",
	"recall_at_k",
	"summarize_ranked_candidates",
	"summarize_retrieval_candidates",
	"top_k_id_overlap",
]
