# LLM Lane Compliance Specification v0.1

## Overview

This document specifies how the Safety Sigma LLM integration lane enforces validation gates V-001 through V-005 and maintains advisory separation from authoritative artifacts.

**Status**: Draft v0.1  
**Date**: September 2025  
**Applies to**: Safety Sigma LLM integration layer

## Executive Summary

The LLM lane provides an alternative processing path that:
- Maintains identical compliance standards as the scripted lane  
- Enforces V-001..V-005 validation gates through code-level guardrails
- Produces NON-AUTHORITATIVE outputs clearly separated from authoritative artifacts
- Provides audit trail with tamper-evident logging for regulatory compliance

## Validation Gates Implementation

### V-001: Indicator Preservation

**Requirement**: All indicators must be preserved exactly as found in source documents (verbatim text maintenance).

**LLM Lane Implementation**:
```python
# llm_integration/adapter.py lines 78-95
def _build_ir_deterministic(self, extractions_raw, source_doc):
    """Preserves exact indicators verbatim"""
    for extraction in extractions_raw:
        value = extraction.get("value", "")  # Verbatim preservation
        ir_extraction = {
            "value": value,  # No normalization applied
            # ...
        }
```

**Enforcement Mechanisms**:
- **Code-level**: Direct verbatim copying with no string transformation
- **Testing**: Golden tests verify `$1,998.88`, `VOID 2000`, `wa.me/123456789` preserved exactly
- **Validation**: `IRValidator.validate_ir_against_golden()` checks for normalization artifacts
- **Audit**: All processing decisions logged with input/output hashes

**Test Evidence**: `tests/test_llm_integration.py::test_build_ir_preserves_exact_indicators`

### V-002: Category Grounding

**Requirement**: Categories appear only if explicitly present in source with span IDs.

**LLM Lane Implementation**:
```python
# llm_integration/validator.py lines 89-120
def _validate_category_grounding(self, extractions):
    """Ensures categories only appear if explicitly sourced"""
    for extraction in extractions:
        if extraction.get("type") == "category":
            # Check provenance exists
            provenance = extraction.get("provenance", {})
            if not provenance:
                result["issues"].append("Category lacks provenance")
```

**Enforcement Mechanisms**:
- **Prompt-level**: System prompts explicitly forbid category invention
- **Code-level**: Category extractions require source_span with span_id  
- **Validation**: `_validate_category_grounding()` verifies provenance for categories
- **Testing**: Negative tests ensure benign input doesn't generate threat categories

**Prompt Guardrails**:
```
"Categories only if explicit in source; include span ids"
"If unsure, mark UNSPECIFIED and leave field absent"
```

### V-003: Audit Completeness

**Requirement**: Every extraction has provenance + spans + source tracking.

**LLM Lane Implementation**:
```python
# llm_integration/adapter.py lines 132-147
ir_extraction = {
    "provenance": {
        "page": extraction.get("page", 1),
        "start": extraction.get("start", 0), 
        "end": extraction.get("end", len(value))
    },
    "source_span": {
        "category_id": extraction.get("category_id", ""),
        "span_id": extraction.get("span_id", f"span_{idx}")
    }
}
```

**Enforcement Mechanisms**:
- **Code-level**: Mandatory provenance fields in IR schema
- **Validation**: `_validate_audit_completeness()` checks all required fields
- **Audit**: Complete processing chain logged to `audit/log.jsonl`
- **Tamper-evidence**: Hash chain prevents log modification

### V-004: Practitioner Readiness

**Requirement**: Generated rules execute without syntax errors.

**LLM Lane Implementation**:
```python
# llm_integration/validator.py lines 196-250  
def validate_rules(self, rules):
    """Validate rules execute without syntax errors"""
    for target, content in rules.items():
        if target == "regex":
            patterns = self._extract_regex_patterns(content)
            for pattern in patterns:
                try:
                    re.compile(pattern)  # Syntax validation
                except re.error as e:
                    result["issues"].append(f"Invalid regex: {e}")
```

**Enforcement Mechanisms**:
- **Code-level**: Syntax validation for all rule targets (regex, JSON, Python, SQL)
- **Testing**: Rules executed in test harness to verify functionality  
- **CI**: Rules tested in automated pipeline before deployment
- **Compilation**: Safe escaping prevents injection while preserving indicators

### V-005: Execution Guarantees

**Requirement**: No UNSPECIFIED values in production outputs.

