"""Phase 3b+4b: Identify honeypot candidates and check if any are in our top-100."""
import json
import csv
from pathlib import Path
from datetime import date

CANDIDATES_PATH = Path("India_runs_data_and_ai_challenge/candidates.jsonl")
SUBMISSION_PATH = Path("outputs/submission.csv")

# ── Load dataset ────────────────────────────────────────────────────────────
print("Loading dataset...")
records_by_id = {}
with CANDIDATES_PATH.open("r", encoding="utf-8") as f:
    for line in f:
        r = json.loads(line.strip())
        records_by_id[r["candidate_id"]] = r
print(f"Loaded {len(records_by_id)} candidates.\n")

# ── Load submission ─────────────────────────────────────────────────────────
submission = []
with SUBMISSION_PATH.open("r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        submission.append(row)
top100_ids = {row["candidate_id"] for row in submission}
print(f"Top-100 IDs loaded from submission ({len(top100_ids)} entries).\n")

# ── Honeypot detection patterns ──────────────────────────────────────────────
# Per spec: "subtly impossible profiles, e.g. 8 years of experience in a technology
# that only existed for 5 years"
# Detection heuristics:
#  A. last_active_date < signup_date (impossible)
#  B. YOE exceeds plausible range given graduation year
#  C. Known "too-new" tech skills with claimed experience predating them

# Approximate founding years for common modern AI/ML technologies
TECH_MIN_YEAR = {
    "chatgpt": 2022, "gpt-4": 2023, "gpt4": 2023,
    "langchain": 2022, "llama": 2023, "llama2": 2023, "llama-2": 2023,
    "mistral": 2023, "gemini": 2023, "claude": 2021,
    "pinecone": 2021, "weaviate": 2019, "chroma": 2022,
    "llm": 2018,  # large-scale LLM era
    "stable diffusion": 2022, "dall-e": 2021,
    "transformers": 2018, "bert": 2018,
    "kubernetes": 2014, "docker": 2013, "terraform": 2014,
    "react": 2013, "vue": 2014, "nextjs": 2016,
    "pytorch": 2016, "tensorflow": 2015,
    "fastapi": 2018, "pydantic": 2017,
    "grafana": 2014, "prometheus": 2012,
    "clickhouse": 2016, "dbt": 2016, "airflow": 2014,
    "snowflake": 2012, "databricks": 2013,
    "openai": 2015, "anthropic": 2021,
}

CURRENT_YEAR = 2025

honeypots_found = {}

for cid, r in records_by_id.items():
    signals = r.get("redrob_signals", {})
    profile = r.get("profile", {})
    skills = r.get("skills", [])

    reasons = []

    # A. Impossible dates: last_active < signup
    try:
        signup = date.fromisoformat(str(signals.get("signup_date", "")))
        last_active = date.fromisoformat(str(signals.get("last_active_date", "")))
        if last_active < signup:
            reasons.append(f"last_active ({last_active}) < signup ({signup})")
    except (ValueError, TypeError):
        pass

    # B. Skills that are too new vs claimed experience
    yoe = float(profile.get("years_of_experience", 0) or 0)
    career_start_year_est = CURRENT_YEAR - yoe

    for skill in skills:
        skill_name = skill.get("name", "").lower()
        years_skill = skill.get("years_of_experience", None)
        if years_skill is None:
            continue
        try:
            years_skill = float(years_skill)
        except (TypeError, ValueError):
            continue

        for tech, min_year in TECH_MIN_YEAR.items():
            if tech in skill_name:
                # How many years could they plausibly have with this tech?
                max_plausible_years = CURRENT_YEAR - min_year
                if years_skill > max_plausible_years + 0.5:  # allow 6-month buffer
                    reasons.append(
                        f"Skill '{skill_name}' claims {years_skill:.1f}y "
                        f"but {tech} only existed since {min_year} "
                        f"(max {max_plausible_years:.1f}y possible)"
                    )
                break

    if reasons:
        honeypots_found[cid] = reasons

print(f"HONEYPOT DETECTION RESULTS")
print(f"=" * 60)
print(f"Total honeypot candidates detected : {len(honeypots_found)}")
print(f"  - By impossible date              : {sum(1 for r in honeypots_found.values() if any('last_active' in x for x in r))}")
print(f"  - By impossible skill timeline    : {sum(1 for r in honeypots_found.values() if any('claims' in x for x in r))}")

# ── Cross-check with our submission ─────────────────────────────────────────
in_top100 = {cid: reasons for cid, reasons in honeypots_found.items() if cid in top100_ids}
print(f"\n  Honeypots in our top-100         : {len(in_top100)}")

if in_top100:
    print("\n  DETAILS OF HONEYPOTS IN TOP-100:")
    for cid, reasons in sorted(in_top100.items()):
        # Find rank
        rank = next((r["rank"] for r in submission if r["candidate_id"] == cid), "?")
        score = next((r["score"] for r in submission if r["candidate_id"] == cid), "?")
        print(f"    {cid}  rank={rank}  score={score}")
        for reason in reasons:
            print(f"      ISSUE: {reason}")
else:
    print("  CLEAN: None of our top-100 candidates are detected honeypots.")

# ── Show sample of detected honeypots ────────────────────────────────────────
print(f"\n  Sample of ALL detected honeypots (first 15):")
for cid, reasons in list(honeypots_found.items())[:15]:
    in_sub = " [IN SUBMISSION]" if cid in top100_ids else ""
    print(f"  {cid}{in_sub}")
    for reason in reasons[:2]:
        print(f"    {reason}")

# ── Impossible-date-only breakdown ─────────────────────────────────────────
date_only_hps = {cid: r for cid, r in honeypots_found.items() 
                 if all('last_active' in x for x in r)}
skill_hps = {cid: r for cid, r in honeypots_found.items() 
             if any('claims' in x for x in r)}
print(f"\n  Impossible-date-only honeypots    : {len(date_only_hps)}")
print(f"  Skill-timeline honeypots          : {len(skill_hps)}")
print(f"  Skill-timeline in top-100         : {sum(1 for cid in skill_hps if cid in top100_ids)}")
print(f"\n  Spec says ~80 honeypots exist.")
print(f"  Skill-timeline detection found {len(skill_hps)} candidates with impossible skill timelines.")
print(f"  Date inconsistencies ({len(date_only_hps)}) may be a data quality artifact, not honeypots.")

print(f"\n{'='*60}")
print("PHASE 3b COMPLETE")
