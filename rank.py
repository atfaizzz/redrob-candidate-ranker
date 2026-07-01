#!/usr/bin/env python3
"""
Production CLI entrypoint for generating competition submission.

Usage:
    python rank.py
    python rank.py --config configs/base.yaml
    python rank.py --candidates ./candidates.jsonl --out ./submission.csv
    python rank.py --config configs/base.yaml --candidates ./data/candidates.jsonl --out ./out/sub.csv
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Redrob AI Recruiter — produce challenge-compliant submission CSV",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--config",
        default="configs/base.yaml",
        help="Path to YAML/JSON config file",
    )
    parser.add_argument(
        "--candidates",
        default=None,
        help="Override candidates.jsonl path (overrides config)",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Override submission CSV output path (overrides config)",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=None,
        help="Override number of ranked candidates to emit (must be >= 100 for valid submission)",
    )
    parser.add_argument(
        "--no-preflight",
        action="store_true",
        help="Skip repository preflight health checks (not recommended)",
    )
    return parser


def main() -> int:
    parser = _build_arg_parser()
    args = parser.parse_args()

    # ── Lazy imports so arg-parse errors surface quickly ──────────────────────
    from src.config.settings import load_config, parse_app_settings
    from src.pipelines.ranking_pipeline import RankingPipeline
    from src.qa.preflight import RepositoryHealthChecker
    from src.submission.writer import SubmissionWriter

    # ── Load and patch config ─────────────────────────────────────────────────
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"[rank.py] ERROR: config not found: {config_path}", file=sys.stderr)
        return 1

    raw_config = load_config(config_path)

    if args.candidates:
        raw_config.setdefault("paths", {})["candidates_path"] = args.candidates

    if args.out:
        raw_config.setdefault("paths", {})["submission_output_path"] = args.out

    if args.top_n is not None:
        raw_config.setdefault("runtime", {})["top_n"] = args.top_n

    settings = parse_app_settings(raw_config)

    # ── Preflight ─────────────────────────────────────────────────────────────
    if not args.no_preflight:
        checker = RepositoryHealthChecker()
        result = checker.run(settings)
        if result.warnings:
            for w in result.warnings:
                print(f"[rank.py] WARNING: {w}", file=sys.stderr)
        if not result.ok:
            for e in result.errors:
                print(f"[rank.py] ERROR: {e}", file=sys.stderr)
            return 1

    top_n = settings.runtime.top_n
    if top_n < 100:
        print(
            f"[rank.py] ERROR: top_n={top_n} is below 100; "
            "competition requires exactly 100 ranked rows.",
            file=sys.stderr,
        )
        return 1

    # ── Run pipeline ──────────────────────────────────────────────────────────
    print(f"[rank.py] Starting ranking pipeline (top_n={top_n}) …")
    t0 = time.perf_counter()

    pipeline = RankingPipeline(settings)
    ranked, summary = pipeline.execute()

    elapsed = time.perf_counter() - t0
    print(
        f"[rank.py] Pipeline complete in {elapsed:.1f}s — "
        f"scanned={summary.scanned_candidates} "
        f"parsed={summary.parsed_candidates} "
        f"ranked={summary.ranked_candidates}"
    )

    # ── Write submission ──────────────────────────────────────────────────────
    output_path = Path(settings.runtime.submission_output_path)
    writer = SubmissionWriter()
    try:
        writer.write(ranked, output_path)
    except ValueError as exc:
        print(f"[rank.py] ERROR: Submission validation failed: {exc}", file=sys.stderr)
        return 1

    print(f"[rank.py] Submission written to: {output_path}")
    print(f"[rank.py] Rows written: 100 (ranks 1–100)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
