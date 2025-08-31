> **Authority note**: Binding rules live in the spec vault:
> - Guardrails (zero-inference, exact preservation, dual audience): Safety-Sigma-Docs/policy/guardrails.md:contentReference[oaicite:0]{index=0}
> - Golden tests (G-001..G-003, G-010): Safety-Sigma-Docs/tests/golden_cases.md:contentReference[oaicite:1]{index=1}
> - Validation contract (gates V-001..V-005): Safety-Sigma-Docs/validation/contract.md:contentReference[oaicite:2]{index=2}
> This file is **operational**: how to prove compliance in CI.


Purpose

Define the golden test harness and acceptance gates for pdf_processor.

Golden Tests

G-001 Amount exactness — $1,998.88 must be preserved verbatim in IR value and compiled rules.

G-002 Memo preservation — VOID 2000 must remain intact.

G-003 Link literal — wa.me/123456789 must be captured exactly; regex: \bwa\.me/[0-9]{6,}\b.

G-010 Category check — No category may appear unless explicitly in source (diff == ∅).

Acceptance Gates

V-001: G-001..G-003 pass.

V-002: G-010 passes.

V-003: Every output has provenance + spans + decisions.

V-004: Rules execute on sample DB/harness.

V-005: Exec checklist completed; no UNSPECIFIED items.

How to Run
pytest tests/golden_cases/ --junitxml=results/golden.xml


Outputs are compared against fixtures in tests/fixtures/. CI must fail if any gate fails.
