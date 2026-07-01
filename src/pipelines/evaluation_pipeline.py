"""Evaluation and experiment orchestration for README_04 phase."""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Sequence

from src.config.settings import AppSettings, load_config, parse_app_settings
from src.contracts.domain import Candidate
from src.evaluation.ablation import AblationRunner
from src.evaluation.confidence import (
    confidence_bucket_summary,
    confidence_relevance_correlation,
)
from src.evaluation.experiment_tracking import ExperimentTracker
from src.evaluation.explainability_eval import evaluate_explanations
from src.evaluation.metrics import (
    average_precision,
    candidate_coverage,
    mrr,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
)
from src.evaluation.ranking_analysis import top_k_id_overlap
from src.evaluation.robustness import (
    perturb_duplicate_candidates,
    perturb_missing_behavioral_signals,
    perturb_missing_education,
    perturb_missing_skills,
)
from src.explainability.reasoning import ExplanationGenerator
from src.ingestion.jsonl_reader import iter_jsonl_records
from src.monitoring.metrics import PipelineMetrics, StageMetric
from src.parsing.candidate_parser import CandidateParser
from src.parsing.job_parser import JobDescriptionParser
from src.preprocessing.normalization import normalize_candidate_record
from src.qa.preflight import RepositoryHealthChecker
from src.ranking.evidence_ranker import EvidenceBasedRanker
from src.retrieval.strategies import CandidateRetriever
from src.validation.candidate_validation import (
    CanonicalCandidateValidator,
    RawCandidateRecordValidator,
)


@dataclass(frozen=True)
class EvaluationSummary:
    """High-level evaluation outputs."""

    scanned_candidates: int
    parsed_candidates: int
    validation_failures: int
    retrieval_metrics: Dict[str, float]
    ranking_metrics: Dict[str, float]
    confidence_metrics: Dict[str, float]
    explainability_metrics: Dict[str, float]
    ablation_topk_overlap: Dict[str, float]
    robustness_topk_overlap: Dict[str, float]
    performance_metrics: Dict[str, float]


