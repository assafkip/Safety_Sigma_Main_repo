# Behavioral Feedback & Memory v0.9

## Overview
Safety Sigma v0.9 introduces a cumulative, auditable knowledge base where every case/report enriches future analysis. Memory features preserve V-001..V-005 contract compliance for the scripted lane while adding advisory memory context.

## Memory Architecture

### Case Linkage
- **case_id/report_id**: All indicators and expansions carry identifiers linking them to originating cases
- **Cross-reference**: IR and EDAP expansions maintain bidirectional linkage for audit trails
- **Tolerance**: Fields are optional; missing IDs don't break processing

### Cumulative Reuse Index
- **Location**: `artifacts/memory/reuse_index.json`
- **Aggregation**: Patterns, domains, and behaviors accumulated across all prior cases
- **Metrics**: 
  - `count`: Total occurrences across cases
  - `cases`: List of case_ids where pattern appeared
  - `first_seen/last_seen`: Temporal tracking
  - `kinds`: Types of indicators (amount, domain, account, etc.)

### Report Metrics
- **duplication_saved**: Count of indicators already seen in prior cases
- **pattern_velocity_days**: Time delta between first and last occurrence
- **reuse_signals**: Per-pattern prior case counts for contextual analysis

## HTML Report Sections

### Living Knowledge Base
- **Purpose**: Show cumulative learning across all processed cases
- **Display**: Tabular view of patterns with occurrence counts and case references
- **Metrics**: Duplication rates, pattern velocity, cross-case linkage
- **Safety**: Advisory-only; does not influence authoritative outputs

### Reuse Signals
- **Integration**: Enhanced proactive/agentic sections show `prior_case_count`
- **Context**: Analysts see which patterns appeared in previous cases
- **Linkage**: Case IDs clickable/referenceable for investigation workflows

## Audit Log Enrichment
- **related_cases**: Hash-chained audit entries reference connected case_ids
- **memory.reuse_index**: Audit events track index updates and related counts
- **Provenance**: Full traceability from pattern → cases → audit decisions

## Implementation Constraints
- **V-001..V-005 Preservation**: Scripted lane remains authoritative and unmodified
- **Advisory Status**: All memory features are NON-AUTHORITATIVE
- **Storage**: Memory artifacts under `artifacts/memory/*` and `agentic/*`
- **Tolerance**: Missing memory data doesn't break core processing

## Acceptance Criteria
- [ ] Indicators carry case_id/report_id when available
- [ ] Reuse index aggregates patterns across multiple runs
- [ ] HTML shows "Living Knowledge Base" with prior-case counts
- [ ] Audit log references related_cases in hash chain
- [ ] Tests verify case linkage and memory indexing
- [ ] Make targets: `memory-index`, `report-v09`
- [ ] Advisory CI validates memory features without breaking builds