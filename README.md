# Redrob Candidate Ranking System

A production-grade, CPU-native intelligent candidate discovery and ranking platform. The system ingests large candidate corpora, applies a multi-signal evidence-weighted ranking model, generates structured recruiter-facing explanations, and produces a deterministically reproducible ranked output — all within a sub-5-minute wall-clock budget on commodity hardware.

---

## System Overview

The platform solves the core recruiter intelligence problem: given a job description and a large pool of candidates, surface the highest-fit individuals, ranked by evidence quality, with transparent reasoning.

It is built as a standalone internal service: the system runs fully offline, requires no GPU, makes no external API calls at inference time, and produces reproducible output on every run given the same inputs. Configuration is fully externalized. Each pipeline stage is independently testable and monitored.

```
Candidate Corpus (JSONL)
         │
         ▼
   Ingestion + Validation
         │
         ▼
   Hybrid Retrieval (lexical + semantic + metadata)
   Initial shortlist: top-k from 100 000 candidates
         │
         ▼
   Evidence-Weighted Ranker
   5-component scoring with plausibility guard
         │
         ▼
   Explanation Generator
   Per-candidate reasoning attached inline
         │
         ▼
   Output Writer + Integrity Checks
   Ranked CSV with strict schema enforcement
```

---

## Architecture

### Domain model and contracts

All internal objects — candidates, profiles, career records, skills, redrob signals, job descriptions — are defined as immutable frozen dataclasses in `src/contracts/domain.py`. Protocol interfaces for pipeline boundaries are in `src/contracts/interfaces.py`. No pipeline stage consumes raw dictionaries directly.

### Ingestion and parsing (`src/ingestion`, `src/parsing`)

- Streaming JSONL reader for large corpora — does not load the full dataset into memory before iteration
- Raw record schema validation and normalization before domain object construction
- Separate parsers for candidate records and DOCX job descriptions
- Strict separation between raw-record validation and canonical-object validation

### Retrieval (`src/retrieval/strategies.py`)

Three strategies are available, configurable at runtime:

| Strategy | Mechanism | Use case |
|---|---|---|
| `lexical` | Token-frequency intersection over candidate tokens and JD requirements | High-precision term matching |
| `semantic` | Token overlap with JD role text weighted by coverage ratio | Broader vocabulary recall |
| `hybrid` | Weighted combination of lexical (35%), semantic (45%), and metadata signals (20%) | Default production mode |

The retrieval step produces a shortlist of the top-`initial_k` candidates (default: 2000) from the full corpus, which is then passed to the ranker.

### Evidence-based ranker (`src/ranking/evidence_ranker.py`)

Final score is a weighted linear combination of five interpretable components:

| Component | Default weight | Signal |
|---|---|---|
| Semantic alignment | 0.30 | Token overlap between candidate profile and JD |
| Experience alignment | 0.20 | Years of experience relative to JD seniority range |
| Career progression | 0.15 | Career depth and current-title seniority indicators |
| Behavioral availability | 0.20 | Open-to-work flag, recruiter response rate, interview completion |
| Trust / completeness | 0.15 | Verified contact, LinkedIn connection, profile completeness score |

Tie-breaking is deterministic: equal scores are resolved by `candidate_id` ascending. Output order is stable across identical runs.

### Profile plausibility filter (`src/ranking/plausibility.py`)

Before a candidate enters the final ranked list, the system applies `plausibility_penalty(candidate)` — a hard multiplier that returns `0.0` for candidates with clearly impossible profile claims, removing them from ranked output entirely. This prevents inflated profiles from gaming the experience-alignment component.

Checks performed:
- Skill `duration_months` exceeds the age of the technology (based on a curated tech-release-year knowledge base, fixed at reference year 2025 for determinism)
- Employer tenure pre-dates the verified founding year of the company
- Career record chronology violations (`end_date < start_date`, negative duration, timeline–duration mismatch)
- Multiple simultaneous current-employer flags
- `years_of_experience` irreconcilable with earliest career start or education history

Any single violation drives the candidate's final score to zero and removes them from the output pool.

### Explanation generator (`src/explainability`)

Each ranked candidate receives an inline reasoning string built from its evidence components at score time — not post-hoc. The explanation references concrete evidence signals (title, experience level, behavioral availability, confidence label) and is rank-consistent: higher-ranked candidates produce more positive reasoning and vice versa.

