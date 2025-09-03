# Sharing Spec (v0.7)

## Goal
Make bundles importable/exportable across orgs while preserving authority flags, provenance, and manifest sanity — enabling operational signal sharing. 【/docs/overview.md】

## Bundle contents
- scripted/, llm_output/, proactive/, adapters/, tests/, docs/, manifest.json, README.md
- optional SIGNATURE.txt (checksum/signature pointer)

## New Gate: V-007 Sharing Integrity
- V-007.1: Bundle completeness (all declared lanes present; authoritative flags correct).
- V-007.2: Manifest sanity (paths, hashes/checksums list).
- V-007.3: Import dry-run passes (no missing files; JSON parseable).

## Deliverables
- scripts/share_export.py (build bundle + checksums)
- scripts/share_import.py (dry-run validate/extract)
- sharing/import_log.txt, sharing/checksums.txt
- HTML "Sharing" section summarizing integrity checks