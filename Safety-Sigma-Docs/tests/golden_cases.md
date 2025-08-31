---
title: Golden Tests – Indicator Preservation & Category Grounding
doc_type: tests
authority: authoritative
version: v1.0
effective_date: 2025-08-31
owner: you@company.com
---


## G-001 Amount exactness
- **Input span:** `$1,998.88`
- **Requirement:** exact string preserved in IR and rules
- **Validation:** string equality (no rounding/formatting)


## G-002 Memo preservation
- **Input span:** `VOID 2000`
- **Requirement:** token sequence preserved
- **Validation:** equality; audit log includes source offsets


## G-003 Link literal
- **Input span:** `wa.me/123456789`
- **Requirement:** literal preserved; scheme + path intact
- **Validation:** regex `\bwa\.me/[0-9]{6,}\b` + exact capture


## G-010 Category source check
- **Requirement:** No category appears unless explicitly in source
- **Validation:** `diff(generated_categories, source_categories) == ∅`


## G-020 NRIF coverage
- **Requirement:** NRIF/aid scam claims preserved; no paraphrase drift
- **Validation:** span capture + semantic match to source clause


## G-030 Toll scam exemplar (placeholder)
- **Requirement:** pattern detection without over-fragmentation
- **Validation:** rule fires on labeled examples; remains silent on negatives
