# Deployment and Reproducibility Guide

## Requirements

- Python 3.10 or later (tested on 3.14.5)
- PyYAML (`pip install pyyaml`)
- python-docx (`pip install python-docx`)
- Streamlit (`pip install streamlit`) — only required for the recruiter dashboard UI

No network access is required during ranking or submission generation.  
No GPU is required.  

## Quick Start

### 1. Install dependencies

```bash
pip install pyyaml python-docx
```

### 2. Verify dataset

Confirm the following files exist in `India_runs_data_and_ai_challenge/`:

- `candidates.jsonl` — full candidate corpus
- `job_description.docx` — target job description

### 3. Generate submission CSV

```bash
python rank.py
```

This reads `configs/base.yaml` and writes `outputs/submission.csv` with exactly 100 ranked candidates.

Override paths without editing config:

```bash
python rank.py --candidates ./India_runs_data_and_ai_challenge/candidates.jsonl --out ./outputs/submission.csv
```

### 4. Validate submission

```bash
cd India_runs_data_and_ai_challenge
python validate_submission.py ../outputs/submission.csv
```

Expected output: `Submission is valid.`

### 5. Run tests

```bash
python -m unittest discover -s tests -v
```

All tests should pass. The `test_submission_writer` test runs the full corpus and calls the official validator.

---

## Configuration

All runtime settings are in `configs/base.yaml`. Key fields:

| Key | Default | Description |
|---|---|---|
| `runtime.top_n` | 100 | Number of ranked candidates in output (must be 100 for competition) |
| `runtime.random_seed` | 42 | Seed for deterministic behaviour |
| `runtime.max_candidates_to_process` | null | Cap candidate loading (null = all) |
| `retrieval.strategy` | hybrid | `lexical`, `semantic`, or `hybrid` |
| `retrieval.initial_k` | 2000 | Shortlist size before ranking |
| `ranking.confidence_threshold` | 0.5 | Minimum confidence for explanation labelling |

Environment variable overrides are supported — see `src/config/settings.py`.

---

## Reproducing Experiments

Experiment records are written to `experiments/experiment_log.jsonl` after each evaluation run. Each record includes:

- Configuration snapshot
- Dataset version
- Model/strategy identifiers
- All metric values
- Timestamp and experiment ID

To re-run the evaluation suite:

```bash
python -c "
from src.config.settings import load_config, parse_app_settings
from src.pipelines.evaluation_pipeline import EvaluationPipeline
settings = parse_app_settings(load_config('configs/base.yaml'))
summary = EvaluationPipeline(settings).execute()
print(summary)
"
```

---

## Dashboard (Optional)

```bash
pip install streamlit
streamlit run src/dashboard/streamlit_app.py
```

Navigate to `http://localhost:8501` in your browser.

---

## Project Structure

```
India_Runs/
├── rank.py                          # Production CLI entrypoint
├── submission_metadata.yaml        # Competition metadata
├── configs/base.yaml               # Externalized configuration
├── India_runs_data_and_ai_challenge/
│   ├── candidates.jsonl            # Dataset (authoritative input)
│   ├── job_description.docx        # Job requirements
│   └── validate_submission.py      # Official competition validator
├── outputs/
│   └── submission.csv              # Generated submission (rank.py output)
├── experiments/
│   └── experiment_log.jsonl        # Evaluation run history
├── src/
│   ├── config/                     # Settings parsing and env overrides
│   ├── contracts/                  # Domain types and protocol interfaces
│   ├── ingestion/                  # Dataset discovery and JSONL reading
│   ├── validation/                 # Schema inference and record validation
│   ├── parsing/                    # Candidate and job description parsing
│   ├── preprocessing/              # Normalisation and feature extraction
│   ├── retrieval/                  # Lexical, semantic, and hybrid retrieval
│   ├── ranking/                    # Evidence-based ranker with confidence
│   ├── explainability/             # Reasoning text generation
│   ├── evaluation/                 # Metrics, ablation, robustness, tracking
│   ├── submission/                 # Competition-compliant CSV writer
│   ├── dashboard/                  # Recruiter UI service and view models
│   ├── pipelines/                  # Backend, ranking, evaluation orchestration
│   ├── qa/                         # Preflight checks and performance profiling
│   ├── cache/                      # JSON file cache
│   ├── monitoring/                 # Stage-level timing metrics
│   └── app_logging/                # Structured logging setup
└── tests/                          # Full test suite (28 tests)
```
