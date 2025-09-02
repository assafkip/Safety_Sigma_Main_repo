# Privacy & Legal Note v0.1

## Data Processing Scope

Safety Sigma processes intelligence documents with the following constraints:

### What We Store
- **Literal spans only**: Exact text excerpts from supplied PDF documents
- **Source provenance**: Document references and span locations
- **Zero inference**: No actor identification, behavioral analysis, or ATT&CK mapping
- **Append-only audit trail**: All processing steps logged with timestamps

### What We Do NOT Store
- Personal identifying information (unless explicitly present in source documents)
- Inferred relationships beyond explicit textual links
- Normalized or enriched data from external sources
- Behavioral profiles or threat actor attribution

## Operator Responsibilities

### Document Redaction
- **Pre-processing redaction**: Operators must remove sensitive PII before processing
- **Source control**: Original documents remain under operator's data governance
- **Distribution control**: Generated bundles inherit sensitivity of source materials

### Data Retention
- **Audit bundles**: Self-contained with source material and processing logs
- **Local processing**: No external APIs or cloud services by default
- **Retention policy**: Determined by operator's security and compliance requirements

## Technical Safeguards

### Zero-Inference Processing
- Indicators preserved exactly as found in source text
- No normalization, stemming, or semantic enrichment
- Category assignments based solely on literal content patterns

### Audit Completeness
- Every extracted indicator includes source span references
- Processing provenance recorded for compliance verification
- Bundle manifest includes validation gate status (V-001 through V-005)

### Output Boundaries
- **Authoritative artifacts**: IR, rules, test results (immutable)
- **Advisory content**: Clearly marked as NON-AUTHORITATIVE convenience layer
- **Display presentation**: May clean formatting without altering underlying data

## Compliance Considerations

### Data Classification
- Generated bundles inherit classification level of source documents
- Advisory narratives maintain same sensitivity as authoritative artifacts
- Processing logs may contain metadata requiring equivalent protection

### Audit Requirements
- Complete processing chain documented in bundle manifest
- Validation tests provide evidence of preservation fidelity
- Append-only design supports forensic analysis requirements

### Legal Disclaimers
- **No warranty**: System provides extraction capabilities; accuracy depends on source quality
- **Operator responsibility**: Final validation and use decisions remain with operator
- **Zero inference**: System makes no claims about threat attribution or behavioral analysis

## Questions & Support

For privacy, legal, or compliance questions regarding Safety Sigma processing:
- Review bundle manifest for processing details
- Consult validation test results for fidelity evidence
- Contact system operators for data governance policies

---

**Document Version**: v0.1  
**Last Updated**: September 2025  
**Scope**: Covers Safety Sigma 2.0 zero-inference processing methodology