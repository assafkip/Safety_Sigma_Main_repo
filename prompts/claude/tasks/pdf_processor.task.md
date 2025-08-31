# Task: Implement pdf_processor v0.1 to pass golden tests
## Inputs
- PRD: docs/specs/pdf_processor_PRD_v0.1.md
- Golden tests: tests/golden_cases/*
## Deliverables
- src/pdf_processor/ingest.py (pdf_to_text_with_offsets)
- src/pdf_processor/extract.py (extract_amounts, extract_memos, extract_links, extract_categories)
- src/pdf_processor/ir.py (to_ir_objects)
- src/pdf_processor/rules.py (compile_rules)
- src/pdf_processor/audit.py (append_jsonl)
- tests/unit/test_pdf_processor_ir.py (covers C-001..C-003)
- Update tests/golden_cases/test_indicators.py to call real functions
## Acceptance
- CI: G-001..G-003, G-010 pass (pytest). :contentReference[oaicite:23]{index=23}
- IR objects meet C-001..C-003. :contentReference[oaicite:24]{index=24}
- Audit row exists and includes spans/decisions/scores. :contentReference[oaicite:25]{index=25}:contentReference[oaicite:26]{index=26}
- Minimal rule executes in harness (V-004). :contentReference[oaicite:27]{index=27}
