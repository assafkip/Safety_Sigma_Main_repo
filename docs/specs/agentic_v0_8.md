# PRD Δ v0.8 — Agentic Workflows (Feedback-Driven)

## Goal
Automate Sigma's end-to-end pipeline with advisory agents that reduce analyst toil and accelerate prevention, **without** altering authoritative artifacts or weakening V-gates.

## Scope (In)
- Orchestrator agent: sequences scripted → LLM → proactive (EDAP) → backtest → adapter → sharing (dry-runs).
- Decision agents:
  - Confidence-based promotion: mark expansions `ready-deploy` when FPR ≤ policy.max_fpr AND EDAP justification is strong.
  - Escalation: route `ready-review` or high-FPR items to analyst queue with rationale.
- Behavioral context: if present (velocity/IP/account age), include in proposals and scoring.
- Outputs: agentic/run_<stamp>/{plan.json, decisions.json, proposals/*.json, audit.log.jsonl (hash-chained)}

## Scope (Out)
- Autonomous production deployment without human policy checks.
- Actor identity inference; ATT&CK mapping unless cited explicitly.

## A-Gates (Agentic)
- **A-801 Orchestrator Determinism & Logging:** Every step must be appended to a hash-chained JSONL audit log.
- **A-802 Safe Actions Only:** Agents can only read artifacts and write proposals under agentic/; no writes to authoritative scripted/.
- **A-803 Escalation Policy:** Items with FPR > policy.max_fpr OR missing strong justification → `ready-review`.
- **A-804 Deployment Policy Compliance:** Proposals can claim target_system only if matching adapter exists and dry-run compiles.
- **A-805 Privacy/Redaction Guard:** Proposals must reference evidence spans/quotes; no novel PII; redactions preserved.

## Acceptance
- Dry-run produces agentic/run_<stamp>/ with plan/decisions/proposals and audit.log.jsonl (hash chaining).
- HTML report shows "Agentic Plan (Advisory)" summarizing proposals & escalations.
- A-gates pass; V-001..V-005 remain green.