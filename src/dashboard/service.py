"""Recruiter dashboard service orchestrating ranking and interaction actions."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence

from src.config.settings import AppSettings
from src.contracts.domain import Candidate, RankedCandidate
from src.dashboard.view_models import CandidateCard, build_candidate_cards
from src.pipelines.ranking_pipeline import RankingPipeline, RankingPipelineResult


@dataclass(frozen=True)
class RecruiterDashboardState:
    """State payload consumed by recruiter-facing UI."""

    cards: List[CandidateCard]
    ranked: List[RankedCandidate]
    candidates_by_id: Dict[str, Candidate]
    summary: dict


class RecruiterDashboardService:
    """High-level dashboard operations for recruiter workflow."""

    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings
        self._pipeline = RankingPipeline(settings)

    def run_ranking(self) -> RecruiterDashboardState:
        """Execute ranking workflow and transform into dashboard state."""

        result: RankingPipelineResult = self._pipeline.execute_detailed()
        cards = build_candidate_cards(result.ranked_candidates, result.candidates_by_id)
        summary = {
            "total_candidates": result.summary.parsed_candidates,
            "retrieved_candidates": result.summary.retrieved_candidates,
            "ranked_candidates": result.summary.ranked_candidates,
            "ranking_summary": result.summary.ranking_summary,
            "retrieval_summary": result.summary.retrieval_summary,
            "metrics": result.summary.metrics,
        }
        return RecruiterDashboardState(
            cards=cards,
            ranked=list(result.ranked_candidates),
            candidates_by_id=result.candidates_by_id,
            summary=summary,
        )

    def export_shortlist(
        self,
        ranked: Sequence[RankedCandidate],
        shortlisted_ids: Iterable[str],
    ) -> Path:
        """Export shortlisted candidate rows with explanation and confidence."""

        selected = set(shortlisted_ids)
        rows = [row for row in ranked if row.candidate_id in selected]

        output_path = Path(self._settings.dashboard.shortlist_output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with output_path.open("w", encoding="utf-8", newline="") as fp:
            writer = csv.writer(fp)
            writer.writerow(
                [
                    "candidate_id",
                    "rank",
                    "score",
                    "confidence",
                    "reasoning",
                ]
            )
            for row in rows:
                writer.writerow(
                    [
                        row.candidate_id,
                        row.rank,
                        f"{row.score:.6f}",
                        f"{row.evidence.confidence:.6f}",
                        row.reasoning,
                    ]
                )

        return output_path
