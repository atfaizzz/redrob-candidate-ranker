# Honeypot & Competition Integrity Audit Report

**Project:** India Runs — Redrob Hackathon Candidate Ranking  
**Audit Completed:** 2025-07-07  
**Auditor:** Automated 8-Phase Audit (GitHub Copilot Agent)  
**Status:** ⚠️ FINDINGS DETECTED — Action Required Before Re-submission

---

## Executive Summary

This report documents the results of a formal 8-phase competition integrity and honeypot audit conducted on the India Runs candidate ranking system and its final submission (`outputs/submission.csv`).

**Key Findings:**
- The competition planted **~80 honeypot candidates** with subtly impossible profiles (per `submission_spec.docx` §7).
- Our ranking pipeline has no profile-plausibility guard, causing it to **over-represent candidates with impossible signals** in the top-100.
- **52 of our top-100 ranked candidates** have at least one detectable impossible signal — primarily skill-duration claims that exceed the technology's existence window.
- The competition disqualification threshold is **honeypot rate > 10 in top-100**. If even 11 of those 52 are actual competition honeypots, the submission is disqualified.
- The **core vulnerability**: our `EvidenceRanker` rewards claimed skill duration (via experience scoring) without validating whether those claims are temporally plausible. Honeypot profiles exploit this by claiming 7+ years of experience in 2–3 year-old technologies.

---

## Phase 1 — Competition Document Review

**Files inspected:**
- `India_runs_data_and_ai_challenge/README.docx`
- `India_runs_data_and_ai_challenge/submission_spec.docx`
- `India_runs_data_and_ai_challenge/redrob_signals_doc.docx`

### Honeypot Definition (per competition spec)

From `submission_spec.docx` §7 (Honeypot Warning):

> *"The dataset contains a small number (~80) of honeypot candidates with subtly impossible profiles (e.g., 8 years of experience in a technology that only existed for 5 years). If your submission ranks honeypots in the top 10, this is a strong signal that your system isn't reading profiles — it's ranking on platform signals, row order, or some other shortcut. If your submission ranks honeypots in the top 10, this is a strong signal that your system isn't reading profiles."*

> *"You can identify honeypots through careful profile inspection. We expect a good ranking system to naturally avoid them."*

**Evaluation trigger:** From §5 (Stage 3): *"Cannot reproduce within compute limits; honeypot rate >10% in top 100; missing or fabricated code repo"* → disqualification.

**Conclusion of Phase 1:** Honeypots are real, formally documented, and enforced at Stage 3 evaluation. The check is: how many of our top-100 are official competition honeypots? Threshold = ≤10 (10%).

---

## Phase 2 — Repository Code Audit

**Directories scanned:** `src/`, `configs/`, `tests/`, `docs/`, `experiments/`  
**Patterns checked:** hardcoded IDs, blacklists, row-order assumptions, submission file leakage, ground-truth label usage, eval-only flags.

### Findings

| Category | Count | Verdict |
|---|---|---|
| Hardcoded candidate IDs (`CAND_0000001..3`) | 10 | ✅ Test fixtures only — not in ranking path |
| `rank=0` in `evidence_ranker.py:68` | 1 | ✅ Temporary placeholder overwritten at line 83–91 |
| ID-based sort (`candidate_id` tie-break) | 1 | ✅ Competition-required tie-break (§3: "break score ties deterministically using candidate_id ascending") |
| `_confidence_label()` named "label" | 4 | ✅ UI display label, not a ground-truth target column |
| `pseudo_relevance` in evaluation pipeline | 6 | ✅ Heuristic keyword-match, no ground-truth leakage |
| `submission_output_path` in test configs | 13 | ✅ Output path only — no code reads from `submission.csv` |
| Blacklist/whitelist, holdout, eval-only flags | 0 | ✅ None found |

**Phase 2 Verdict:** ✅ **CLEAN** — No hardcoded shortcuts, no ground-truth leakage, no ID-based ranking manipulation.

---

## Phase 3 — Dataset Integrity Audit

**Dataset:** `India_runs_data_and_ai_challenge/candidates.jsonl`  
**Records scanned:** 100,000 (zero parse errors)

### 3a. Structural Integrity

| Check | Result |
|---|---|
| Total records | 100,000 |
| JSON parse errors | 0 |
| Records with all required keys | 100,000 / 100,000 (100%) |
| Unique candidate IDs | 100,000 (zero duplicates) |
| Malformed IDs | 0 |
| ID numeric range | CAND_0000001 – CAND_0100000 (sequential, no gaps) |
| Empty records (no skills/career/summary) | 0 |
| Placeholder/synthetic names | 0 |
| Duplicate profile fingerprints | 0 |

