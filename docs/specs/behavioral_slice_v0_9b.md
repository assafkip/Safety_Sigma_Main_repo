# PRD Δ v0.9b — Behavioral Slice

## Purpose
Make behaviors (tactics, payment methods, redirects, spoofing, urgency) first-class in Sigma. Keep authoritative lane literal, expand only when evidence explicitly lists enumerations or ranges. Surface memory-driven families (velocity, diversity, recurrence) to move from reactive to proactive posture without inference.

## Scope (In)
- Schema: add `type=behavior` with required fields: `value` (verbatim), `category` (optional structured e.g. platform, payment), `provenance` (doc_id, span_id, offsets).
- Extraction: capture literal phrases explicitly naming behaviors (e.g. "redirected to WhatsApp", "spoofed caller ID").
- EDAP expansions (advisory): when reports state enumerations ("WhatsApp or Telegram", "gift cards, wire transfers, or crypto") or ranges ("3–4 digit code").
- Memory: aggregate behaviors across cases, show family counts, velocity (days between first_seen/last_seen).
- Report: "Behavioral Analysis" section with current case indicators + memory families.

## Scope (Out)
- No synonym guessing, no ATT&CK mapping, no inferred actor context.

## New Goldens
- G-060: redirect behavior preserved verbatim.
- G-061: spoofed caller ID phrase preserved.
- G-062: payment method enumeration preserved (gift cards, wire, crypto).

## Acceptance
- V-001..V-005 remain intact for scripted lane.
- Behavioral spans extracted with provenance.
- EDAP expansions marked advisory and tied to explicit enumerations/ranges.
- Memory shows prior-case families with counts and velocity.
- HTML report displays "Behavioral Analysis" and "Behavioral Families".