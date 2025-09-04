---
title: Pilot Runbook (Shadow Mode)
doc_type: runbook
authority: advisory
version: v1.1
effective_date: 2025-09-04
owner: you@company.com
links:
- /docs/specs/v1.1.md
- /docs/specs/v1.1_delta.md
---

# Pilot Runbook (Shadow Mode)
## Preflight
- Set Snowflake reader role and sample window; record dataset hash and window in audit.
- Configure N_min and composite weights in config.yaml.
- Use sandbox keys for Sift/Unit21 (no prod writes).

## Run
- `make -C ops/pilot all` → compile, golden, metadata, backtest, adapters, report.
- Share `out/pilot/report/index.html` + `out/pilot/bundle.tgz` with testers.

## Gates
- V-001..V-005 outcomes visible per rule in report; promotion disabled unless all pass.
- Golden tests enforce exact preservation and category grounding.

## Roles
- Analyst: confirm span fidelity & bounded expansions.
- Engineer: treat as compiler acceptance (syntax + metrics + metadata).
- Leader: auditability & gate behavior; shadow-only.

## Rollback
- Read-only data; sandbox adapters; delete `out/pilot/` to reset. No prod enforcements in pilot.