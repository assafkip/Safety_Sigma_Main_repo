# PRD Δ v0.3 — Analyst-Fit (Display & Ops Polish)

## Scope (display/ops only; authority unchanged)
Improve analyst usability without changing the authoritative contract or schema invariants:
- Scripted lane remains the only path for V-001..V-005. LLM lane remains advisory. 
- Zero-inference, verbatim spans, category diff==∅, provenance, and deployable rules remain binding.

## New/Changed Requirements
A-301 (MUST) Display deduplication: Show each identical indicator once in HTML with a `count` and a list/tooltip of span_ids. Authoritative JSON/rules remain unchanged.

A-302 (MUST) Noise guards (literal validation only; no inference):
- Phones: require ≥7 digits and reject tokens with >30% whitespace/linebreak chars.
- Generic keywords: do not promote "fraudulent/defrauded/phishing-like" to IOC unless the exact token (e.g., "fraud") appears.
- Domains/emails: keep verbatim in IR/rules; in HTML only, display may trim trailing punctuation (e.g., `irs-help.com,` → `irs-help.com`).

A-303 (SHOULD) Relationships (explicit co-occurrence only): If IR contains a `links` array with existing span_ids, render a small "Relationships" table in HTML (from_span → to_span with verbatim values). No inference of links is allowed.

A-304 (SHOULD) Backtest harness: Provide a minimal script to run regex rules over a CSV with a `text` column, outputting match counts per rule; if a `label` column exists, compute precision proxy. No external IO.

A-305 (MUST) Compliance: All V-001..V-005 continue to be satisfied by the scripted lane outputs; LLM remains NON-AUTHORITATIVE.

## Acceptance
- Golden tests (G-001..G-003, G-010) remain green.
- New v0.3 negative/noise tests pass.
- HTML shows dedup + relationships; authoritative artifacts unchanged.
- Backtest summary JSON produced on demand.

## Out of Scope
- Actor inference; ATT&CK mapping; any heuristic categorization beyond literal spans.