### Output writer (`src/submission/writer.py`)

The `SubmissionWriter` enforces the output contract before writing:
- Exactly 100 rows
- Each rank 1–100 appears exactly once
- No duplicate candidate IDs
- Score strictly non-increasing by rank

Any violation raises a `ValueError` before disk write — ranking output is either fully compliant or rejected.

### Pipeline orchestration (`src/pipelines`)

| Pipeline | Entry point | Purpose |
|---|---|---|
| `RankingPipeline` | `src/pipelines/ranking_pipeline.py` | Production path: retrieval → ranking → reasoning → output |
| `EvaluationPipeline` | `src/pipelines/evaluation_pipeline.py` | Offline experiment path: ranking + NDCG/MAP/MRR metrics + ablation + robustness |
| `BackendPipeline` | `src/pipelines/backend_pipeline.py` | Dashboard service backend |

All pipelines run preflight health checks on startup and emit per-stage timing metrics.

### QA and preflight (`src/qa`)

`RepositoryHealthChecker` validates the environment before any pipeline stage runs:
- Config file presence and schema validity
- Dataset file accessibility
- Output directory writeability
- Cache integrity

`PerformanceProfiler` measures and reports wall-clock time per pipeline stage.

### Dashboard (`src/dashboard`)

A Streamlit-based recruiter UI that:
- Auto-runs the full ranking pipeline on first load
- Displays ranked candidates with evidence breakdowns and explanations
- Supports text search, experience filter, and side-by-side candidate comparison
- Exports shortlists to CSV

Launch with:
```bash
streamlit run src/dashboard/streamlit_app.py
```

---

## Repository Layout

```
Redrob-Candidate-Ranking-System/
├── rank.py                               # CLI entrypoint — produces ranked CSV
├── configs/
│   └── base.yaml                         # Externalized runtime configuration
├── requirements.txt
├── submission_metadata.yaml
├── outputs/
│   └── submission.csv                    # Ranked output (generated by rank.py)
├── India_runs_data_and_ai_challenge/
│   ├── candidates.jsonl                  # Candidate corpus
│   ├── job_description.docx              # Target job description
│   └── validate_submission.py            # Output schema validator
├── src/
│   ├── config/                           # Settings parsing and env-var overrides
│   ├── contracts/                        # Frozen domain types and protocol interfaces
│   ├── ingestion/                        # Streaming JSONL reader and corpus discovery
│   ├── parsing/                          # Candidate and JD parsers
│   ├── preprocessing/                    # Record normalization and feature extraction
│   ├── validation/                       # Raw and canonical record validators
│   ├── retrieval/                        # Lexical, semantic, and hybrid retrieval
│   ├── ranking/                          # Evidence ranker and plausibility filter
│   ├── explainability/                   # Reasoning generation and explanation builder
│   ├── evaluation/                       # Offline metrics, ablation, robustness, tracking
│   ├── submission/                       # Output writer with contract enforcement
│   ├── pipelines/                        # Ranking, evaluation, and backend orchestrators
│   ├── qa/                               # Preflight checks and performance profiling
│   ├── dashboard/                        # Streamlit UI, service layer, and view models
│   ├── monitoring/                       # Stage-level timing instrumentation
│   ├── cache/                            # JSON file cache
│   └── app_logging/                      # Structured logging setup
├── tests/                                # Automated test suite (33 tests)
└── docs/
    ├── DEPLOYMENT.md
    ├── TECHNICAL_DEBT.md
    └── honeypot_audit_report.md
```

---

## Getting Started

### Prerequisites

- Python 3.10 or later (tested on 3.14.5)
- No GPU required
- No network access required at runtime

### Installation

```bash
python -m pip install -r requirements.txt
```

### Running the ranking pipeline

```bash
python rank.py
```

With explicit path overrides (no config edit required):

```bash
python rank.py \
  --config configs/base.yaml \
  --candidates ./India_runs_data_and_ai_challenge/candidates.jsonl \
  --out ./outputs/submission.csv
```

Progress is printed to stdout:

```
[rank.py] Starting ranking pipeline (top_n=100) …
[rank.py] Pipeline complete in 140.7s — scanned=100000 parsed=92504 ranked=100
[rank.py] Submission written to: outputs/submission.csv
[rank.py] Rows written: 100 (ranks 1–100)
```

### Validating output integrity

