# Validation Contract Δ v0.6 / v0.7

**V-006 Deployment Readiness**  
- Compiles into ≥1 adapter target with no syntax errors  
- Preserves pattern + provenance + justification  
- Dry-run command returns success

**V-007 Sharing Integrity**  
- Bundle completeness + manifest sanity  
- Checksums present/verified  
- Import dry-run succeeds (no malformed or missing files)

Notes: These extend operational readiness; they do not alter V-001..V-005. 【/docs/validation/contract.md】