# Sharing Spec (v0.7)

**Goal:** Make bundles importable/exportable across orgs while preserving authority markings and provenance.

## Bundle content
- `scripted/`, `llm_output/`, `proactive/`, `adapters/`, `tests/`, `docs/`, `manifest.json`, `README.md`
- Optional signature: `SIGNATURE.txt` (public key or detached signature location)

## Manifest fields (lanes + adapters)
- `lanes.scripted.authoritative = true`
- `lanes.llm.authoritative = false`
- `lanes.proactive.authoritative = false`
- `adapters`: { "<target>": {"present":true, "status":"compiled|error"} }

## New Gate: V-007 Sharing Integrity
- **V-007.1** Bundle completeness (all declared lanes present)
- **V-007.2** Manifest sanity (authoritative flags, hashes)
- **V-007.3** Import dry-run passes (schema read, file paths valid)
- **Evidence:** `import_log.txt`, checksum list

## Import workflow (other org)
1) Verify signature/checksum (optional)
2) Validate manifest and lanes
3) Dry-run import (no side effects)
4) Activate selected lanes/targets (policy driven)