### 3b. Anomalies Detected

| Anomaly | Count | Assessment |
|---|---|---|
| `last_active_date < signup_date` | 7,496 (7.5%) | Data artifact — both dates are future (2025–2026) from synthetic generation; not a honeypot marker |
| `profile_completeness_score = 100` | 0 | All profiles incomplete; max observed ≈ 99 |
| `open_to_work_flag = True` | 35,339 (35.3%) | Normal distribution |
| `years_of_experience` range: 1.0–16.9 | Capped at 16.9 | Synthetic generation artifact |

### 3c. Honeypot Detection — Impossible Skill Duration Claims

**Method:** For each candidate, compare `skill.duration_months / 12` against the maximum possible years (current year minus technology first-release year). Flag if claimed duration exceeds max by more than 0.5 years.

**Strict honeypot technologies and their first-availability year:**

| Technology | First Available | Max Possible (2025) |
|---|---|---|
| LangChain | 2022 | 3 years |
| LlamaIndex | 2023 | 2 years |
| Pinecone | 2021 | 4 years |
| Weaviate | 2019 | 6 years |
| Chroma | 2022 | 3 years |
| Mistral | 2023 | 2 years |
| Gemini | 2023 | 2 years |
| Stable Diffusion | 2022 | 3 years |
| ChatGPT | 2022 | 3 years |

**Dataset-wide detection results:**

| Detection Type | Dataset-Wide | In Our Top-100 |
|---|---|---|
| Impossible skill duration | 1,016 (1.0%) | **52 (52%)** |
| YOE vs graduation mismatch | 21,748 (21.7%) | 27 | 
| Notice period > 180 days | 0 | 0 |

> **Note:** The YOE vs graduation mismatch (21,748 cases) is likely a data artifact — many candidates hold degrees earned mid-career, making their latest `education.end_year` appear recent relative to their total experience. These are **not** considered reliable honeypot indicators.

> The skill-duration impossibilities (1,016) are more definitively anomalous, but include borderline cases (e.g., `sentence-transformers: 8.0y` when max is ~6–7y depending on counting from paper vs. library release).

---

## Phase 4 — Ranking Pipeline Integrity

**Files audited:** `src/ranking/evidence_ranker.py`, `src/retrieval/strategies.py`, `src/pipelines/ranking_pipeline.py`, `src/explainability/reasoning.py`, `src/preprocessing/normalization.py`, `src/parsing/candidate_parser.py`

### Verdict: Clean — No Ranking Manipulation

- ✅ **No row-order dependency**: candidates are loaded from JSONL in file order but sorted purely by score.
- ✅ **No ID-based ranking**: the only use of `candidate_id` in sorting is the competition-required ascending tie-break.
- ✅ **No hardcoded results**: `rank=0` is a temporary placeholder, overwritten by `enumerate(top, start=1)`.
- ✅ **No ground-truth leakage**: `pseudo_relevance` is computed from profile keywords, not from any external label.
- ✅ **No submission shortcut**: no code reads from the output `submission.csv` to derive scores.

### Root Cause of Honeypot Vulnerability

The vulnerability is **not manipulation** but a **model weakness**: the `EvidenceRanker` uses `years_of_experience` as a positive signal in the experience component, and counts skill duration in the semantic match. Honeypot candidates exploit this by claiming inflated (temporally impossible) skill durations — making them appear more experienced and relevant.

```python
# evidence_ranker.py — experience scoring rewards higher YOE without plausibility checks
experience_score = min(1.0, candidate.profile.years_of_experience / target_yoe)
```

This is correct behavior for real candidates but creates a vulnerability to fabricated profiles.

---

## Phase 5 — Robustness Testing Review

**Test file:** `tests/test_robustness.py`

| Test Function | Scenario Covered |
|---|---|
| `test_missing_skills_perturbation` | Candidates with no skills still produce valid ranking |
| `test_missing_education_and_behavioral` | Empty education + empty redrob_signals handled gracefully |
| `test_duplicate_candidates` | Duplicate candidate IDs in input handled |

**Gap identified:** No robustness test covers honeypot/impossible-profile perturbation. A test verifying that candidates with impossible profiles are penalized (or at least not over-ranked) does not exist.

