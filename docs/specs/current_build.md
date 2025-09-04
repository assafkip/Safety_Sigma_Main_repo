---
title: Current Build Plan
doc_type: status
authority: advisory
version: v1.1
effective_date: 2025-09-04
owner: you@company.com
links:
- /docs/specs/v1.1.md
---

# Current Build – v1.1
**Status:** In progress  
**Objective:** Pilot-ready compiler with measured confidence + complete metadata for Snowflake/Sift/Unit21.

## Focus Areas
- Backtest harness + composite confidence
- Mandatory metadata enforcement
- Gate transparency in reports
- HTML-first report UX
- Adapter compile: 0 errors

## Exit Criteria (must all pass)
- Metrics populated; no confidence=0.000
- Required metadata present (no missing)
- Per-gate outcomes shown; only all-gates-pass rules promoted
- Snowflake/Sift/Unit21 compile with 0 errors
- <6h turnaround evidence
- Golden tests pass on IR and compiled outputs