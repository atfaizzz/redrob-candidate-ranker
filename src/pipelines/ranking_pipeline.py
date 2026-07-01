"""ML ranking pipeline for multi-evidence retrieval and ranking."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from src.config.settings import AppSettings, load_config, parse_app_settings
from src.contracts.domain import Candidate, RankedCandidate
from src.evaluation.ranking_analysis import (
    summarize_ranked_candidates,
    summarize_retrieval_candidates,
    top_k_id_overlap,
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
class RankingPipelineSummary:
    """Summary artifacts for ranking phase verification."""

    scanned_candidates: int
    parsed_candidates: int
    validation_failures: int
    retrieved_candidates: int
    ranked_candidates: int
    retrieval_comparison: Dict[str, float]
    retrieval_summary: Dict[str, float]
    ranking_summary: Dict[str, float]
    metrics: Dict[str, float]


@dataclass(frozen=True)
class RankingPipelineResult:
    """Detailed ranking output used by dashboard and analysis modules."""

    ranked_candidates: List[RankedCandidate]
    summary: RankingPipelineSummary
    candidates_by_id: Dict[str, Candidate]


class RankingPipeline:
    """Runs README_03 ranking workflow end-to-end."""

    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings
        self._candidate_parser = CandidateParser()
        self._job_parser = JobDescriptionParser()
        self._raw_validator = RawCandidateRecordValidator()
        self._canonical_validator = CanonicalCandidateValidator()
        self._retriever = CandidateRetriever()
        self._ranker = EvidenceBasedRanker()
        self._reasoning = ExplanationGenerator()
        self._preflight = RepositoryHealthChecker()
        self._metrics = PipelineMetrics()

    @classmethod
    def from_config_file(cls, config_path: Path) -> "RankingPipeline":
        config = load_config(config_path)
        settings = parse_app_settings(config)
        return cls(settings)

    def execute(self) -> tuple[List[RankedCandidate], RankingPipelineSummary]:
        result = self.execute_detailed()
        return result.ranked_candidates, result.summary

    def execute_detailed(self) -> RankingPipelineResult:
        runtime = self._settings.runtime
        retrieval_cfg = self._settings.retrieval
        self._preflight.ensure_healthy(self._settings)

        t_job = time.perf_counter()
        job = self._job_parser.parse(Path(runtime.job_description_path))
        self._metrics.add(
            StageMetric(
                stage_name="job_understanding",
                duration_ms=(time.perf_counter() - t_job) * 1000,
                processed_records=1,
            )
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
                stage_name="candidate_understanding",
                duration_ms=(time.perf_counter() - t_load) * 1000,
                processed_records=scanned,
                failures=failures,
            )
        )

        initial_k = max(1, min(retrieval_cfg.initial_k, len(candidates)))

        t_compare = time.perf_counter()
        lexical = self._retriever.retrieve_lexical(job, candidates, initial_k)
        semantic = self._retriever.retrieve_semantic(job, candidates, initial_k)
        hybrid = self._retriever.retrieve_hybrid(job, candidates, initial_k)
        lexical_ids = [item.candidate.candidate_id for item in lexical]
        semantic_ids = [item.candidate.candidate_id for item in semantic]
        hybrid_ids = [item.candidate.candidate_id for item in hybrid]

        compare = {
            "lexical_semantic_topk_overlap": top_k_id_overlap(lexical_ids, semantic_ids, min(50, initial_k)),
            "lexical_hybrid_topk_overlap": top_k_id_overlap(lexical_ids, hybrid_ids, min(50, initial_k)),
            "semantic_hybrid_topk_overlap": top_k_id_overlap(semantic_ids, hybrid_ids, min(50, initial_k)),
        }
        self._metrics.add(
            StageMetric(
                stage_name="retrieval_comparison",
                duration_ms=(time.perf_counter() - t_compare) * 1000,
                processed_records=initial_k,
            )
        )

        retrieval_strategy = retrieval_cfg.strategy.strip().lower()
        if retrieval_strategy == "lexical":
            selected = lexical
        elif retrieval_strategy == "semantic":
            selected = semantic
        else:
            selected = hybrid

        t_rank = time.perf_counter()
        ranked = self._ranker.rank(job, selected, top_n=runtime.top_n)
        id_to_candidate = {candidate.candidate_id: candidate for candidate in candidates}
        ranked = self._reasoning.attach_reasoning(id_to_candidate, list(ranked))
        self._metrics.add(
            StageMetric(
                stage_name="candidate_ranking",
                duration_ms=(time.perf_counter() - t_rank) * 1000,
                processed_records=len(ranked),
            )
        )

        summary = RankingPipelineSummary(
            scanned_candidates=scanned,
            parsed_candidates=len(candidates),
            validation_failures=failures,
            retrieved_candidates=len(selected),
            ranked_candidates=len(ranked),
            retrieval_comparison=compare,
            retrieval_summary=summarize_retrieval_candidates(selected),
            ranking_summary=summarize_ranked_candidates(ranked),
            metrics=self._metrics.summary(),
        )

        return RankingPipelineResult(
            ranked_candidates=list(ranked),
            summary=summary,
            candidates_by_id=id_to_candidate,
        )