**Preflight checks (`src/qa/preflight.py`):** Config file existence, candidate file existence, cache integrity. No honeypot-rate pre-check.

---

## Phase 6 — Leakage & Integrity Review

| Check | Result |
|---|---|
| Submission CSV read during ranking | ✅ No — output-only path |
| Ground-truth labels embedded in code | ✅ No |
| External API calls during ranking | ✅ No — fully offline |
| Network dependency | ✅ None |
| GPU usage | ✅ None — CPU only |
| Runtime on full 100k corpus (verified) | ✅ 153.7 seconds (within 300s limit) |
| Memory (estimated) | ✅ Within 16GB |

**Phase 6 Verdict:** ✅ **CLEAN** — No integrity violations found.

---

## Phase 7 — Critical Finding: Honeypot Vulnerability in Submission

### The Problem

52 of our top-100 submitted candidates have at least one temporally impossible signal. The 10 most clearly impossible are:

| Rank | Candidate ID | Issue | Severity |
|---|---|---|---|
| 1 | CAND_0077337 | LlamaIndex: 3.9y claimed (max 2y) | High |
| 4 | CAND_0055905 | LangChain: 5.8y claimed (max 3y) | High |
| 5 | CAND_0018499 | Weaviate: 7.3y + LangChain: 4.4y + YOE/grad | High |
| 7 | CAND_0081846 | LlamaIndex: 3.2y claimed (max 2y) | High |
| 8 | CAND_0079064 | LlamaIndex: 4.2y + Pinecone: 7.5y | High |
| 9 | CAND_0046064 | Pinecone: 7.1y claimed (max 4y) | High |
| 10 | CAND_0006567 | YOE 7.9y / grad 2020 (borderline) | Medium |
| 11 | CAND_0046525 | LlamaIndex: 5.5y claimed (max 2y) | High |
| 12 | CAND_0067866 | YOE 6.4y / grad 2021 (borderline) | Medium |
| 13 | CAND_0002025 | LangChain: 7.0y claimed (max 3y) | High |
| 16 | CAND_0007412 | Pinecone: 8.0y claimed (max 4y) | High |
| 19 | CAND_0065878 | LlamaIndex: 5.0y claimed (max 2y) | High |
| 20 | CAND_0011687 | LangChain: 5.2y + LlamaIndex: 5.6y | High |
| 22 | CAND_0008425 | Sentence-transformers: 8.0y (max ~6y) | Medium |

### Risk Assessment

**Worst case:** If the competition's ~80 honeypots are drawn from the 1,016 impossible-profile candidates we detected, and if they are proportionally distributed across ranks, we should expect approximately:

```
Expected honeypots in top-100 = (80 / 100000) × 100 = 0.08 candidates (random ranker)
Our top-100 skill-impossible count = 52 candidates
Enrichment factor = 52 / 0.08 ≈ 650x
```

This extreme enrichment indicates our ranker **is selecting honeypots disproportionately**, likely because inflated experience scores cause them to rank highly. If even 11 of the 52 are official competition honeypots, we hit the 10% threshold and are disqualified at Stage 3.

**Likelihood:** Given that our rank-1 candidate already has an LlamaIndex impossibility (3.9y vs. max 2y), and ranks 4, 5, 7, 8, 9, 11, 13, 16, 19, 20 also have high-severity impossible signals, the probability of exceeding 10 official honeypots in our top-100 is **HIGH**.

---

## Phase 8 — Recommendations

### Immediate Fix (Before Re-submission)

Add a **profile plausibility filter** to the ranking pipeline that penalizes candidates with temporally impossible skill claims:

```python
# Proposed addition to evidence_ranker.py
TECH_FIRST_AVAILABLE = {
    "langchain": 2022, "llamaindex": 2023, "pinecone": 2021,
    "weaviate": 2019, "chroma": 2022, "mistral": 2023,
    "gemini": 2023, "stable diffusion": 2022, "chatgpt": 2022,
}

def _plausibility_penalty(skills: Sequence[Skill], current_year: int = 2025) -> float:
    """Return a 0.0–1.0 multiplier; < 1.0 penalizes impossible skill claims."""
    for skill in skills:
        sname = skill.name.lower()
        dur_years = (skill.duration_months or 0) / 12.0
        for tech, min_year in TECH_FIRST_AVAILABLE.items():
            if tech in sname:
                max_possible = current_year - min_year
                if dur_years > max_possible + 0.5:
                    return 0.0  # Clear honeypot signal — disqualify from top-100
    return 1.0
```

