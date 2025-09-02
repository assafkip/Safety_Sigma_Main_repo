# PRD Δ v0.5 — Backtesting, Smarter EDAP, Behavioral Context

## Purpose
Add automated backtesting metrics, robust EDAP filtering/justification, and initial behavioral context operators — while preserving the authoritative validation contract (V-001..V-005). 

## New/Changed Requirements
A-501 (MUST) Backtesting Metrics:
- Each EDAP expansion marked `ready` MUST include: samples_tested, false_positive_rate (FPR), true_positive_rate (TPR).
- Bundle: proactive/backtest_report.json and HTML summary.

A-502 (MUST) Smarter EDAP Filtering:
- Drop generic ALT_ENUM tokens (e.g., "apps", "payments", "transfers") at generation time.
- Each expansion MUST show inline justification: Operator + Evidence Quote + Sentence ID.

A-503 (SHOULD) Behavioral Context (initial):
- Support optional behavioral fields: ip_reputation (low|med|high), velocity_event_count (int), account_age_days (int).
- Allow display and rule composition examples in HTML (advisory), without changing authoritative schema doc yet.

A-504 (MUST) Compliance:
- Scripted lane continues to satisfy V-001..V-005. Proactive/LLM stay NON-AUTHORITATIVE.

## Acceptance
- Backtest metrics appear per expansion in JSON + HTML.
- No generic EDAP tokens in expansions; each entry shows operator + evidence quote.
- Behavioral fields render in HTML "Behavioral Context" (advisory), without breaking existing tests.