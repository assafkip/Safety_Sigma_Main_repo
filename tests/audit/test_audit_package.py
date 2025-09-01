import json
import re
from pathlib import Path

import pytest
from src.pdf_processor.rules import compile_rules, CompileOptions

GOLDEN_INPUT = {
    "extractions": [],
    "indicators": [
        {"kind":"amount","verbatim":"$1,998.88","numeric":1998.88,"category_id":"payments","span_id":"s1"},
        {"kind":"text","verbatim":"VOID 2000","category_id":"fraud_marker","span_id":"s2"},
        {"kind":"link","literal":"wa.me/123456789","category_id":"comm","span_id":"s3"},
    ],
    "categories":{"payments":{},"fraud_marker":{},"comm":{}},
}

def test_audit_package_acceptance(tmp_path):
    arts = compile_rules(GOLDEN_INPUT, CompileOptions(targets=["regex","sql","json"]))

    # V-001: indicator preservation (amount/link/memo exact)
    rows = arts["sql"]["rows"]
    assert any(r.get("verbatim")=="$1,998.88" and r.get("numeric")==1998.88 for r in rows)
    assert any(r.get("verbatim")=="VOID 2000" for r in rows if r.get("kind")=="text")
    assert any(r.get("literal")=="wa.me/123456789" for r in rows if r.get("kind")=="link")

    # V-002: category diff == ∅
    compiled_cats = set(arts["json"]["categories"].keys())
    assert compiled_cats == {"payments","fraud_marker","comm"}

    # V-003: audit completeness (span refs present on compiled rows)
    for r in rows:
        assert "category_id" in r and "span_id" in r

    # V-004: practitioner readiness (regex matches originals)
    vals = ["$1,998.88","VOID 2000","wa.me/123456789"]
    for rr in arts["regex"]:
        assert any(re.search(rr["pattern"], v) for v in vals)

    # V-005: no UNSPECIFIED outputs
    assert "UNSPECIFIED" not in json.dumps(arts)