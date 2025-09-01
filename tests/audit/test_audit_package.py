# tests/audit/test_audit_package.py
import pytest
import json
from pathlib import Path

# Assume compile_rules + IR generator already exist
from src.pdf_processor.rules import compile_rules, CompileOptions
from src.pdf_processor import ir

GOLDEN_INPUT = {
    "extractions": [
        {"type": "amount", "value": "$1,998.88", "norm": {"amount": 1998.88},
         "provenance": {"page": 1, "start": 10, "end": 20}, "category_id": "payments", "span_id": "s1"},
        {"type": "memo", "value": "VOID 2000",
         "provenance": {"page": 1, "start": 30, "end": 39}, "category_id": "fraud_marker", "span_id": "s2"},
        {"type": "link", "value": "wa.me/123456789",
         "provenance": {"page": 2, "start": 5, "end": 20}, "category_id": "comm", "span_id": "s3"},
    ],
    "categories": {"payments": {}, "fraud_marker": {}, "comm": {}},
}

def test_audit_package_acceptance(tmp_path):
    # Step 1: Compile rules
    artifacts = compile_rules(GOLDEN_INPUT, CompileOptions(targets=["regex","sql","json"]))

    # V-001 Indicator preservation
    sql_rows = artifacts["sql"]["rows"]
    assert any(r.get("verbatim") == "$1,998.88" and r.get("numeric") == 1998.88 for r in sql_rows)
    assert any(r.get("verbatim") == "VOID 2000" for r in sql_rows if r.get("kind") == "memo")
    assert any(r.get("literal") == "wa.me/123456789" for r in sql_rows if r.get("kind") == "link")

    # V-002 Category grounding
    compiled_cats = set(artifacts["json"]["categories"].keys())
    source_cats = set(GOLDEN_INPUT["categories"].keys())
    assert compiled_cats == source_cats

    # V-003 Audit completeness: every row has provenance fields
    for row in sql_rows:
        assert "category_id" in row and "span_id" in row

    # V-004 Practitioner readiness: regex rules actually match originals
    regex_rules = artifacts["regex"]
    values = [e["value"] for e in GOLDEN_INPUT["extractions"]]
    for rr in regex_rules:
        pat = rr["pattern"]
        assert any(val for val in values if __import__("re").search(pat, val))

    # V-005 Exec guarantees: no UNSPECIFIED fields
    json_text = json.dumps(artifacts)
    assert "UNSPECIFIED" not in json_text
