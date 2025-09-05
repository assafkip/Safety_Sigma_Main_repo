# PRD v1.0 — Pilot Readiness

## Purpose
Make advisory outputs deployable in a limited pilot: metrics on every signal, confidence scoring, risk-tier thresholds, explicit field mappings, analyst feedback loop, and governance/SLAs.

## Scope (In)
- Backtesting coverage for all advisory signals (FP/TP/samples).
- Confidence scoring per signal; display in HTML + adapters.
- Risk-tier thresholds (blocking/hunting/enrichment) in policy YAML.
- Metadata: severity_label, rule_owner, detection_type, sla, staleness_days, log_field_targets.
- Analyst feedback loop (approve/reject/tune) persisted & rendered.
- Governance: decision tree + escalation timers in HTML & bundle.

## Acceptance
- No advisory item leaves the system without metrics, confidence, and tier.
- Agentic `ready-deploy` requires grounded=YES and meets tier threshold.
- Field mappings explicit for Splunk/Elastic/SQL.
- Feedback/audit history visible; staleness warnings visible.