class EvaluationPipeline:
    """Runs evaluation hierarchy and logs reproducible experiment records."""

    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings
        self._candidate_parser = CandidateParser()
        self._job_parser = JobDescriptionParser()
        self._raw_validator = RawCandidateRecordValidator()
        self._canonical_validator = CanonicalCandidateValidator()
        self._retriever = CandidateRetriever()
        self._ranker = EvidenceBasedRanker()
        self._reasoner = ExplanationGenerator()
        self._ablation = AblationRunner()
        self._preflight = RepositoryHealthChecker()
        self._metrics = PipelineMetrics()

    @classmethod
    def from_config_file(cls, config_path: Path) -> "EvaluationPipeline":
        config = load_config(config_path)
        return cls(parse_app_settings(config))

    def execute(self) -> EvaluationSummary:
        runtime = self._settings.runtime
        retrieval_cfg = self._settings.retrieval
        self._preflight.ensure_healthy(self._settings)

        t_job = time.perf_counter()
        job = self._job_parser.parse(Path(runtime.job_description_path))
        self._metrics.add(
            StageMetric("evaluation_job_parsing", (time.perf_counter() - t_job) * 1000, 1)
        )

        candidates: List[Candidate] = []
        scanned = 0
        failures = 0
        t_load = time.perf_counter()
        for _, raw in iter_jsonl_records(Path(runtime.candidates_path)):
            scanned += 1
            normalized = normalize_candidate_record(raw)

            raw_issues = self._raw_validator.validate(normalized)
            if raw_issues:
                failures += 1
                if runtime.strict_validation:
                    continue

            candidate = self._candidate_parser.parse(normalized)
            canonical_issues = self._canonical_validator.validate(candidate)
            if canonical_issues:
                failures += 1
                if runtime.strict_validation:
                    continue
            candidates.append(candidate)

            if runtime.max_candidates_to_process is not None and scanned >= runtime.max_candidates_to_process:
                break

        self._metrics.add(
            StageMetric(
                "evaluation_candidate_loading",
                (time.perf_counter() - t_load) * 1000,
                scanned,
                failures=failures,
            )
        )

        initial_k = max(1, min(retrieval_cfg.initial_k, len(candidates)))

        t_retrieval = time.perf_counter()
        lexical = self._retriever.retrieve_lexical(job, candidates, initial_k)
        semantic = self._retriever.retrieve_semantic(job, candidates, initial_k)
        hybrid = self._retriever.retrieve_hybrid(job, candidates, initial_k)
        self._metrics.add(
            StageMetric(
                "evaluation_retrieval",
                (time.perf_counter() - t_retrieval) * 1000,
                initial_k,
            )
        )

        selected = hybrid
        ranked = self._ranker.rank(job, selected, runtime.top_n)
        by_id = {candidate.candidate_id: candidate for candidate in candidates}
        ranked = self._reasoner.attach_reasoning(by_id, list(ranked))

        pseudo_relevance = self._pseudo_relevance(by_id)
        graded_relevance = self._graded_relevance(by_id)

        predicted_ids = [row.candidate_id for row in ranked]
        lexical_ids = [item.candidate.candidate_id for item in lexical[: runtime.top_n]]
        semantic_ids = [item.candidate.candidate_id for item in semantic[: runtime.top_n]]
        hybrid_ids = [item.candidate.candidate_id for item in hybrid[: runtime.top_n]]

        retrieval_metrics = {
            "precision_at_20": precision_at_k(hybrid_ids, pseudo_relevance, 20),
            "recall_at_20": recall_at_k(hybrid_ids, pseudo_relevance, 20),
            "mrr": mrr(hybrid_ids, pseudo_relevance),
            "ndcg_at_20": ndcg_at_k(hybrid_ids, graded_relevance, 20),
            "coverage": candidate_coverage(hybrid_ids),
            "lexical_semantic_top20_overlap": top_k_id_overlap(lexical_ids, semantic_ids, 20),
            "semantic_hybrid_top20_overlap": top_k_id_overlap(semantic_ids, hybrid_ids, 20),
        }

        ranking_metrics = {
            "precision_at_10": precision_at_k(predicted_ids, pseudo_relevance, 10),
            "precision_at_20": precision_at_k(predicted_ids, pseudo_relevance, 20),
            "recall_at_20": recall_at_k(predicted_ids, pseudo_relevance, 20),
            "map_at_50": average_precision(predicted_ids, pseudo_relevance, 50),
            "mrr": mrr(predicted_ids, pseudo_relevance),
            "ndcg_at_10": ndcg_at_k(predicted_ids, graded_relevance, 10),
            "ndcg_at_50": ndcg_at_k(predicted_ids, graded_relevance, 50),
        }

        confidence_metrics = {
            "confidence_relevance_correlation": confidence_relevance_correlation(ranked, {k: 1 for k in pseudo_relevance}),
            **confidence_bucket_summary(ranked),
        }

        explainability_metrics = evaluate_explanations(ranked, by_id)

        ablations = self._ablation.run(job, selected, runtime.top_n)
        baseline_ids = [row.candidate_id for row in ablations["baseline"]]
        ablation_topk_overlap = {
            name: top_k_id_overlap(
                baseline_ids,
                [row.candidate_id for row in rows],
                min(20, len(baseline_ids)),
            )
            for name, rows in ablations.items()
            if name != "baseline"
        }

        robustness_topk_overlap = self._robustness_analysis(job, candidates, baseline_ids, runtime.top_n)

        summary = EvaluationSummary(
            scanned_candidates=scanned,
            parsed_candidates=len(candidates),
            validation_failures=failures,
            retrieval_metrics=retrieval_metrics,
            ranking_metrics=ranking_metrics,
            confidence_metrics=confidence_metrics,
            explainability_metrics=explainability_metrics,
            ablation_topk_overlap=ablation_topk_overlap,
            robustness_topk_overlap=robustness_topk_overlap,
            performance_metrics=self._metrics.summary(),
        )

        tracker_path = Path(runtime.repository_root) / "experiments" / "experiment_log.jsonl"
        tracker = ExperimentTracker(tracker_path)
        record = ExperimentTracker.build_record(
            experiment_id=f"eval_{int(time.time())}",
            config_snapshot={
                "runtime": asdict(self._settings.runtime),
                "retrieval": asdict(self._settings.retrieval),
                "ranking": asdict(self._settings.ranking),
            },
            dataset_version=Path(runtime.candidates_path).name,
            model_summary={
                "retriever": retrieval_cfg.strategy,
                "ranker": self._settings.ranking.strategy,
                "explainability": "reasoning_generator_v1",
            },
            hyperparameters={
                "top_n": runtime.top_n,
                "initial_k": retrieval_cfg.initial_k,
            },
            metrics={
                "retrieval": retrieval_metrics,
                "ranking": ranking_metrics,
                "confidence": confidence_metrics,
                "explainability": explainability_metrics,
                "ablation": ablation_topk_overlap,
                "robustness": robustness_topk_overlap,
                "performance": summary.performance_metrics,
            },
            observations="Offline pseudo-label evaluation to compare ranking architectures.",
            decision="retain" if ranking_metrics["ndcg_at_10"] >= 0.4 else "investigate",
            git_commit=None,
        )
        tracker.log(record)

        return summary

    def _pseudo_relevance(self, candidates_by_id: Dict[str, Candidate]) -> set[str]:
        relevant: set[str] = set()
        for candidate_id, candidate in candidates_by_id.items():
            title = candidate.profile.current_title.lower()
            text = (candidate.profile.summary + " " + candidate.profile.headline).lower()
            ai_keywords = ["ai", "machine learning", "ml", "retrieval", "ranking", "llm", "embedding"]
            keyword_hits = sum(1 for kw in ai_keywords if kw in text or kw in title)
            if keyword_hits >= 2 and candidate.profile.years_of_experience >= 4.0:
                relevant.add(candidate_id)
        return relevant

    def _graded_relevance(self, candidates_by_id: Dict[str, Candidate]) -> Dict[str, int]:
        graded: Dict[str, int] = {}
        for candidate_id, candidate in candidates_by_id.items():
            score = 0
            title = candidate.profile.current_title.lower()
            if "ai" in title or "ml" in title:
                score += 2
            if candidate.profile.years_of_experience >= 5.0:
                score += 1
            if any(skill.name.lower() in {"retrieval", "ranking", "embeddings", "python"} for skill in candidate.skills):
                score += 1
            graded[candidate_id] = score
        return graded

    def _robustness_analysis(
        self,
        job,
        candidates: Sequence[Candidate],
        baseline_ids: Sequence[str],
        top_n: int,
    ) -> Dict[str, float]:
        scenarios = {
            "missing_skills": perturb_missing_skills(candidates),
            "missing_education": perturb_missing_education(candidates),
            "missing_behavior": perturb_missing_behavioral_signals(candidates),
            "duplicates": perturb_duplicate_candidates(candidates),
        }

        overlaps: Dict[str, float] = {}
        for name, perturbed_candidates in scenarios.items():
            retrieved = self._retriever.retrieve_hybrid(job, perturbed_candidates, max(top_n, 50))
            ranked = self._ranker.rank(job, retrieved, top_n)
            scenario_ids = [row.candidate_id for row in ranked]
            overlaps[name] = top_k_id_overlap(
                baseline_ids,
                scenario_ids,
                min(20, len(baseline_ids), len(scenario_ids)),
            )
        return overlaps
