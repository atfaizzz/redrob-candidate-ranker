"""Competition-compliant submission CSV writer."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Sequence

from src.contracts.domain import RankedCandidate

REQUIRED_HEADER = ["candidate_id", "rank", "score", "reasoning"]
EXPECTED_ROWS = 100


class SubmissionWriter:
    """Writes a challenge-compliant ranked CSV from a list of RankedCandidates.

    Rules enforced:
    - Header: candidate_id, rank, score, reasoning
    - Exactly 100 data rows (ranks 1–100)
    - Unique candidate_ids and unique ranks
    - Score non-increasing by rank
    - Tie-break: equal scores → candidate_id ascending (already guaranteed by ranker sort)
    """

    def write(self, ranked: Sequence[RankedCandidate], output_csv: Path) -> None:
        """Persist competition-compliant CSV.

        Args:
            ranked: Ranked candidates ordered by rank (length must be >= EXPECTED_ROWS).
            output_csv: Destination path. Parent directory is created if needed.

        Raises:
            ValueError: If the output does not satisfy competition rules.
        """
        top100 = list(ranked[:EXPECTED_ROWS])

        if len(top100) < EXPECTED_ROWS:
            raise ValueError(
                f"SubmissionWriter requires at least {EXPECTED_ROWS} ranked candidates; "
                f"got {len(top100)}. Increase runtime.top_n to at least {EXPECTED_ROWS}."
            )

        self._validate(top100)

        output_csv.parent.mkdir(parents=True, exist_ok=True)

        with output_csv.open("w", encoding="utf-8", newline="") as fp:
            writer = csv.writer(fp)
            writer.writerow(REQUIRED_HEADER)
            for i, row in enumerate(top100, start=1):
                writer.writerow(
                    [
                        row.candidate_id,
                        str(i),
                        f"{row.score:.6f}",
                        row.reasoning,
                    ]
                )

    @staticmethod
    def _validate(top100: list[RankedCandidate]) -> None:
        """Raise ValueError for any submission-rule violation."""
        seen_ids: set[str] = set()
        prev_score: float | None = None

        for i, row in enumerate(top100, start=1):
            if row.candidate_id in seen_ids:
                raise ValueError(f"Duplicate candidate_id at rank {i}: {row.candidate_id}")
            seen_ids.add(row.candidate_id)

            if prev_score is not None and row.score > prev_score:
                raise ValueError(
                    f"Score not non-increasing: rank {i-1} score={prev_score:.6f} < "
                    f"rank {i} score={row.score:.6f}"
                )
            prev_score = row.score
