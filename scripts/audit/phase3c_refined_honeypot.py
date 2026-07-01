"""Phase 3c: Refined honeypot detection using duration_months per skill."""
import json
import csv
from pathlib import Path
from datetime import date

CANDIDATES_PATH = Path("India_runs_data_and_ai_challenge/candidates.jsonl")
SUBMISSION_PATH = Path("outputs/submission.csv")

print("Loading dataset...")
records_by_id = {}
with CANDIDATES_PATH.open("r", encoding="utf-8") as f:
    for line in f:
        r = json.loads(line.strip())
        records_by_id[r["candidate_id"]] = r
print(f"Loaded {len(records_by_id)} candidates.\n")

submission = []
with SUBMISSION_PATH.open("r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        submission.append(row)
top100_ids = {row["candidate_id"] for row in submission}

CURRENT_YEAR = 2025

# Approx year each major tech became widely available
TECH_MIN_YEAR = {
    "chatgpt": 2022, "gpt-4": 2023, "gpt4": 2023, "gpt-3": 2020, "gpt3": 2020,
    "langchain": 2022, "llama": 2023, "llama2": 2023, "llama-2": 2023,
    "mistral": 2023, "gemini": 2023, "claude": 2021,
    "pinecone": 2021, "weaviate": 2019, "chroma": 2022, "qdrant": 2020,
    "stable diffusion": 2022, "dall-e": 2021, "midjourney": 2022,
    "transformers": 2018, "bert": 2018, "gpt-2": 2019,
    "rag": 2020, "langchain": 2022, "llamaindex": 2022, "haystack": 2019,
    "autogpt": 2023, "crewai": 2024, "autogen": 2023,
    "kubernetes": 2014, "docker": 2013, "terraform": 2014,
    "react": 2013, "vue": 2014, "nextjs": 2016, "vite": 2020,
    "pytorch": 2016, "tensorflow": 2015, "jax": 2018,
    "fastapi": 2018, "pydantic": 2017,
    "grafana": 2014, "prometheus": 2012,
    "clickhouse": 2016, "dbt": 2016, "airflow": 2014,
    "snowflake": 2012, "databricks": 2013,
    "openai": 2015, "anthropic": 2021,
    "rust": 2010, "go": 2009, "kotlin": 2011,
    "cassandra": 2008, "mongodb": 2009, "redis": 2009,
    "spark": 2014, "kafka": 2011, "flink": 2014,
    "elastic": 2010, "elasticsearch": 2010,
}

honeypots = {}

for cid, r in records_by_id.items():
    profile = r.get("profile", {})
    skills = r.get("skills", [])
    education = r.get("education", [])
    career = r.get("career_history", [])
    signals = r.get("redrob_signals", {})

    reasons = []

    # ── A. Skill duration exceeds tech existence ───────────────────────────
    for skill in skills:
        skill_name = str(skill.get("name", "")).lower()
        dur_months = skill.get("duration_months", None)
        if dur_months is None:
            continue
        try:
            dur_months = float(dur_months)
        except (TypeError, ValueError):
            continue
        dur_years = dur_months / 12.0

        for tech, min_year in TECH_MIN_YEAR.items():
            if tech in skill_name:
                max_possible = CURRENT_YEAR - min_year
                if dur_years > max_possible + 0.5:
                    reasons.append(
                        f"Skill '{skill_name}': {dur_years:.1f}y "
                        f"but '{tech}' exists since {min_year} "
                        f"(max ~{max_possible:.1f}y)"
                    )
                break

    # ── B. YOE vs graduation year consistency ─────────────────────────────
    yoe = float(profile.get("years_of_experience", 0) or 0)
    for edu in education:
        end_year = edu.get("end_year")
        if end_year:
            try:
                end_year = int(end_year)
                max_possible_yoe = CURRENT_YEAR - end_year
                if yoe > max_possible_yoe + 2:  # +2 years buffer for rounding
                    reasons.append(
                        f"YOE {yoe:.1f} but graduated {end_year} "
                        f"(max ~{max_possible_yoe:.1f}y)"
                    )
            except (TypeError, ValueError):
                pass

    # ── C. Career history start before graduation ─────────────────────────
    grad_years = []
    for edu in education:
        ey = edu.get("end_year")
        if ey:
            try:
                grad_years.append(int(ey))
            except (TypeError, ValueError):
                pass
    if grad_years:
        earliest_grad = min(grad_years)
        for job in career:
            start = job.get("start_date", "")
            try:
                sy = int(str(start)[:4])
                if sy < earliest_grad - 1:  # allow 1 year buffer for internships
                    reasons.append(
                        f"Job started {sy} but earliest grad {earliest_grad} "
                        f"(career started before graduation)"
                    )
            except (TypeError, ValueError):
                pass

    # ── D. Notice period impossibly large ─────────────────────────────────
    notice = signals.get("notice_period_days", None)
    if notice is not None:
        try:
            notice = int(notice)
            if notice > 180:
                reasons.append(f"Notice period {notice}d > max 180d")
        except (TypeError, ValueError):
            pass

    # ── E. Salary impossibly high for India ───────────────────────────────
    salary = signals.get("expected_salary_range_inr_lpa", {})
    if salary:
        sal_max = salary.get("max", 0)
        try:
            sal_max = float(sal_max)
            if sal_max > 500:  # 500L/yr is extreme even for senior engineers
                reasons.append(f"Salary max {sal_max}L/yr seems impossible")
        except (TypeError, ValueError):
            pass

    if reasons:
        honeypots[cid] = reasons

print(f"REFINED HONEYPOT DETECTION")
print(f"=" * 60)
print(f"Total candidates with impossible signals : {len(honeypots)}")
by_type = {
    "skill_duration": sum(1 for r in honeypots.values() if any("Skill" in x for x in r)),
    "yoe_vs_grad": sum(1 for r in honeypots.values() if any("YOE" in x for x in r)),
    "career_before_grad": sum(1 for r in honeypots.values() if any("before grad" in x for x in r)),
    "notice_period": sum(1 for r in honeypots.values() if any("Notice" in x for x in r)),
    "salary": sum(1 for r in honeypots.values() if any("Salary" in x for x in r)),
}
for k, v in by_type.items():
    print(f"  {k:25s} : {v}")

in_top100 = {cid: reasons for cid, reasons in honeypots.items() if cid in top100_ids}
print(f"\nHoneypots in our top-100 submission : {len(in_top100)}")
if in_top100:
    print("\n  CRITICAL: Honeypots found in top-100!")
    for cid, reasons in sorted(in_top100.items()):
        rank = next((r["rank"] for r in submission if r["candidate_id"] == cid), "?")
        score = next((r["score"] for r in submission if r["candidate_id"] == cid), "?")
        print(f"\n  {cid}  rank={rank}  score={score}")
        for reason in reasons:
            print(f"    FLAG: {reason}")
else:
    print("  PASS: Zero honeypot/impossible-profile candidates in our top-100.\n")
    print("  Honeypot rate = 0/100 = 0.0%  (threshold for disqualification: >10/100 = 10%)")

# ── Show all detected impossible-profile candidates ──────────────────────
print(f"\nAll detected impossible-profile candidates (showing first 30):")
for cid, reasons in list(honeypots.items())[:30]:
    in_sub = " ** IN SUBMISSION **" if cid in top100_ids else ""
    print(f"  {cid}{in_sub}")
    for r in reasons[:3]:
        print(f"    {r}")

print(f"\n{'='*60}")
print(f"PHASE 3c COMPLETE")
print(f"\nSpec says ~80 honeypots exist.")
print(f"We detected {len(honeypots)} candidates with at least one impossible signal.")
print(f"Note: The ~7,496 future-date records (last_active in 2025-2026) are likely")
print(f"synthetic data artifacts, not honeypots per se.")
