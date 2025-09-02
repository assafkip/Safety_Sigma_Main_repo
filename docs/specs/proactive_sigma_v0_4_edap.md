# Proactive Sigma v0.4 — EDAP (Evidence-Driven Auto-Promotion)

## Overview
Introduce a proactive lane that expands indicators via narrative-aware analysis while preserving the authoritative scripted lane. Auto-promote expansions only when explicitly stated in source text.

## Authority Model (Unchanged)
- **Scripted lane**: Remains AUTHORITATIVE for V-001..V-005 validation gates
- **LLM lane**: Advisory (NON-AUTHORITATIVE) for speed/context  
- **Proactive lane**: Advisory (NON-AUTHORITATIVE) for expansion simulation

## EDAP Criteria
Evidence-Driven Auto-Promotion promotes expansions from "advisory" to "ready" when:

### E1: ALT_ENUM (Alternative Enumeration)
Source explicitly lists alternatives:
- "WhatsApp or Telegram"
- "such as A, B, C"
- "including X, Y, Z"

### E2: RANGE_DIGITS (Explicit Ranges)
Source specifies digit patterns:
- "3-4 digit code"
- "6+ digits"  
- "between 4 and 8 characters"

### E3: LITERAL_SET (Explicit Variants)
Source names specific variants:
- "paypaI.com, paypai.com" (typosquatting)
- "multiple domains: a.com, b.com"

## Allowed Operators
- **ALT_ENUM**: Enumeration-based patterns `(option1|option2|option3)`
- **RANGE_DIGITS**: Digit range patterns `\\d{min,max}` or `\\d{min,}`
- **LITERAL_SET**: Exact literal sets for named variants

## Contract Preservation
- Zero-inference methodology: expansions must cite exact source quotes
- Verbatim preservation: all promoted patterns trace to literal spans
- Schema invariants: proactive artifacts include full provenance
- Audit trail: complete hash-chained log of expansion decisions

## Guardrails
- Expansions without explicit evidence remain advisory-only
- No behavioral inference or threat attribution
- All patterns must be verifiable against source text with offsets
- Scripted lane continues to satisfy all V-001..V-005 gates independently

## Bundle Structure (v0.4)
```
/
├─ scripted/           # AUTHORITATIVE (unchanged)
├─ llm_output/         # Advisory LLM lane
├─ proactive/          # Advisory proactive lane  
│  ├─ expansions.json  # EDAP-promoted patterns
│  └─ evidence.json    # Source quotes and spans
├─ manifest.json       # Three-lane metadata
```

## Validation Gates (New P-series)
- **P-001**: Traceability - All expansions link to parent span_ids
- **P-002**: Mutation audit - Operator and evidence quote preserved  
- **P-003**: EDAP compliance - Only E1/E2/E3 criteria auto-promote
- **P-004**: Risk assessment - Expansion impact evaluation (stub)

## Out of Scope
- Adversary inference or behavioral modeling
- Pattern generation without explicit source evidence
- Modification of scripted lane outputs or validation gates