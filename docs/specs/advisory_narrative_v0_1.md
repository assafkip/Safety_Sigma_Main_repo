# Advisory Narrative v0.1 (NON-AUTHORITATIVE)

## Purpose
Provide an analyst-readable narrative built from **existing literal spans** in IR/rules. This improves usability without changing authoritative outputs (IR, rules, tests).

## Principles (binding to this layer)
- NON-AUTHORITATIVE: not part of IR or rules; optional; advisory only.
- Zero-inference: sentences are stitched from **quoted** spans and categories already present.
- Separation: lives in `advisory/` folder; never referenced by compiled rules or contract tests (V-001..V-005).
- Provenance: each claim must cite span ids and/or indicator values included in IR/rules.

## Output
- `advisory/narrative_advisory.md`
- `advisory/sources.json` (span → quote map)

## Sections
1) **Disclaimer (required)** — bold, red-banner style notice of non-authoritative status.
2) **Threat Themes (literal)** — behaviors/categories as bullets (e.g., "redirected to WhatsApp").
3) **Financial Indicators (literal)** — amounts and co-occurring accounts (verbatim).
4) **Infrastructure (literal)** — domains, phones, emails (verbatim).
5) **Observed Phrases (quotes)** — short quotes with span ids.
6) **Advisory Augmentations (optional)** — if LLM mode is enabled; each sentence references one or more quoted spans and is prefixed with "Advisory: …".

## Out of Scope
- Actor identity inference, ATT&CK mapping, or normalization beyond literal spans.