# PRD Δ v0.8 — Agentic Workflows

## Goal
Automate Sigma's end-to-end pipeline with agents that **propose** actions (never enforce), reduce analyst toil, and accelerate prevention — while preserving the authoritative contract (V-001..V-005).

## Scope (In)
- Orchestrator agent: sequences lanes (scripted→LLM→proactive→backtest→adapter).
- Decision agents: triage EDAP expansions, select backtests/adapters, propose deployment PRs.
- Analyst-in-the-loop: approve/deny proposals with a single action list.
- Audit: full hash-chained logs of agent plans, inputs, outputs.

## Scope (Out)
- Autonomous production deployment without policy checks.
- Actor identity inference; ATT&CK mapping unless explicitly stated in source.

## New Agentic Gates (A-gates)
- **A-801 Orchestrator Determinism (log)** — run IDs, inputs, chosen steps, outcomes logged in hash chain.
- **A-802 Safe Actions** — agents may only read artifacts or write **proposals** (`proposals/*.json`), never overwrite authoritative `scripted/`.
- **A-803 Escalation Policy** — proposals beyond threshold (e.g., FP rate ≥ X) MUST be routed to analyst queue.
- **A-804 Deployment Policy Compliance** — proposals must satisfy adapter availability and local policy constraints.
- **A-805 Privacy/Redaction Guard** — no PII expansion beyond source; proposals must reference quotes/spans only.

## Acceptance
- Dry-run orchestrator produces: `agentic/run_<stamp>/{plan.json, decisions.json, proposals/*.json, audit.log.jsonl}`.
- Tests verify A-801..A-805; V-001..V-005 remain green (scripted lane unaffected).
- HTML includes "Agentic Plan (Advisory)" section summarizing proposals.

## Deliverables
- Docs: this PRD + validation deltas for A-gates.
- Code: `src/agentic/{orchestrator.py,actions.py,policy.py,audit.py}` + runner.
- Tests: `tests/agentic/test_agentic_workflow.py`.
- CI: non-blocking dry-run job.