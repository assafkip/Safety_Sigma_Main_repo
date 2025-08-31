---
title: Current Build – Working Spec (Advisory)
doc_type: spec
authority: advisory
version: v0.2-draft
effective_date: 2025-08-31
owner: you@company.com
links:
- /docs/policy/guardrails.md
- /docs/tests/golden_cases.md
---


> **Advisory**: This document proposes options. Requirements are binding only if duplicated in an authoritative doc or confirmed by the owner.


## Scope (proposed)
- Modules: pdf_processor, IR extractor, formatter, validator, side-by-side, rulecards.


## Open Questions
- Category taxonomy merge rules to reduce over-fragmentation.


## Assumptions (require confirmation)
- A1: Use intersection-only cross-LLM validator initially.


## Options
- **O1 Lean**: Regex-first extraction + targeted parsers.
- **O2 Robust**: Parser pipeline + weak supervision + schema validators.


## Risks & Mitigations
- R1: Over-fragmented categories → taxonomy consolidation tests.