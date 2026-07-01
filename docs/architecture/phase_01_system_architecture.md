# Phase 01 System Architecture

## Scope
This document captures the architecture baseline for README_01_SYSTEM_ARCHITECT.
It does not implement ranking logic. It defines module boundaries, contracts,
and configuration conventions that later phases will implement.

## Dataset Ground Truth
Source of truth directory:
- India_runs_data_and_ai_challenge

Observed inventory:
- candidates.jsonl (100000 records, JSONL)
- candidate_schema.json
- job_description.docx
- submission_spec.docx
- redrob_signals_doc.docx
- validate_submission.py
- sample_submission.csv

Key structural findings from Phase 0:
- Primary key: candidate_id
- 1:1 candidate -> profile
- 1:1 candidate -> redrob_signals
- 1:N candidate -> career_history, education, skills, certifications, languages
- Stable schema across all 100000 records

## Architecture Layers
1. Input and Discovery
2. Validation and Normalization
3. Candidate and Job Understanding
4. Retrieval
5. Ranking
6. Reasoning and Confidence
7. Explanation
8. Evaluation
9. Submission Generation

## Module Layout
- src/contracts: canonical dataclasses and interface protocols
- src/config: configuration loading and typed settings parsing
- src/pipelines: top-level orchestration entry points
- src/app_logging: shared logging configuration
- src/ingestion, src/validation, src/preprocessing, src/parsing,
  src/embeddings, src/retrieval, src/ranking, src/explainability,
  src/evaluation, src/dashboard, src/cache, src/monitoring, src/utils:
  reserved modular implementation packages for upcoming phases

## Design Decisions
- Dataset-first internal models: canonical objects in src/contracts/domain.py
- Interface-based modularity: Protocol contracts in src/contracts/interfaces.py
- Config-driven runtime: all execution paths and limits externalized in configs/base.yaml
- Deterministic execution posture: central runtime settings and top_n configuration
- Explanation-ready outputs: RankedCandidate includes structured evidence payload

## Known Data Risks To Handle In Later Phases
- Salary min > max appears in part of dataset; normalization policy required
- signup_date > last_active_date appears in part of dataset; validation strategy required
- skill_assessment_scores sparsity is high; confidence logic must account for missingness

## Non-Goals In This Phase
- No retrieval algorithm implementation
- No ranking model implementation
- No frontend implementation
- No experiment framework implementation

## Acceptance Mapping To README_01
- Dataset-first architecture: satisfied
- Modular structure with clear responsibilities: satisfied
- Externalized configuration baseline: satisfied
- Type-hinted, documented public modules: satisfied for phase scaffold
- ADR process established: satisfied
