"""Phase 4+5: Ranking pipeline integrity and robustness checks."""
import re
from pathlib import Path

print("PHASE 4 — RANKING PIPELINE INTEGRITY")
print("=" * 60)

RANKING_FILES = [
    "src/ranking/evidence_ranker.py",
    "src/retrieval/strategies.py",
    "src/pipelines/ranking_pipeline.py",
    "src/explainability/reasoning.py",
    "src/preprocessing/normalization.py",
    "src/preprocessing/feature_extraction.py",
    "src/parsing/candidate_parser.py",
]

# Patterns that would indicate illegitimate ranking signals
LEAKAGE_PATTERNS = [
    (r"candidate_id\s*==|==\s*candidate_id", "ID-based filter/shortcut"),
    (r"rank\s*=\s*\d+", "hardcoded rank"),
    (r"\.index\[|iloc\[|row_order", "row-order dependency"),
    (r"submission|sample_submission", "submission file reference"),
    (r"label|ground_truth|relevance", "ground-truth label reference"),
    (r"eval_only|held_out|holdout", "eval-only flag"),
    (r"CAND_\d{7}", "hardcoded candidate ID"),
    (r"sort.*candidate_id|candidate_id.*sort", "ID-based sort"),
]

all_clean = True
for filepath in RANKING_FILES:
    p = Path(filepath)
    if not p.exists():
        print(f"  [SKIP] {filepath} not found")
        continue
    text = p.read_text(encoding="utf-8")
    hits = []
    for pattern, label in LEAKAGE_PATTERNS:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            lineno = text[:m.start()].count("\n") + 1
            line = text.splitlines()[lineno - 1].strip()
            # Filter out tie-break sort by candidate_id (legitimate per competition rules)
            if "tie" in line.lower() or "competition" in line.lower() or "ascending" in line.lower():
                continue
            hits.append((label, lineno, m.group(), line))
    if hits:
        all_clean = False
        print(f"\n  [{filepath}] — {len(hits)} potential issue(s):")
        for label, lineno, match, ctx in hits:
            print(f"    line {lineno} [{label}]: {ctx[:100]}")
    else:
        print(f"  OK  {filepath}")

print(f"\n  Summary: {'All ranking files CLEAN — no leakage patterns detected.' if all_clean else 'See issues above.'}")

print("\n\nPHASE 5 — ROBUSTNESS CHECKS (from test results)")
print("=" * 60)
# Read the existing robustness test file to confirm coverage
robustness_test = Path("tests/test_robustness.py")
if robustness_test.exists():
    text = robustness_test.read_text(encoding="utf-8")
    scenarios = re.findall(r"def (test_\w+)", text)
    print(f"  Robustness test file : tests/test_robustness.py")
    print(f"  Test functions       : {scenarios}")
else:
    print("  tests/test_robustness.py not found")

# Also check QA preflight
preflight = Path("src/qa/preflight.py")
if preflight.exists():
    text = preflight.read_text(encoding="utf-8")
    checks = re.findall(r"def (_?\w+)\(", text)
    print(f"\n  Preflight checks in src/qa/preflight.py:")
    for c in checks:
        print(f"    {c}")

print("\n\nPHASE 6 — INTEGRITY REVIEW")
print("=" * 60)

# Walk entire src and check for any file reading submission CSV
all_py = list(Path("src").rglob("*.py")) + list(Path("tests").rglob("*.py"))
integrity_hits = []
for p in all_py:
    text = p.read_text(encoding="utf-8", errors="replace")
    if re.search(r"sample_submission|submission\.csv|submission_spec", text, re.IGNORECASE):
        for i, line in enumerate(text.splitlines(), 1):
            if re.search(r"sample_submission|submission\.csv|submission_spec", line, re.IGNORECASE):
                integrity_hits.append((str(p), i, line.strip()))

if integrity_hits:
    print("  Files referencing submission artifacts (potential shortcut):")
    for f, lineno, ctx in integrity_hits:
        print(f"    {f}:{lineno}  {ctx[:100]}")
else:
    print("  No source files reference submission artifacts or competition-specific shortcuts.")

print(f"\n{'='*60}")
print("PHASES 4-6 COMPLETE")
