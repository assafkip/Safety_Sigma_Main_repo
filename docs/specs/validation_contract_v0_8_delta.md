# Validation Contract Δ v0.8 — Agentic Gates

- A-801: Hash-chained log present; entries for load, decide, propose, write.
- A-802: No writes to authoritative directories; proposals only under agentic/.
- A-803: Proposals include confidence (FPR/TPR) & justification; escalate if FPR > max_fpr or justification weak.
- A-804: If proposal references target_system, adapter compile dry-run must succeed.
- A-805: All proposals reference evidence spans/quotes; no unquoted PII; redactions intact.