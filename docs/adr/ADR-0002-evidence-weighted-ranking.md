# Architecture Decision Record: ADR-0002 — Evidence-Weighted Ranking Strategy

**Date:** 2026-06-29  
**Status:** Accepted  
**Phase:** README_03 (ML Ranking Engine)

---

## Context

The challenge requires ranking ~100,000 candidates for a specific AI/ML role and producing a competition-compliant CSV with 100 rows. Candidate data is rich (career history, skills, Redrob behavioural signals, education) but there are no labeled ground-truth relevance judgements available. An embedding model cannot be run online (network-off constraint). The solution must be fully reproducible on CPU within 5 minutes.

## Decision

Use an **evidence-weighted linear ranker** with five interpretable components:

| Component | Weight | Description |
|---|---|---|
| Semantic alignment | 0.30 | Token overlap between candidate profile and job must-have + preferred requirements |
| Experience alignment | 0.20 | Proximity of candidate years-of-experience to job seniority range |
| Career progression | 0.15 | Career depth and seniority-title signals |
| Behavioural availability | 0.20 | Open-to-work flag, recruiter response rate, interview completion rate, response time |
| Trust signals | 0.15 | Verified email/phone/LinkedIn, profile completeness, skill assessment coverage |

Confidence is estimated from profile completeness, internal consistency, and inter-component agreement.

Retrieval is a three-strategy hybrid (lexical 35 % + semantic 45 % + metadata 20 %) that narrows 100k to an `initial_k` shortlist before ranking.

## Alternatives Considered

1. **Pure lexical TF-IDF** — fast and transparent but ignores behavioural and trust signals entirely; would over-rank keyword-stuffed profiles.
2. **Neural sentence embeddings** — higher semantic recall but requires network access (prohibited) or pre-computed index (adds operational complexity); no ranking improvement guaranteed without labelled data.
3. **Learned-to-rank (LambdaMART)** — optimal when labelled data exists; not applicable without ground truth.

## Consequences

**Positive:**
- Fully interpretable — every score component is readable and auditable.
- Deterministic and reproducible; no stochastic training steps.
- Fast: < 5 seconds on CPU for full 100k corpus at `initial_k=2000`.
- Explainability is grounded in the same evidence used for ranking.

**Negative / Accepted trade-offs:**
- Token overlap for semantic alignment is an approximation of true semantic similarity.
- Weights are expert-assigned; hyperparameter search could improve ranking quality.
- No cross-candidate calibration; scores are relative within a run, not absolute.

## Review Notes

The tie-breaking rule (equal scores → candidate_id ascending) was applied at the ranker sort level to satisfy the competition validator constraint. This was confirmed and corrected in the README_07 phase after the official `validate_submission.py` rule was inspected.
