"""Phase 3: Dataset integrity audit — statistics, duplicates, anomalies."""
import json
import re
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

CANDIDATES_PATH = Path("India_runs_data_and_ai_challenge/candidates.jsonl")
SAMPLE_LIMIT = None  # full scan

print("PHASE 3 — DATASET INTEGRITY AUDIT")
print("=" * 60)

records = []
parse_errors = 0

with CANDIDATES_PATH.open("r", encoding="utf-8") as f:
    for i, line in enumerate(f):
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            parse_errors += 1

total = len(records)
print(f"Total records loaded : {total}")
print(f"JSON parse errors    : {parse_errors}")

# ── 1. Basic schema keys ────────────────────────────────────────────────────
top_keys = Counter()
for r in records:
    for k in r.keys():
        top_keys[k] += 1
print(f"\n1. Top-level keys present in >80% of records:")
for k, cnt in top_keys.most_common():
    pct = cnt / total * 100
    if pct >= 80:
        print(f"   {k:40s} {cnt:6d}  ({pct:.1f}%)")

# ── 2. Candidate ID format & uniqueness ───────────────────────────────────
ID_PATTERN = re.compile(r"^CAND_\d{7}$")
cand_ids = []
malformed_ids = []
for r in records:
    cid = r.get("candidate_id", "")
    cand_ids.append(cid)
    if not ID_PATTERN.match(str(cid)):
        malformed_ids.append(cid)

id_counter = Counter(cand_ids)
exact_dup_ids = {cid: cnt for cid, cnt in id_counter.items() if cnt > 1}
print(f"\n2. Candidate ID checks:")
print(f"   Unique IDs           : {len(id_counter)}")
print(f"   Duplicate IDs        : {len(exact_dup_ids)}")
if exact_dup_ids:
    for cid, cnt in list(exact_dup_ids.items())[:10]:
        print(f"     {cid} appears {cnt}x")
print(f"   Malformed IDs        : {len(malformed_ids)}")
if malformed_ids[:5]:
    print(f"     samples: {malformed_ids[:5]}")

# Check for sequential IDs (sentinel pattern)
numeric_ids = []
for cid in cand_ids:
    m = re.match(r"^CAND_(\d{7})$", cid)
    if m:
        numeric_ids.append(int(m.group(1)))
numeric_ids.sort()
gaps = [numeric_ids[i+1] - numeric_ids[i] for i in range(len(numeric_ids)-1)]
if gaps:
    print(f"   ID numeric range     : {numeric_ids[0]} – {numeric_ids[-1]}")
    print(f"   Max gap              : {max(gaps)}")
    print(f"   Min gap              : {min(gaps)}")

# ── 3. Experience value distribution ──────────────────────────────────────
yoe_values = []
impossible_yoe = []
for r in records:
    profile = r.get("profile", {})
    yoe = profile.get("years_of_experience", None)
    if yoe is not None:
        try:
            yoe = float(yoe)
            yoe_values.append(yoe)
            if yoe < 0 or yoe > 60:
                impossible_yoe.append((r.get("candidate_id"), yoe))
        except (TypeError, ValueError):
            impossible_yoe.append((r.get("candidate_id"), yoe))

if yoe_values:
    yoe_values.sort()
    print(f"\n3. Experience (years_of_experience):")
    print(f"   Count       : {len(yoe_values)}")
    print(f"   Min         : {min(yoe_values)}")
    print(f"   Max         : {max(yoe_values)}")
    print(f"   Mean        : {sum(yoe_values)/len(yoe_values):.2f}")
    print(f"   P50         : {yoe_values[len(yoe_values)//2]:.2f}")
    print(f"   Impossible  : {len(impossible_yoe)}")
    if impossible_yoe[:5]:
        print(f"   Samples     : {impossible_yoe[:5]}")

# ── 4. Empty / sparse candidates ──────────────────────────────────────────
empty_skills = 0
empty_career = 0
empty_education = 0
no_summary = 0
no_signals = 0
completely_empty = 0

for r in records:
    profile = r.get("profile", {})
    skills_empty = len(r.get("skills", [])) == 0
    career_empty = len(r.get("career_history", [])) == 0
    edu_empty = len(r.get("education", [])) == 0
    summary_empty = not str(profile.get("summary", "")).strip()
    sig_empty = r.get("redrob_signals") is None

    if skills_empty:
        empty_skills += 1
    if career_empty:
        empty_career += 1
    if edu_empty:
        empty_education += 1
    if summary_empty:
        no_summary += 1
    if sig_empty:
        no_signals += 1
    if skills_empty and career_empty and summary_empty:
        completely_empty += 1

print(f"\n4. Sparse / empty records:")
print(f"   No skills            : {empty_skills:6d} ({empty_skills/total*100:.1f}%)")
print(f"   No career history    : {empty_career:6d} ({empty_career/total*100:.1f}%)")
print(f"   No education         : {empty_education:6d} ({empty_education/total*100:.1f}%)")
print(f"   No summary           : {no_summary:6d} ({no_summary/total*100:.1f}%)")
print(f"   No redrob signals    : {no_signals:6d} ({no_signals/total*100:.1f}%)")
print(f"   Completely empty     : {completely_empty:6d} ({completely_empty/total*100:.1f}%)")

