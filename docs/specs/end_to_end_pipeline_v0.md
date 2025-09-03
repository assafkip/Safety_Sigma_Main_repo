# End-to-End Pipeline (v0)

**Goal:** Make the entire journey from intel → IR → rules → proactive expansions → backtesting → deployment adapters → cross-company sharing explicit and testable.

## Stages (and primary artifacts)
1. **Ingest (PDF/Text)** → `raw_text.txt`, metadata
2. **IR Extraction (scripted, authoritative)** → `ir.json` (verbatim spans, provenance, grounded categories)
3. **Rule Compilation (scripted, authoritative)** → `rules.json` (regex/SQL/JSON), `report.html`
4. **LLM Lane (advisory)** → `llm_output/{ir.json, narrative.md, rules.json, validation_report.json}`
5. **Proactive Lane (EDAP, advisory)** → `proactive/expansions.json` (operator, parent_spans, evidence_quote, status)
6. **Backtesting (metrics)** → `proactive/backtest_report.json` (samples_tested, FPR, TPR)
7. **Deployment Adapters (target-specific)** → `adapters/<target>/rule_files/*` (generated), logs
8. **Sharing (bundle packaging)** → `audit_package_vX.Y.zip` (lanes, manifest, README), signature

## Gates & Invariants (binding vs advisory)
- **V-001..V-005 (binding)** apply to scripted lane only.
- **P-001..P-004 (advisory)** apply to Proactive EDAP.
- **V-006 (new, advisory→binding over time):** Deployment Readiness (at least one adapter compiles rules without loss).
- **V-007 (new, advisory):** Sharing Integrity (bundle completeness, signatures, importability).

## RACI (who owns what)
- Scripted Lane: Eng owns; Analyst reviews findings.
- LLM Lane: Eng owns prompts/validators; Analyst consumes narrative.
- Proactive EDAP: Eng owns operators/filters; Analyst approves policy to deploy per metrics.
- Backtesting: Eng owns harness; SecEng signs off thresholds.
- Adapters: Eng creates; Customer Eng/SE validates in target systems.
- Sharing: Eng packages; Customer/Partner imports and validates.

## Evidence per stage
- Ingest → raw text, offsets
- IR → span IDs, page/offsets
- Rules → regex list + example matches
- LLM → JSON+hash-chained audit log
- EDAP → evidence quotes + operator tags
- Backtest → CSV inputs + summary metrics
- Adapter → generated rule files + compile logs
- Sharing → manifest + README + (optional) signature

## Acceptance checklists (fast)
- Scripted lane: V-001..V-005 ✅
- EDAP: operator + quote + status + (FPR/TPR if available)
- Backtest: `backtest_report.json` present; rates summarised in HTML
- Adapter: generated config exists; test command provided
- Sharing: bundle zip contains all lanes; manifest `lanes.*.authoritative` set; README present