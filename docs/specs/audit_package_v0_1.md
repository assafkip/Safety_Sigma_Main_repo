# Audit Package v0.1 — Deliverable Spec

## Purpose
Ship a reproducible, self-validating bundle from a given intel report PDF: **source-grounded IR** + **deployable rules** (SQL/JSON/Regex) + **evidence** (tests & provenance).

## Contents
- `input/` : the source PDF (or provided text)
- `ir/`    : `ir.json` (source-grounded, exact spans; C-001..C-003)
- `rules/` : `rules.json` (compiler output), `report.html` (human view)
- `tests/` : `junit_golden.xml`, `junit_audit.xml`, `junit_unit.xml`
- `manifest.json` : run metadata, versions, and **gate status** V-001..V-005

## Gate Mapping (evidence sources)
- **V-001 Indicator preservation** → Golden tests G-001..G-003 pass
- **V-002 Category grounding** → Golden G-010 pass (diff==∅)
- **V-003 Audit completeness** → `rules.json` rows carry `category_id`/`span_id`; junit_audit.xml green
- **V-004 Practitioner readiness** → regex/SQL in `rules.json` + audit junit green
- **V-005 Exec guarantees** → no `UNSPECIFIED` in artifacts + checklist items recorded in `manifest.json`

## Out of scope
- Actor inference, ATT&CK mapping, or normalization not explicitly in source.