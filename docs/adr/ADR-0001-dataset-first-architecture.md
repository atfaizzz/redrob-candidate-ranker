# ADR-0001: Dataset-First, Contract-Driven Architecture

## Status
Accepted

## Context
The project must rank candidates for a specific hiring challenge with strict
runtime limits and explainability requirements. The dataset is nested JSONL with
behavioral signals and profile history structures. A monolithic script approach
would increase coupling and make future ranking experiments brittle.

## Options Considered
1. Monolithic ranking script with inline parsing and scoring
2. Layered modules with ad-hoc dictionaries and loose conventions
3. Canonical dataclasses + protocol interfaces + config-driven modules

## Decision
Adopt option 3:
- Canonical domain models in src/contracts/domain.py
- Protocol contracts in src/contracts/interfaces.py
- Central settings loader in src/config/settings.py
- Top-level pipeline entry point in src/pipelines/system_pipeline.py
- Externalized config in configs/base.yaml

## Consequences
- Positive:
  - Enables independent evolution of ingestion, retrieval, and ranking modules
  - Makes reasoning outputs and confidence factors first-class artifacts
  - Reduces hidden assumptions by encoding shared objects and interfaces
- Negative:
  - Additional upfront scaffolding before feature delivery
  - Requires discipline to keep implementations aligned to contracts

## Trade-offs
This choice prioritizes maintainability and explainability over immediate coding speed.

## References
- README_01_SYSTEM_ARCHITECT.md
- MASTER_ORCHESTRATOR.md
- India_runs_data_and_ai_challenge/candidate_schema.json
