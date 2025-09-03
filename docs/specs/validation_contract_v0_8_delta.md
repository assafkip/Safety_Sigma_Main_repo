# Validation Contract Δ v0.8 — Agentic Gates

**A-801 Orchestrator Determinism (log)**: every step (inputs, decisions, outputs) appended to `agentic/audit.log.jsonl` with hash chain.

**A-802 Safe Actions**: only allowed writes are proposals under `proposals/`; scripted authoritative artifacts remain read-only.

**A-803 Escalation Policy**: proposals with `false_positive_rate >= POLICY.max_fpr` or `status != ready-deploy` MUST be escalated.

**A-804 Deployment Policy Compliance**: proposal marks `target_system` only if a matching adapter exists and compiles in dry-run.

**A-805 Privacy/Redaction Guard**: proposals must cite evidence spans/quotes; no new PII strings; redactions preserved.