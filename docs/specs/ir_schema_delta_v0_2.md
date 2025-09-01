# PRD Δ v0.2 — IR Schema Extension for Richer Indicators

## Overview
Extend IR to capture additional **literal** indicators/behaviors that appear in source PDFs. No inference, no normalization. Every item carries provenance + span ids and is category-grounded.

## New types (MUST)
- `domain` (e.g., `irs-help.com`)
- `phone` (e.g., `+1-800-123-4567`)
- `email` (e.g., `support@imf-aid.org`)
- `account` (e.g., `Zelle ID 123456789`)
- `behavior` (literal phrases like `redirected to WhatsApp`, `spoofed caller ID`)

## Invariants
- Verbatim preservation of source spans; no added scheme or casing changes.
- Category diff == ∅ vs. source categories.
- Provenance present on all items: {doc_id?, page, start, end} where available.
- Links: optional, only between spans that co-occur explicitly (no inference).

## Out of scope
- Actor identity inference; ATT&CK mapping; heuristic normalization.

## Golden tests (new)
- G-040 Phone exactness: `+1-800-123-4567`
- G-041 Domain exactness: `irs-help.com`
- G-042 Email exactness: `support@imf-aid.org`
- G-043 Behavior exactness: `redirected to WhatsApp`
- G-044 Relational link: `$1,998.88` ↔ `Zelle ID 123456789` (same sentence)