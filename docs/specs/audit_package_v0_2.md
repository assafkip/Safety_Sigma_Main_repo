# Audit Package v0.2 — Dual-Lane Bundle (Authoritative Scripted + Advisory LLM)

## Purpose
Deliver a reproducible, self-validating bundle with **two** parallel extraction lanes:
- **Authoritative scripted lane** (regex/parse) → grounds IR/rules and validation gates.
- **Advisory LLM lane** → faster context, narratives; clearly NON-AUTHORITATIVE.

## Authority model
- Scripted lane remains the sole source for contract gates V-001..V-005 (indicator preservation, category grounding, audit completeness, practitioner readiness, exec guarantees).
- LLM lane is optional and marked `authoritative: false`.

## Contents (additions vs v0.1)
- `scripted/`            : `ir.json` (or rules JSON), `report.html` (existing artifacts)
- `llm_output/`          : `ir.json`, `rules/*`, `narrative.md`, `audit/log.jsonl`, `validation_report.json`
- `advisory/`            : `narrative_advisory.md` (if generated), `sources.json`
- `docs/ops/privacy_legal_note_v0.1.md` (unchanged)
- `manifest.json`        : new keys under `"lanes"`:
  {
    "lanes": {
      "scripted": {"present": true,  "authoritative": true,  "version": "v0.2"},
      "llm":      {"present": true,  "authoritative": false, "config": "configs/llm_dev.yaml"}
    }
  }

## Validation gates (unchanged)
- V-001..V-005 are satisfied **solely** by the scripted lane outputs & tests.
- Golden indicators ($1,998.88, VOID 2000, wa.me/123456789) must appear verbatim in authoritative lane and match in parity checks.

## Out of scope
- Actor inference and ATT&CK mapping unless literally present in source.