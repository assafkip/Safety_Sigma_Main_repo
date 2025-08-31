---
title: Safety Sigma – Product Overview
doc_type: overview
authority: authoritative
version: v1.0
effective_date: 2025-08-31
owner: you@company.com
links:
- /docs/policy/guardrails.md
- /docs/tests/golden_cases.md
- /docs/ir/schema.md
- /docs/validation/contract.md
---


## Purpose
Convert unstructured threat intel (PDFs, advisories, internal write-ups) into **source-grounded IR** and **deployable detection rules** (SQL, JSON, Python, Regex) with full audit trails.


## Scope
- In: intel parsing, IR extraction, rule compilation, validation, audit logging.
- Out: general prevention frameworks not tied to source; unsourced categories.


## Success Metrics (initial)
- T1: 95%+ indicator preservation pass rate on golden tests.
- T2: < 6 hours intel → rule turnaround for scoped reports.
- T3: 0 unsourced categories in generated outputs.


## Non-goals
- End-user case management UI.
- Long-lived data lake design.


## Audiences
- Practitioners: deployable, efficient rules.
- Executives: guarantees of grounding, validation, and auditability.