```bash
python India_runs_data_and_ai_challenge/validate_submission.py outputs/submission.csv
```

Expected: `Submission is valid.`

---

## Configuration Reference

All runtime behavior is controlled by `configs/base.yaml`. No code changes are required to alter pipeline behavior.

| Setting | Default | Description |
|---|---|---|
| `runtime.top_n` | `100` | Number of candidates in ranked output |
| `runtime.random_seed` | `42` | Seed for all stochastic operations |
| `runtime.strict_validation` | `true` | Drop records that fail schema validation |
| `runtime.max_candidates_to_process` | `null` | Cap corpus size for development runs |
| `retrieval.strategy` | `hybrid` | Retrieval mode: `lexical`, `semantic`, `hybrid` |
| `retrieval.initial_k` | `2000` | Shortlist size before ranking step |
| `ranking.confidence_threshold` | `0.5` | Confidence label cutoff for explanation generation |
| `evaluation.enable_ablation` | `true` | Run ablation study during evaluation pipeline |
| `evaluation.enable_robustness` | `true` | Run perturbation analysis during evaluation |

Environment variable overrides are supported — see `src/config/settings.py` for the full mapping.

---

## Automated Test Suite

The test suite covers contracts, parsers, validators, rankers, pipelines, and output integrity. All 33 tests pass on the current codebase.

```bash
python -m unittest discover -s tests -v
```

| Test module | Coverage area |
|---|---|
| `test_domain_contracts` | Immutable domain dataclasses and field defaults |
| `test_parsing` | Candidate and job description parser behavior |
| `test_preprocessing` | Record normalization and feature extraction |
| `test_settings` | Config loading, env override, and schema validation |
| `test_ranking_engine` | Retrieval strategies, evidence scoring, tie-break ordering, plausibility exclusion |
| `test_plausibility_filter` | Penalty assignment for impossible-profile signals and normal profiles |
| `test_ranking_pipeline` | End-to-end pipeline execution on bounded corpus |
| `test_reproducibility` | Output determinism across independent pipeline executions |
| `test_robustness` | Graceful handling of missing skills, education, and behavioral signals |
| `test_evaluation_pipeline` | Offline evaluation pipeline execution and metric generation |
| `test_evaluation_metrics` | NDCG, MAP, MRR, precision, confidence correlation |
| `test_qa_preflight` | Preflight detection of missing files and invalid config |
| `test_qa_performance` | Stage-level timing instrumentation |
| `test_submission_writer` | Output schema enforcement and format validator compatibility |
| `test_dashboard_service` | Dashboard service layer and shortlist export |
| `test_dashboard_view_models` | View model construction, search filtering, and comparison |
| `test_backend_pipeline` | Backend pipeline execution on bounded corpus |

---

## Output Integrity Guarantees

The system enforces a set of hard invariants at the output boundary via `SubmissionWriter._validate()`. These are not warnings — any violation raises before a file is written.

| Invariant | Enforcement point |
|---|---|
| Exactly 100 rows | `SubmissionWriter.write()` |
| Ranks 1–100 each appear exactly once | `SubmissionWriter._validate()` |
| No duplicate `candidate_id` in output | `SubmissionWriter._validate()` |
| Score non-increasing by rank | `SubmissionWriter._validate()` |
| Tie-break is `candidate_id` ascending | `EvidenceBasedRanker.rank()` sort key |
| No plausibility-zero candidate in ranked output | `EvidenceBasedRanker.rank()` exclusion guard |

Independent verification against the provided schema validator:

```bash
python India_runs_data_and_ai_challenge/validate_submission.py outputs/submission.csv
# Submission is valid.
```

---

## Operational Characteristics

| Property | Observed value |
|---|---|
| Full corpus size | 100 000 candidates |
| Corpus parse rate | ~92 500 valid records (92.5%) |
| End-to-end ranking runtime | ~140–160 seconds on a standard CPU machine |
| Memory profile | Well within 16 GB on commodity hardware |
| External network dependency | None — fully air-gapped at inference time |
| GPU requirement | None |
| Determinism | Fully deterministic given identical input and config |

---

## Further Reading

| Document | Location |
|---|---|
| Deployment and environment setup | `docs/DEPLOYMENT.md` |
| Technical debt register | `docs/TECHNICAL_DEBT.md` |
| Profile integrity audit report | `docs/honeypot_audit_report.md` |
| ADRs | `docs/adr/` |