Apply as a pre-filter: candidates with `_plausibility_penalty() == 0.0` are excluded from the top-100 entirely.

### Medium-Term Improvements

1. **Add honeypot robustness test** (`tests/test_robustness.py`): verify that injected impossible-profile candidates never appear in top-50.
2. **Add honeypot rate to preflight** (`src/qa/preflight.py`): warn if >5% of top-100 have impossible signals before writing submission.
3. **Add YOE plausibility check**: compare `years_of_experience` against `career_history` total months to detect inflated YOE claims.
4. **Cross-validate career dates**: verify that no `career_history.start_date` precedes `education.end_year` by more than 3 years.

### Remediation Implemented (Post-Audit)

The immediate recommendation has been implemented and validated.

**Implementation summary**
- Added reusable plausibility module: `src/ranking/plausibility.py`
- Added `plausibility_penalty(candidate)` and `find_plausibility_issues(candidate)`
- Added deterministic competition reference year: `COMPETITION_REFERENCE_YEAR = 2025`
- Added checks for:
    - technology duration exceeding technology age
    - company tenure before company founding (for curated verifiable companies)
    - impossible career chronology (`end_date < start_date`, negative duration, duration timeline mismatch, multiple current roles)
    - impossible experience chronology (`years_of_experience` vs career start / education)
- Integrated into ranking at scoring time:
    - `final_score = original_score * plausibility_penalty(candidate)`
    - candidates with `penalty == 0.0` are excluded from final ranking output (cannot appear in top-100)

**Files modified**
- `src/ranking/plausibility.py` (new)
- `src/ranking/evidence_ranker.py`
- `src/ranking/__init__.py`
- `tests/test_plausibility_filter.py` (new)
- `tests/test_ranking_engine.py`

**Tests added/updated**
- `tests/test_plausibility_filter.py`
    - impossible technology duration -> penalty `0.0`
    - normal candidate -> penalty `1.0`
    - company tenure before founding -> penalty `0.0`
    - final-score multiplier behavior
- `tests/test_ranking_engine.py`
    - impossible profile candidate is excluded from ranked output

**Validation results**
- Full suite: `python -m unittest discover -s tests -v` -> passing
- Submission format validator: `Submission is valid.`
- Regeneration runtime (full 100k): `140.66s`
- Additional integrity check on regenerated submission:
    - top-100 candidates with `plausibility_penalty == 0.0`: `0`

**Submission regeneration**
- Regenerated file: `outputs/submission.csv`
- Timestamp: `2026-07-01T14:40:52`

**Expected impact**
- High-severity impossible-profile candidates (audit failure mode) are now prevented from entering the final top-100.
- Stage-3 honeypot disqualification risk should materially decrease versus the original submission.

---

## Metadata Update

- [x] Re-ran ranking pipeline with plausibility filter and regenerated `outputs/submission.csv`.
- [x] Validated regenerated submission with official validator (`Submission is valid.`).
- [x] Updated `submission_metadata.yaml`: `honeypot_check_done: true`.

---

## Audit Summary

| Phase | Status | Notes |
|---|---|---|
| 1. Competition Document Review | ✅ Complete | Honeypot definition confirmed, disqualification rule documented |
| 2. Repository Code Audit | ✅ CLEAN | No hardcoded IDs, no leakage, no ranking manipulation |
| 3. Dataset Integrity | ✅ CLEAN (structure) / ⚠️ FINDING | 1,016 candidates with impossible skill durations; 7,496 date artifacts |
| 4. Ranking Pipeline Integrity | ✅ REMEDIATED | No manipulation; plausibility penalty integrated in final scoring path |
| 5. Robustness Testing | ✅ IMPROVED | Added plausibility-focused unit tests (`test_plausibility_filter.py`, `test_ranking_engine.py`) |
| 6. Leakage Assessment | ✅ CLEAN | Fully offline, no ground-truth leakage |
| 7. Honeypot Check on Submission | ✅ PASS (Post-Remediation) | Regenerated submission has 0 / 100 candidates with `plausibility_penalty == 0.0` |
| 8. Recommendations | 📋 Documented | Plausibility filter, new tests, preflight check |

**Overall Verdict:** The repository and code are clean from a competition-integrity standpoint (no cheating, no leakage). The critical honeypot vulnerability identified in the original submission has been remediated via a plausibility filter, tests were added, and the submission was regenerated and validated.