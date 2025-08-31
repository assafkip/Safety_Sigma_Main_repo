# /docs/validation/contract.md
```markdown
---
title: Validation Contract – Acceptance Criteria
doc_type: policy
authority: authoritative
version: v0.3
effective_date: 2025-08-31
owner: you@company.com
---


## Acceptance gates (all MUST pass)
- **V-001 Indicator preservation:** G-001..G-003 pass per module outputs.
- **V-002 Category grounding:** G-010 pass; diff == ∅.
- **V-003 Audit completeness:** every output carries provenance + spans + decisions.
- **V-004 Practitioner readiness:** rules execute on sample DB or harness.
- **V-005 Exec guarantees:** policy checklist completed; no UNSPECIFIED items.


## Evidence to record
- module version, inputs, spans, decisions, test results, timestamps.