# ── 5. Placeholder / synthetic names ──────────────────────────────────────
PLACEHOLDER_PATTERNS = [
    r"^test\s", r"^dummy", r"^fake", r"^placeholder",
    r"candidate\s*\d+", r"^user\s*\d+", r"^person\s*\d+",
    r"^john doe$", r"^jane doe$", r"^xxx+$", r"^n/?a$",
    r"^anon", r"^sample\s",
]
placeholder_names = []
for r in records:
    name = str(r.get("profile", {}).get("anonymized_name", "")).strip().lower()
    for pat in PLACEHOLDER_PATTERNS:
        if re.search(pat, name, re.IGNORECASE):
            placeholder_names.append((r.get("candidate_id"), name))
            break

print(f"\n5. Placeholder / synthetic names:")
print(f"   Matches              : {len(placeholder_names)}")
if placeholder_names[:5]:
    for cid, name in placeholder_names[:5]:
        print(f"     {cid}: {name}")

# ── 6. Duplicate profile fingerprints (near-dupes) ────────────────────────
fingerprints = Counter()
for r in records:
    profile = r.get("profile", {})
    skills = tuple(sorted(s.get("name", "") for s in r.get("skills", [])))
    fp = (
        str(profile.get("current_title", "")).lower().strip(),
        str(profile.get("location", "")).lower().strip(),
        round(float(profile.get("years_of_experience", 0) or 0)),
        skills[:5],
    )
    fingerprints[fp] += 1

exact_dup_profiles = {fp: cnt for fp, cnt in fingerprints.items() if cnt > 1}
high_dup_profiles = {fp: cnt for fp, cnt in exact_dup_profiles.items() if cnt >= 5}
print(f"\n6. Near-duplicate profile fingerprints (title+location+yoe+top5skills):")
print(f"   Unique fingerprints  : {len(fingerprints)}")
print(f"   Duplicated FPs (>=2) : {len(exact_dup_profiles)}")
print(f"   High-dup FPs (>=5)   : {len(high_dup_profiles)}")
if high_dup_profiles:
    for fp, cnt in sorted(high_dup_profiles.items(), key=lambda x: -x[1])[:5]:
        print(f"     count={cnt}  title={fp[0]}  loc={fp[1]}  yoe={fp[2]}  skills={fp[3]}")

# ── 7. Extra / unexpected columns ────────────────────────────────────────
all_keys = set()
for r in records:
    all_keys.update(r.keys())
print(f"\n7. All top-level keys across dataset:")
for k in sorted(all_keys):
    cnt = sum(1 for r in records if k in r)
    print(f"   {k:40s} present in {cnt:6d} / {total} records")

# ── 8. Impossible dates check ─────────────────────────────────────────────
print(f"\n8. Impossible date checks (redrob_signals):")
impossible_dates = 0
for r in records:
    sig = r.get("redrob_signals")
    if not sig:
        continue
    signup = sig.get("signup_date")
    last_active = sig.get("last_active_date")
    if signup and last_active:
        try:
            sd = date.fromisoformat(str(signup))
            la = date.fromisoformat(str(last_active))
            if la < sd:
                impossible_dates += 1
        except ValueError:
            pass
print(f"   last_active < signup : {impossible_dates}")

# ── 9. Profile completeness score distribution ────────────────────────────
completeness_scores = []
for r in records:
    sig = r.get("redrob_signals")
    if sig:
        v = sig.get("profile_completeness_score")
        if v is not None:
            try:
                completeness_scores.append(float(v))
            except (TypeError, ValueError):
                pass
if completeness_scores:
    completeness_scores.sort()
    n = len(completeness_scores)
    buckets = Counter()
    for v in completeness_scores:
        if v == 100:
            buckets["=100"] += 1
        elif v >= 90:
            buckets["90-99"] += 1
        elif v >= 70:
            buckets["70-89"] += 1
        elif v >= 50:
            buckets["50-69"] += 1
        else:
            buckets["<50"] += 1
    print(f"\n9. Profile completeness score distribution ({n} records):")
    for label in ["=100", "90-99", "70-89", "50-69", "<50"]:
        print(f"   {label:8s} : {buckets[label]:6d}")

# ── 10. open_to_work_flag distribution ───────────────────────────────────
otw = Counter()
for r in records:
    sig = r.get("redrob_signals")
    if sig:
        otw[sig.get("open_to_work_flag")] += 1
print(f"\n10. open_to_work_flag distribution:")
for k, cnt in sorted(otw.items(), key=lambda x: str(x[0])):
    print(f"   {str(k):10s} : {cnt:6d} ({cnt/total*100:.1f}%)")

print(f"\n{'='*60}")
print("PHASE 3 COMPLETE")
