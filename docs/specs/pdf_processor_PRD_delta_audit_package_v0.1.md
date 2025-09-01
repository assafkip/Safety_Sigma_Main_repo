# PRD Δ v0.1 — Audit Package

## Overview
Adds a consulting-ready “Audit Package” deliverable to pdf_processor.  
Goal: monetize Safety Sigma outputs as validated audit bundles without breaking guardrails.

## New/Changed Requirements
A-101 (MUST) Audit Package includes three artifacts:
  1. Exec-facing Audit Report (overview + acceptance checklist).
  2. Practitioner Rule Pack (SQL/Regex/JSON compiled rules).
  3. Evidence Bundle (PDFs, IR JSON, rules JSON/SQL, test results, audit log).

A-102 (MUST) All artifacts MUST pass V-001..V-005:
  - Indicator preservation (G-001..G-003 exact matches).
  - Category grounding (G-010 diff == ∅).
  - Audit completeness (provenance + spans present).
  - Practitioner readiness (rules execute on harness).
  - Exec guarantees (no UNSPECIFIED items).

A-103 (MUST) Audit Report MUST include a compliance checklist mapping artifacts → acceptance gates.

A-104 (SHOULD) Deliverables are append-only: original inputs + all derived artifacts are preserved without mutation.

## Acceptance Mapping
- V-001 → validated in rule pack + evidence bundle.
- V-002 → validated by category diff in evidence bundle.
- V-003 → validated by audit log in evidence bundle.
- V-004 → validated by rule pack test harness.
- V-005 → validated by exec checklist in audit report.

## Non-goals
- No new UI dashboards.
- No heuristic scoring beyond IR extraction.