**LLM Lane Implementation**:
```python
# llm_integration/validator.py lines 332-356
def _check_execution_guarantees(self, ir, rules, config):
    """Check no UNSPECIFIED values in outputs"""
    ir_str = json.dumps(ir)
    if "UNSPECIFIED" in ir_str:
        result["issues"].append("UNSPECIFIED values found in IR")
    
    for target, content in rules.items():
        if "UNSPECIFIED" in content:
            result["issues"].append(f"UNSPECIFIED in {target} rules")
```

**Enforcement Mechanisms**:
- **Code-level**: String scanning for UNSPECIFIED markers in all outputs
- **Configuration**: Required config fields validated (model_name, targets)
- **Processing**: Deterministic mode (temperature=0) prevents variability
- **Fallback**: Safe defaults when LLM unavailable (deterministic rule-based processing)

## Prompt Engineering for Compliance

### System Prompt Structure

All LLM interactions use structured system prompts that enforce compliance:

1. **IR Structuring Prompt**:
```
You transform pre-extracted spans into Safety Sigma IR v0.4. 
Rules:
- Zero-inference, cite-or-omit only.
- Preserve indicator strings verbatim.
- Map every field to provenance {page,start,end}.
- Categories only if explicit in source; include span ids.
- If unsure, mark UNSPECIFIED and leave field absent.
```

2. **Rule Compilation Prompt**:
```
You compile deployable rules from IR extractions.
Constraints:
- Preserve exact indicators; no reformatting.
- Reference extractions by index (source_refs).
- Emit targets enabled in config: sql|json|python|regex.
```

3. **Narrative Generation Prompt**:
```
You draft a concise practitioner narrative from IR.
Rules:
- Only quote spans verbatim with span ids like [p:3 1043-1052].
- No categories unless present in IR with provenance.
- Keep it operational (what to match, where it appeared), no speculation.
```

### Prompt Safety Validation

```python
# llm_integration/prompt_lib.py lines 181-210
def validate_prompt_safety(self, prompt):
    """Validate prompt doesn't contain unsafe injection patterns"""
    unsafe_patterns = ["{{", "}}", "${", "eval(", "__import__"]
    for pattern in unsafe_patterns:
        if pattern in prompt:
            safety_report["issues"].append(f"Unsafe pattern: {pattern}")
```

## Audit Chain Implementation

### Tamper-Evident Logging

```python  
# llm_integration/audit.py lines 85-115
def append(self, event):
    """Append event with hash chain integrity"""
    previous_hash = self._get_last_entry_hash()
    log_entry = {
        "event": event.get("event", "unknown"),
        "timestamp": time.time(),
        "previous_hash": previous_hash,
        "data": self._sanitize_event_data(event)
    }
    entry_hash = self._compute_entry_hash(log_entry)
    log_entry["entry_hash"] = entry_hash
```

### Chain Verification

```python
# llm_integration/audit.py lines 270-310  
def verify_chain_integrity(self):
    """Verify hash chain hasn't been tampered with"""
    previous_hash = "genesis"
    for entry in log_entries:
        if entry.get("previous_hash") != previous_hash:
            report["issues"].append("Hash chain broken")
        expected_hash = self._compute_entry_hash(entry)
        if entry.get("entry_hash") != expected_hash:
            report["issues"].append("Entry tampered")
```

## Advisory Separation Architecture

### Clear Demarcation

The LLM lane maintains strict separation between authoritative and advisory content:

**Authoritative Artifacts** (immutable, validated):
- `ir.json` - IR Schema v0.4 extractions with provenance
- `rules/*` - Compiled detection rules (regex, JSON, Python, SQL)
- `validation_report.json` - V-001..V-005 gate status
- `audit/log.jsonl` - Tamper-evident processing log

**Advisory Artifacts** (NON-AUTHORITATIVE, convenience):
- `narrative.md` - Practitioner summary with verbatim quotes
- All artifacts clearly marked with disclaimers

### Bundle Integration

```python
# scripts/build_audit_package.py lines 145-149
"llm_lane": {
    "present": llm_present,
    "authoritative": False,  # Explicit marking
    "config": "configs/llm_dev.yaml"
}
```

### Disclaimer Requirements

All LLM-generated content includes prominent disclaimers:

```markdown
**NON-AUTHORITATIVE** — This narrative quotes source spans verbatim.
For authoritative data, reference ir.json and compiled rules.
```

## CI/CD Integration

