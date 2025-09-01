import re
import pytest

from src.pdf_processor.rules import compile_rules, CompileOptions, RuleCompileError

@pytest.fixture
def sample_ir():
    # Minimal IR slice; must preserve exact indicators and category grounding
    return {
        "extractions": [],
        "indicators": [
            {
                "kind": "amount",
                "verbatim": "$1,998.88",
                "numeric": 1998.88,
                "category_id": "payments",
                "span_id": "s_amt",
            },
            {
                "kind": "link",
                "literal": "wa.me/123456789",
                "category_id": "comm",
                "span_id": "s_link",
            },
            {
                "kind": "text",
                "verbatim": "VOID 2000",
                "category_id": "fraud_marker",
                "span_id": "s_void",
            },
        ],
        "categories": {
            "payments": {"spans": ["s_amt"]},
            "comm": {"spans": ["s_link"]},
            "fraud_marker": {"spans": ["s_void"]},
        },
    }

def _find_regex_pattern(artifacts, needle):
    for r in artifacts.get("regex", []):
        if r.get("pattern") and needle in r.get("pattern"):
            return r.get("pattern")
    return None

def test_amount_preservation_regex_sql_json(sample_ir):
    arts = compile_rules(sample_ir, CompileOptions(targets=["regex","sql","json"]))
    # regex literal escape must match exact amount
    pat = _find_regex_pattern(arts, "$1,998.88")
    assert pat is not None
    assert re.search(pat, "$1,998.88")

    # sql rows preserve verbatim + numeric + span refs
    rows = arts.get("sql", {}).get("rows", [])
    amt_rows = [r for r in rows if r.get("kind") == "amount"]
    assert amt_rows, "expected amount row"
    amt = amt_rows[0]
    assert amt["verbatim"] == "$1,998.88"
    assert amt["numeric"] == 1998.88
    assert amt["category_id"] == "payments" and amt["span_id"] == "s_amt"

    # json mirrors indicators
    j_amt = [i for i in arts.get("json", {}).get("indicators", []) if i.get("kind")=="amount"][0]
    assert j_amt["verbatim"] == "$1,998.88" and j_amt["numeric"] == 1998.88

def test_link_literal_preservation(sample_ir):
    arts = compile_rules(sample_ir, CompileOptions(targets=["regex","sql","json"]))
    pat = _find_regex_pattern(arts, "wa.me/123456789")
    assert pat is not None
    assert re.search(pat, "wa.me/123456789")
    assert not re.search(pat, "wa.me/1234567890")  # no accidental overmatch

    rows = arts.get("sql", {}).get("rows", [])
    link = [r for r in rows if r.get("kind") == "link"][0]
    assert link["literal"] == "wa.me/123456789"

def test_category_diff_and_void_exact(sample_ir):
    arts = compile_rules(sample_ir, CompileOptions(targets=["regex","json"]))
    compiled_cats = set(arts.get("json", {}).get("categories", {}).keys())
    assert compiled_cats == {"payments", "comm", "fraud_marker"}  # diff == ∅

    pat = _find_regex_pattern(arts, "VOID 2000")
    assert pat is not None
    assert re.search(pat, "VOID 2000")
    assert not re.search(pat, "VOID 20000")

def test_missing_fields_raise(sample_ir):
    bad = dict(sample_ir)
    bad["indicators"] = [
        {"kind": "amount", "verbatim": "$1,998.88", "category_id": "payments", "span_id": "s_amt"}  # numeric missing
    ]
    with pytest.raises((RuleCompileError, AssertionError, KeyError, ValueError)):
        compile_rules(bad, CompileOptions(targets=["sql"]))