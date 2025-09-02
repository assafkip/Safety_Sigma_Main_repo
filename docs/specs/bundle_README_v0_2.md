# Safety Sigma — Audit Package v0.2 (Dual-Lane)

This bundle contains **two parallel extraction lanes** from the same source report:

- **Scripted lane (authoritative):** deterministic extractor → IR → deployable rules.
- **LLM lane (advisory):** faster context + narrative; **NON-AUTHORITATIVE**.

Only the **scripted lane** satisfies the compliance gates. The LLM lane is included for analyst speed and context.

---

## Bundle Layout

```
/
├─ manifest.json                       # bundle metadata + gate status + lanes section
├─ scripted/                          # AUTHORITATIVE artifacts
│  ├─ rules.json                      # source-grounded IR (verbatim spans, provenance)
│  └─ report.html                     # human view over authoritative indicators/rules
├─ llm_output/                        # NON-AUTHORITATIVE lane (advisory)
│  ├─ ir.json                         # LLM-structured IR (validated for literal spans)
│  ├─ rules/                          # compiled rules from LLM IR (advisory)
│  ├─ narrative.md                    # advisory narrative with quoted spans
│  ├─ validation_report.json          # LLM-lane self-checks
│  └─ audit/log.jsonl                 # tamper-evident hash-chained log
├─ advisory/                          # optional extra narrative/sources (advisory)
│  ├─ narrative_advisory.md
│  └─ sources.json
├─ tests/                             # JUnit reports (if present)
│  ├─ junit_golden.xml
│  ├─ junit_unit.xml
│  └─ junit_audit.xml
└─ docs/ops/privacy_legal_note_v0.1.md
```

**Authority flags** live in `manifest.json` → `lanes.scripted.authoritative: true`, `lanes.llm.authoritative: false`.

---

## What "authoritative" means here

- Indicators are **verbatim** from the source.
- Categories appear **only** if the source explicitly contains them (no inventions).
- Every record carries **provenance** (doc/page/offset/span_id).
- Rules are **deployable** (regex/SQL/JSON) and traced back to spans.

The LLM lane must **never** override or be used to satisfy gates; treat it as analyst assistance.

---

## Validation Gates (V-001..V-005)

| Gate  | What it asserts                                  | Where to verify (authoritative)                              |
|-------|---------------------------------------------------|--------------------------------------------------------------|
| V-001 | Exact indicator preservation                     | `tests/junit_golden.xml`, `scripted/rules.json`            |
| V-002 | Category grounding (diff == ∅)                   | `tests/junit_golden.xml`, `scripted/rules.json`            |
| V-003 | Audit completeness (provenance + spans)          | `scripted/rules.json`, `manifest.json`                     |
| V-004 | Practitioner readiness (rules execute)           | `scripted/rules.json`, `tests/junit_unit.xml`              |
| V-005 | Exec guarantees (no `UNSPECIFIED`, checklist)    | `manifest.json`, test results, `docs/ops/` note            |

> **Note**: LLM artifacts are **advisory**. They can be inspected, but they do **not** satisfy the gates.

---

## Quick Verify (local)

From the repo root (or any shell with Python):

```bash
# 1) Check bundle manifest & lanes
jq '.lanes' manifest.json

# 2) Inspect authoritative IR + a few rows
jq '.json.indicators[:5]' scripted/rules.json | sed -n '1,60p'
head -n 60 scripted/report.html

# 3) Sanity: no UNSPECIFIED in authoritative artifacts
! grep -R "UNSPECIFIED" scripted || echo "UNSPECIFIED FOUND"

# 4) Golden parity across lanes (spot check)
# These three MUST appear in both lanes exactly, if present in your source:
#   $1,998.88  |  VOID 2000  |  wa.me/123456789
grep -R "\$1,998\.88\|VOID 2000\|wa\.me/123456789" scripted llm_output || true
```

If your CI artifacts include JUnit XMLs, open `tests/junit_*.xml` to confirm test pass counts.

### Rerun Parity (if repo is available)

```bash
# Compare scripted vs LLM indicators
python scripts/diff_ir.py --scripted scripted/rules.json --llm llm_output/ir.json
```

You should see no loss of golden indicators in the LLM lane. Differences outside goldens are allowed but advisory.

---

## How to Use

**Practitioners**: take rules from `scripted/rules.json`. If LLM rules look useful, treat them as drafts; validate before deploy.

**Analysts**: read `scripted/report.html` for the authoritative view; use `llm_output/narrative.md` as a NON-AUTHORITATIVE guide.

**Auditors/Exec**: rely on `manifest.json`, `scripted/rules.json`, and JUnit files to confirm all gates are satisfied.

---

## Privacy / Legal

See `docs/ops/privacy_legal_note_v0.1.md`. This bundle stores only literal spans from the provided documents, with optional redaction by the operator. No actor inference or external enrichment is included.

---

## Questions

**"Why two lanes?"** — Scripted lane guarantees compliance and reproducibility. LLM lane accelerates analysis but never drives validation.

**"What if lanes disagree?"** — Trust scripted. Use `scripts/diff_ir.py` to review differences and update the LLM prompts or config, not the authority model.

---

## Acceptance checks
- README present at bundle root after build (`bundle/README.md` or included in `artifacts/audit_package_v0_2/README.md` depending on your bundler path).
- References to lanes and gates match your `manifest.json`.
- No changes to authoritative artifacts or tests; **all V-001..V-005 remain green**.

---

Generated by Safety Sigma v2.0 | Analyst Readiness Enhanced