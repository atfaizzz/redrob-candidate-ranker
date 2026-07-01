# Technical Debt Register

Last updated: 2026-06-29

---

## Open Items

### TD-001: Token-overlap semantic alignment
**Severity:** Medium  
**Area:** `src/retrieval/strategies.py`, `src/ranking/evidence_ranker.py`  
**Description:** Semantic alignment is computed using token-set intersection. This misses synonyms, paraphrases, and domain-specific terminology variants.  
**Proposed fix:** Replace with sentence-transformer embeddings (e.g., `all-MiniLM-L6-v2`) pre-computed offline and served from disk. Requires no network access at inference time.  
**Blocking factor:** Model download and disk storage; adds ~80 MB dependency.

---

### TD-002: Ranker weights are expert-assigned
**Severity:** Low-Medium  
**Area:** `src/ranking/evidence_ranker.py` (`RankerWeights`)  
**Description:** The five evidence component weights (0.30/0.20/0.15/0.20/0.15) were set by engineering judgment. Weights have not been optimised against labelled data.  
**Proposed fix:** Once ground-truth labels are available, run Bayesian optimisation or LambdaMART training to learn optimal weights.

---

### TD-003: No de-duplication of candidates before ranking
**Severity:** Low  
**Area:** `src/pipelines/ranking_pipeline.py`  
**Description:** Duplicate candidate records (same `candidate_id`, multiple JSONL lines) are parsed and ranked separately. The last-occurrence wins in the `candidates_by_id` map, but duplicates inflate retrieval pool size.  
**Proposed fix:** Add deduplication step in `CandidateParser` or at the ingestion layer keyed on `candidate_id`.

---

### TD-004: Dashboard Streamlit test coverage
**Severity:** Low  
**Area:** `src/dashboard/streamlit_app.py`  
**Description:** The Streamlit UI layer has no automated browser or widget-level tests. Service and view-model layers are tested but `run_dashboard()` is not exercised in CI.  
**Proposed fix:** Add a smoke test using `streamlit.testing.v1.AppTest` (available from Streamlit 1.18+).

---

### TD-005: Experiment log grows unboundedly
**Severity:** Low  
**Area:** `src/evaluation/experiment_tracking.py`, `experiments/experiment_log.jsonl`  
**Description:** Every evaluation pipeline run appends a new record to `experiment_log.jsonl`. There is no rotation, pruning, or archival policy.  
**Proposed fix:** Add a configurable max-records-per-file setting and auto-rotate to `experiment_log.YYYYMMDD.jsonl`.

---

### TD-006: No streaming for retrieval
**Severity:** Low  
**Area:** `src/retrieval/strategies.py`  
**Description:** All three retrieval methods materialise the full candidate list into memory before scoring. With very large candidate corpora (> 500k) this may strain memory.  
**Proposed fix:** Convert `retrieve_*` methods to accept iterables and use a bounded heap (e.g. `heapq.nlargest`) to keep memory footprint O(k) instead of O(n).

---

## Resolved Items

| ID | Description | Resolved in phase |
|----|---|---|
| TD-000 | Missing competition tie-break rule (candidate_id ascending for equal scores) | README_07 — fixed in `evidence_ranker.py` sort key |