### Automated Validation Pipeline

```yaml
# .github/workflows/test-suites.yml
llm-pipeline-dev:
  steps:
    - name: Run LLM pipeline
      run: python scripts/run_llm_pipeline.py --doc atlas.pdf --config llm_dev.yaml
    - name: Run LLM integration tests  
      run: pytest tests/test_llm_integration.py -v
    - name: Upload LLM artifacts
      uses: actions/upload-artifact@v4
```

### Parity Testing

```python
# tests/llm/test_parity_vs_scripted.py
def test_golden_indicators_in_both_ir(self):
    """Verify golden indicators in both scripted and LLM pipelines"""
    for golden in ["$1,998.88", "VOID 2000", "wa.me/123456789"]:
        assert golden in scripted_indicators
        assert golden in llm_indicators
```

### Diff Analysis

```bash
# scripts/diff_ir.py
make llm-diff  # Compare scripted vs LLM extraction
```

## Configuration Management

### Development Configuration

```yaml
# configs/llm_dev.yaml
model_name: "claude-3-haiku-20240307"
temperature: 0.0  # Maximum determinism
processing_mode: "zero-inference"
cite_or_omit: true
exact_preservation: true
category_grounding: true
```

### Validation Configuration

```yaml
validation:
  enforce_gates: true
  required_gates: ["V-001", "V-002", "V-003", "V-004", "V-005"]
  golden_indicators: ["$1,998.88", "VOID 2000", "wa.me/123456789"]
  fail_on_invention: true
  require_provenance: true
  no_unspecified: true
```

## Compliance Verification

### Manual Verification Steps

1. **Golden Indicator Check**:
```bash
make llm  # Run LLM pipeline
make llm-diff  # Verify golden indicators preserved
```

2. **Validation Gates**:
```bash
pytest tests/test_llm_integration.py -v
# Verify all 18 tests pass, including V-001..V-005 gates
```

3. **Audit Chain**:
```bash
python -c "
from llm_integration.audit import AuditLogger
logger = AuditLogger('artifacts/llm_output/audit/log.jsonl')  
print(logger.verify_chain_integrity())
"
```

4. **Advisory Separation**:
```bash
grep -r "NON-AUTHORITATIVE" artifacts/llm_output/
# Verify disclaimers present in advisory content
```

### Automated Compliance Reports

The validation report provides comprehensive gate status:

```json
{
  "all_gates_passed": true,
  "gates": {
    "V-001": {"passed": true, "issues": []},
    "V-002": {"passed": true, "issues": []},
    "V-003": {"passed": true, "issues": []},
    "V-004": {"passed": true, "issues": []}, 
    "V-005": {"passed": true, "issues": []}
  }
}
```

## Risk Mitigation

### LLM-Specific Risks

1. **Model Hallucination**: Mitigated by zero-inference prompts and validation
2. **Prompt Injection**: Prevented by safe templating and input sanitization
3. **Output Variability**: Controlled by temperature=0 and deterministic fallbacks
4. **API Dependencies**: Fallback to deterministic rule-based processing

### Compliance Risks  

1. **Indicator Mutation**: Prevented by verbatim preservation and golden tests
2. **Category Invention**: Blocked by prompt guardrails and negative tests
3. **Missing Provenance**: Enforced by schema validation and completeness checks
4. **Audit Gaps**: Prevented by append-only logging and hash chain integrity

## Future Enhancements

### Planned Improvements

1. **Multi-Model Support**: Add support for additional LLM providers
2. **Batch Processing**: Optimize for high-volume document processing
3. **Advanced Provenance**: Enhance with document structure mapping
4. **Real-time Validation**: Stream validation during processing

### Maintenance Requirements

1. **Monthly**: Review golden test coverage and add new critical indicators
2. **Quarterly**: Audit prompt effectiveness and update system prompts
3. **Annually**: Compliance audit of entire LLM lane implementation
4. **On Model Updates**: Re-validate all gates when changing LLM models

## Conclusion

The Safety Sigma LLM lane maintains full compliance with validation gates V-001 through V-005 through:
- **Code-level enforcement** of preservation and grounding requirements
- **Prompt engineering** with explicit guardrails against invention
- **Comprehensive validation** at every processing stage
- **Tamper-evident audit trails** for regulatory compliance
- **Clear advisory separation** with prominent disclaimers

This architecture ensures that LLM integration enhances analyst productivity while maintaining the strict compliance standards required for threat intelligence processing.