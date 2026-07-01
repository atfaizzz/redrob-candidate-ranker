"""Phase 3c fast: Honeypot detection with file output."""
import json
import csv
import sys
from pathlib import Path
from datetime import date

out = open("scripts/audit/phase3c_output.txt", "w", encoding="utf-8")

def log(msg=""):
    print(msg)
    out.write(msg + "\n")
    out.flush()

CANDIDATES_PATH = Path("India_runs_data_and_ai_challenge/candidates.jsonl")
SUBMISSION_PATH = Path("outputs/submission.csv")
CURRENT_YEAR = 2025

TECH_MIN_YEAR = {
    "chatgpt": 2022, "gpt-4": 2023, "gpt4": 2023, "gpt-3": 2020,
    "langchain": 2022, "llama": 2023, "llama2": 2023,
    "mistral": 2023, "gemini": 2023, "claude": 2021,
    "pinecone": 2021, "weaviate": 2019, "chroma": 2022,
    "stable diffusion": 2022, "dall-e": 2021,
    "transformers": 2018, "bert": 2018,
    "pytorch": 2016, "tensorflow": 2015,
    "fastapi": 2018, "pydantic": 2017,
    "clickhouse": 2016, "dbt": 2016, "airflow": 2014,
    "kubernetes": 2014, "docker": 2013, "terraform": 2014,
    "react": 2013, "vue": 2014, "nextjs": 2016,
    "snowflake": 2012, "databricks": 2013,
}

log("Loading dataset...")
records_by_id = {}
with CANDIDATES_PATH.open("r", encoding="utf-8") as f:
    for line in f:
        r = json.loads(line.strip())
        records_by_id[r["candidate_id"]] = r
log(f"Loaded {len(records_by_id)} candidates.")

submission = []
with SUBMISSION_PATH.open("r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        submission.append(row)
top100_ids = {row["candidate_id"] for row in submission}
log(f"Submission has {len(top100_ids)} candidates.\n")

honeypots = {}

log("Scanning for impossible profiles...")
for i, (cid, r) in enumerate(records_by_id.items()):
    if i % 20000 == 0:
        log(f"  Progress: {i}/100000...")
    profile = r.get("profile", {})
    skills = r.get("skills", [])
    education = r.get("education", [])
    career = r.get("career_history", [])
    signals = r.get("redrob_signals", {})
    reasons = []

    # A. Skill duration vs tech age
    for skill in skills:
        sname = str(skill.get("name", "")).lower()
        dm = skill.get("duration_months")
        if dm is None:
            continue
        try:
            dm = float(dm)
        except (TypeError, ValueError):
            continue
        dur_yrs = dm / 12.0
        for tech, min_yr in TECH_MIN_YEAR.items():
            if tech in sname:
                max_poss = CURRENT_YEAR - min_yr
                if dur_yrs > max_poss + 0.5:
                    reasons.append(f"Skill '{sname}': {dur_yrs:.1f}y claimed, tech exists since {min_yr} (max {max_poss:.0f}y)")
                break

    # B. YOE vs graduation year
    yoe = float(profile.get("years_of_experience", 0) or 0)
    for edu in education:
        ey = edu.get("end_year")
        if ey:
            try:
                ey = int(ey)
                max_yoe = CURRENT_YEAR - ey
                if yoe > max_yoe + 2:
                    reasons.append(f"YOE {yoe:.1f}y but grad {ey} => max {max_yoe:.0f}y possible")
            except (TypeError, ValueError):
                pass

    # C. Notice period > 180d
    notice = signals.get("notice_period_days")
    if notice is not None:
        try:
            if int(notice) > 180:
                reasons.append(f"Notice period {notice}d > 180d max")
        except (TypeError, ValueError):
            pass

    if reasons:
        honeypots[cid] = reasons

log(f"\nScan complete.")
log(f"\nREFINED HONEYPOT DETECTION RESULTS")
log(f"=" * 60)
log(f"Total impossible-profile candidates : {len(honeypots)}")
log(f"  skill_duration_impossible : {sum(1 for r in honeypots.values() if any('Skill' in x for x in r))}")
log(f"  yoe_vs_graduation         : {sum(1 for r in honeypots.values() if any('YOE' in x for x in r))}")
log(f"  notice_period_over_180    : {sum(1 for r in honeypots.values() if any('Notice' in x for x in r))}")

in_top100 = {cid: reasons for cid, reasons in honeypots.items() if cid in top100_ids}
log(f"\nHoneypot candidates in our top-100  : {len(in_top100)}")
if in_top100:
    log("\n  *** CRITICAL: Impossible-profile candidates in top-100! ***")
    for cid, reasons in sorted(in_top100.items()):
        rank = next((r["rank"] for r in submission if r["candidate_id"] == cid), "?")
        score = next((r["score"] for r in submission if r["candidate_id"] == cid), "?")
        log(f"\n  {cid}  rank={rank}  score={score}")
        for reason in reasons:
            log(f"    FLAG: {reason}")
else:
    log(f"\n  PASS: Zero impossible-profile candidates in our top-100.")
    log(f"  Honeypot rate = 0% (disqualification threshold: >10%)")

log(f"\nSample of ALL detected candidates (first 20):")
for cid, reasons in list(honeypots.items())[:20]:
    flag = " [IN TOP-100]" if cid in top100_ids else ""
    log(f"  {cid}{flag}")
    for r in reasons[:2]:
        log(f"    {r}")

log(f"\n{'='*60}")
log("PHASE 3c COMPLETE")
out.close()
