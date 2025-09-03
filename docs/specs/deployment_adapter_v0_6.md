# Deployment Adapters (v0.6)

**Purpose:** Ensure Sigma rules compile into at least one target system so customers can deploy immediately.

## Targets (initial)
- Splunk SPL (detections as saved searches)
- Elastic Detection (Rule JSON)
- SQL Risk Engine (templated DDL/DML or DSL)

## Canonical → Target mapping
- Canonical regex → SPL `search` | Elastic `query` | SQL `REGEXP_LIKE`
- Provenance (span_id, evidence) → attach as rule annotations/metadata
- Backtest metrics → annotate rule with FPR/TPR + samples_tested

## Validation Gate (new): V-006 Deployment Readiness
- **V-006.1** At least one adapter compiles canonical rules without syntax errors.
- **V-006.2** Critical metadata preserved (pattern, category_id, span references, justification).
- **V-006.3** Dry-run command exists and passes (adapter smoke test).
- **Evidence:** `adapters/<target>/compile_log.txt`, sample generated files.

## Acceptance
- `adapters/<target>/` folder with generated rule files
- Smoke test command + non-zero failure if invalid
- HTML report "Deployment" section lists targets generated + results