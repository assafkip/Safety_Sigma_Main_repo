# Pull Request Checklist

## Safety Sigma Compliance Gates (V-001..V-005)

**All boxes must be checked before merge approval.**

### V-001: PDF Processing Pipeline
- [ ] Golden tests G-001 (amount exactness), G-002 (memo preservation), G-003 (link literal) pass
- [ ] Golden test G-010 (category source check) passes - no hallucinated categories
- [ ] All extraction functions preserve indicators verbatim with proper provenance

### V-002: Intermediate Representation (IR) Compliance
- [ ] C-001: Amount IR objects preserve verbatim text AND include numeric norm.amount
- [ ] C-002: Link IR objects are literal with NO normalization fields
- [ ] C-003: Category IR objects include explicit span_ids mapping to evidence spans
- [ ] All IR objects carry complete provenance (page/start/end)

### V-003: Audit Trail Compliance
- [ ] Audit records include required fields: module_version, doc_id, spans, decisions, validation_scores, timestamp
- [ ] Audit logging is append-only JSONL format
- [ ] All spans and decisions include complete provenance information

### V-004: Rule Execution Framework
- [ ] `scripts/run_rule.py` loads IR samples and executes compiled rules successfully
- [ ] Rule execution exits 0 on success, non-zero on failure/no matches
- [ ] Practitioner harness integrates with PDF processor components

### V-005: Integration Testing
- [ ] All PDF processor modules import without errors
- [ ] docs/EXEC_CHECKLIST.md has all boxes checked (enforced by CI)
- [ ] No compliance violations detected in test suite

## Documentation Updates Required

**Check all that apply for changes in this PR:**

### Core Implementation Files Changed
- [ ] `src/pdf_processor/ingest.py` → Update `docs/specs/pdf_processor_PRD_v0.1.md`
- [ ] `src/pdf_processor/extract.py` → Update golden test documentation in `Safety-Sigma-Docs/tests/golden_cases.md`
- [ ] `src/pdf_processor/ir.py` → Update `docs/IR_SCHEMA.md` and `Safety-Sigma-Docs/ir/schema.md`
- [ ] `src/pdf_processor/audit.py` → Update `docs/AUDIT.md` and `Safety-Sigma-Docs/validation/contract.md`
- [ ] `src/pdf_processor/rules.py` → Update rule documentation in `Safety-Sigma-Docs/`

### Test Files Changed
- [ ] `tests/golden_cases/test_indicators.py` → Update `Safety-Sigma-Docs/tests/golden_cases.md`
- [ ] `tests/unit/test_pdf_processor_ir.py` → Update `Safety-Sigma-Docs/ir/schema.md`
- [ ] New test files → Update `docs/TESTING.md`

### Scripts Changed
- [ ] `scripts/run_rule.py` → Update `docs/specs/pdf_processor_PRD_v0.1.md` 
- [ ] New scripts → Update `docs/TESTING.md` or appropriate spec docs

### Configuration Changes
- [ ] Execution checklist → Update `docs/EXEC_CHECKLIST.md`
- [ ] New requirements → Update `Safety-Sigma-Docs/validation/contract.md`

## Change Description

### What changed
<!-- Describe the changes in this PR -->

### Why it changed  
<!-- Explain the reasoning behind the changes -->

### Impact on compliance
<!-- How do these changes affect V-001..V-005 compliance? -->

### Documentation updates made
<!-- List specific documentation files updated and why -->

## Testing

- [ ] All existing tests continue to pass
- [ ] New tests added for new functionality
- [ ] Golden tests G-001..G-003, G-010 validate against real extraction code
- [ ] IR invariants C-001..C-003 verified with binding tests
- [ ] `python scripts/run_rule.py` executes successfully
- [ ] Self-check passes: All compliance gates validated

## Reviewer Notes

### For Reviewers
- Verify all V-001..V-005 boxes are checked
- Confirm documentation updates match code changes
- Validate compliance gates are satisfied
- Check that `docs/EXEC_CHECKLIST.md` items remain checked

### Critical Review Points
- [ ] Zero-inference / cite-or-omit: Indicators preserved verbatim
- [ ] Category grounding: Only explicit source categories (no hallucinations)
- [ ] Provenance tracking: Every IR field carries page/start/end
- [ ] Append-only audit: Complete spans/decisions/scores logging
- [ ] Contract compliance: All binding requirements satisfied

---

**Note**: This PR template enforces Safety Sigma compliance. All V-001..V-005 gates must be satisfied before merge approval. Missing documentation updates will be flagged by CI automation.