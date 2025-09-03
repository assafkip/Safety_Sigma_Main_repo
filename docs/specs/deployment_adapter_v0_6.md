# Deployment Adapters (v0.6)

## Goal
Ensure Sigma rules compile into at least one target environment so customers can deploy quickly, aligning "practitioner readiness" with real stacks. 【/docs/validation/contract.md】 

## Targets (initial)
- Splunk SPL (detections as saved searches)
- Elastic Detection Rule JSON
- SQL Risk Engine (REGEXP_LIKE / templated DSL)

## Canonical → Target mapping
- Canonical regex → SPL `search` | Elastic `query` | SQL `REGEXP_LIKE`
- Provenance (span_id, evidence) → rule annotations/metadata
- Backtest metrics (FPR/TPR) → rule annotations

## New Gate: V-006 Deployment Readiness
- V-006.1: ≥1 adapter compiles rules without syntax error.
- V-006.2: Preserve pattern + provenance + justification in target file(s).
- V-006.3: Provide a dry-run command that returns non-zero on invalid output.

## Deliverables
- adapters/<target>/{compile.py, templates/*}
- adapters/<target>/out/* (generated)
- adapters/<target>/compile_log.txt
- HTML section "Deployment" listing generated targets and results