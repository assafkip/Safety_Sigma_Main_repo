---
title: Guardrails & Compliance – Zero Inference and Auditability
doc_type: policy
authority: authoritative
version: v1.0
effective_date: 2025-08-31
owner: you@company.com
---


## Binding Rules
1. **Zero-inference / cite-or-omit**: every factual output is traceable to a source span or is omitted.
2. **Exact indicator preservation**: amounts, tokens, links (e.g., `$1,998.88`, `VOID 2000`, `wa.me`) must be preserved verbatim in IR and compiled rules.
3. **Category validation**: only categories present explicitly in source may appear.
4. **Dual audience outputs**: each spec delivers practitioner rules + exec guarantees.
5. **Auditability**: append-only audit records with inputs, spans, decisions, validation scores.


## Do / Don’t Examples
- ✅ Keep `£300–800/day` exact; encode range properly.
- ❌ Normalize to `hundreds per day` or introduce `romance scams` if not