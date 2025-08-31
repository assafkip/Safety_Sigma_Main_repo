# PRD — pdf_processor v0.1

## Overview
Ingest a PDF, extract spans (amount/memo/link/category), and emit **IR** with verbatim indicators, numeric norms (for amounts), and span provenance. Enforce zero-inference and category grounding. Compile minimal rules for a runnable harness. :contentReference[oaicite:0]{index=0}:contentReference[oaicite:1]{index=1}:contentReference[oaicite:2]{index=2}

## Non-negotiable Requirements (MUST)
- **R1 Indicators verbatim:** `$1,998.88`, `VOID 2000`, `wa.me/...` preserved exactly in IR and compiled rules. Tests **G-001..G-003** must pass. :contentReference[oaicite:3]{index=3}:contentReference[oaicite:4]{index=4}
- **R2 Category grounding:** only categories present in source; diff(generated, source) == ∅ (**G-010**). Fail-closed. :contentReference[oaicite:5]{index=5}:contentReference[oaicite:6]{index=6}
- **R3 IR invariants:** 
  - Amounts: `value` keeps original string; `norm.amount` numeric; `norm.currency` set. (**C-001**)  
  - Links: `value` is literal; no normalization. (**C-002**)  
  - Categories: map to explicit source spans. (**C-003**) :contentReference[oaicite:7]{index=7}
- **R4 Auditability:** append-only log with inputs, spans (page/start/end), decisions, validation scores, timestamps (**V-003**). :contentReference[oaicite:8]{index=8}:contentReference[oaicite:9]{index=9}
- **R5 Runnable rules:** produce a simple executable rule (regex/SQL/JSON) and run it in a harness (**V-004**). :contentReference[oaicite:10]{index=10}
- **R6 Acceptance gates:** V-001..V-005 must pass in CI; no UNSPECIFIED items (**V-005**). :contentReference[oaicite:11]{index=11}
- **R7 Metrics:** track T1–T3: ≥95% indicator preservation on golden tests; <6h intel→rule; 0 unsourced categories. :contentReference[oaicite:12]{index=12}

## Design (v0.1)
Pipeline stages:
1) **ingest** → PDF text + offsets  
2) **extract** → spans: amount|memo|link|category  
3) **ir_build** → emit IR objects with `value|norm|provenance`  
4) **compile_rules** → minimal regex/SQL/JSON  
5) **validate** → run G-001..G-003, G-010; score  
6) **audit** → append JSONL entry with spans/decisions/scores  
(Claude must implement pure functions per stage; no global state.)

## Alternatives (ASSUMPTIONS, need confirmation)
- OCR fallback for scans (tesseract) — **ASSUMPTION**. Q: include OCR in v0.1?  
- Compile rules here vs downstream — **ASSUMPTION**. Q: compile minimal regex here?  

## Tests & Golden Cases
- Must pass **G-001 Amount**, **G-002 Memo**, **G-003 Link**, **G-010 Category** in CI. Provide fixtures with exact spans. :contentReference[oaicite:13]{index=13}

## Audit/Logging
- JSONL, append-only; include module version, doc_id, spans (page/start/end), decisions, validation_scores, timestamp. :contentReference[oaicite:14]{index=14}:contentReference[oaicite:15]{index=15}

## Risks & Mitigations
- Indicator corruption → assert equality/regex; fail build. :contentReference[oaicite:16]{index=16}  
- Category drift → enforce G-010 diff==∅; fail-closed. :contentReference[oaicite:17]{index=17}

## Exec Guarantees
- Zero-inference, grounded categories, full audit, runnable rules with test evidence. :contentReference[oaicite:18]{index=18}:contentReference[oaicite:19]{index=19}

