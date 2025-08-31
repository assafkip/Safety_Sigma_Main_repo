---
title: Intermediate Representation (IR) Schema
doc_type: schema
authority: authoritative
version: v0.4
effective_date: 2025-08-31
owner: you@company.com
links:
- /docs/tests/golden_cases.md
---


## Principles
- Lossless for indicators and categories.
- Explicit provenance: each IR field carries source doc id + span offsets.


## Top-level
```json
{
"doc_id": "<uuid>",
"extractions": [
{
"type": "amount|memo|link|category|entity|date|range|platform",
"value": "<verbatim or structured>",
"norm": {"currency": "USD", "amount": 1998.88},
"provenance": {"page": 3, "start": 1043, "end": 1052},
"confidence": 0.98
}
],
"rules": [
{
"target": "sql|json|python|regex",
"body": "<compiled rule>",
"source_refs": [ {"extraction_idx": 0} ]
}
],
"audit": {"created_at": "<iso>", "validator": "<name>", "score": 0.0}
}

C-001 Amounts MUST keep original string in value and numeric in norm. 
C-002 Links MUST be literal; no normalization. 
C-003 Categories MUST map to source spans; provide span ids.