"""Phase 2: Repository code audit — search for hardcoded IDs, filters, leakage."""
import ast
import re
from pathlib import Path

ROOT = Path(".")
SEARCH_DIRS = ["src", "configs", "tests", "docs", "experiments"]

SUSPICIOUS_PATTERNS = [
    (r"CAND_\d{7}", "hardcoded candidate ID"),
    (r"blacklist|whitelist|blocklist|allowlist", "ID filter list"),
    (r"row_order|row_index|iloc\[|\.index\b", "row-order assumption"),
    (r"submission\.csv|sample_submission", "submission file reference in code"),
    (r"label|target|ground_truth|relevance_score", "potential target leakage column"),
    (r"eval_only|evaluation_only|held_out|holdout", "eval-only references"),
    (r"sentinel|watermark|honeypot|trap_id", "honeypot/sentinel reference"),
    (r"cache.*label|label.*cache", "cached label leakage"),
    (r"rank\s*=\s*\d+\b", "hardcoded rank assignment"),
    (r"score\s*=\s*[01]\.\d{3}", "hardcoded score"),
    (r"candidate_id.*==|==.*candidate_id", "hardcoded ID comparison"),
]

findings = []

for search_dir in SEARCH_DIRS:
    base = ROOT / search_dir
    if not base.exists():
        continue
    for path in base.rglob("*.py"):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        for pattern, label in SUSPICIOUS_PATTERNS:
            for m in re.finditer(pattern, text, re.IGNORECASE):
                lineno = text[:m.start()].count("\n") + 1
                line = text.splitlines()[lineno - 1].strip()
                findings.append({
                    "file": str(path),
                    "line": lineno,
                    "pattern": label,
                    "match": m.group(),
                    "context": line[:120],
                })

# Also scan yaml/json configs
for search_dir in ["configs"]:
    base = ROOT / search_dir
    if not base.exists():
        continue
    for path in base.rglob("*"):
        if path.suffix not in {".yaml", ".yml", ".json"}:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        for pattern, label in SUSPICIOUS_PATTERNS:
            for m in re.finditer(pattern, text, re.IGNORECASE):
                lineno = text[:m.start()].count("\n") + 1
                line = text.splitlines()[lineno - 1].strip()
                findings.append({
                    "file": str(path),
                    "line": lineno,
                    "pattern": label,
                    "match": m.group(),
                    "context": line[:120],
                })

print(f"\nPHASE 2 — REPOSITORY AUDIT")
print(f"{'='*60}")
print(f"Directories scanned: {SEARCH_DIRS}")
print(f"Total suspicious pattern matches: {len(findings)}\n")

if not findings:
    print("  No suspicious patterns found.")
else:
    by_pattern = {}
    for f in findings:
        by_pattern.setdefault(f["pattern"], []).append(f)
    for label, items in sorted(by_pattern.items()):
        print(f"\n  [{label}] — {len(items)} occurrence(s):")
        for item in items:
            print(f"    {item['file']}:{item['line']}  match={item['match']!r}")
            print(f"      context: {item['context']}")
