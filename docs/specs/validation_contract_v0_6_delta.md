# Validation Contract Δ v0.6

**New Gates**
- **V-006 Deployment Readiness**
  - Compiles into ≥1 adapter target (SPL/Elastic/SQL) with no syntax errors
  - Preserves rule pattern + provenance + justification in target format
  - Provides a dry-run command for validation

- **V-007 Sharing Integrity**
  - Bundle completeness and manifest sanity
  - Optional signature/checksum verified
  - Import dry-run succeeds (no missing paths, no malformed JSON)

**Notes:** These gates do not change V-001..V-005 authority; they extend operational readiness.