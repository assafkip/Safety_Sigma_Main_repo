import json, re, pytest
from src.pdf_processor.rules import compile_rules, CompileOptions, RuleCompileError

@pytest.fixture
def ir_rich():
    # Minimal IR with new literal types; all strings must be preserved exactly.
    return {
        "indicators": [
            {"kind":"amount","verbatim":"$1,998.88","numeric":1998.88,"category_id":"financial","span_id":"s_amt"},
            {"kind":"text","verbatim":"VOID 2000","category_id":"memo","span_id":"s_void"},
            {"kind":"link","literal":"wa.me/123456789","category_id":"comm","span_id":"s_link"},
            {"kind":"domain","verbatim":"irs-help.com","category_id":"infra","span_id":"s_dom"},
            {"kind":"phone","verbatim":"+1-800-123-4567","category_id":"contact","span_id":"s_phone"},
            {"kind":"email","verbatim":"support@imf-aid.org","category_id":"contact","span_id":"s_mail"},
            {"kind":"account","verbatim":"Zelle ID 123456789","category_id":"financial","span_id":"s_zelle"},
            {"kind":"behavior","verbatim":"redirected to WhatsApp","category_id":"tactic","span_id":"s_beh"},
        ],
        "categories": {"financial":{}, "memo":{}, "comm":{}, "infra":{}, "contact":{}, "tactic":{}},
        # Optional explicit link: amount ↔ account (same sentence in real doc)
        "links":[{"from":"s_amt","to":"s_zelle","type":"co_occurs"}]
    }

def test_g040_g041_g042_g043_exact_preservation(ir_rich):
    arts = compile_rules(ir_rich, CompileOptions(targets=["regex","sql","json"]))
    rows = arts["sql"]["rows"]
    # Exact domain, phone, email, behavior preserved in SQL rows or JSON indicators
    expect = {
        "irs-help.com": any(r.get("verbatim")=="irs-help.com" for r in rows),
        "+1-800-123-4567": any(r.get("verbatim")=="+1-800-123-4567" for r in rows),
        "support@imf-aid.org": any(r.get("verbatim")=="support@imf-aid.org" for r in rows),
        "redirected to WhatsApp": any(r.get("verbatim")=="redirected to WhatsApp" for r in rows),
    }
    assert all(expect.values()), f"Missing preserved literals: { [k for k,v in expect.items() if not v] }"

def test_category_diff_is_empty(ir_rich):
    compiled_cats = set(compile_rules(ir_rich, CompileOptions(targets=["json"]))["json"]["categories"].keys())
    assert compiled_cats == set(ir_rich["categories"].keys())

def test_regex_exactness(ir_rich):
    arts = compile_rules(ir_rich, CompileOptions(targets=["regex"]))
    pats = { (r["meta"]["name"], r["pattern"]) for r in arts["regex"] }
    def has(name, s): return any(n==name and re.search(p, name) for n,p in pats)
    assert has("irs-help.com", "irs-help.com")
    assert has("+1-800-123-4567", "+1-800-123-4567")
    assert has("support@imf-aid.org", "support@imf-aid.org")
    assert has("redirected to WhatsApp", "redirected to WhatsApp")

def test_g044_links_optional_and_literal(ir_rich):
    arts = compile_rules(ir_rich, CompileOptions(targets=["json"]))
    j = arts["json"]
    # If links are carried through, they must reference existing span_ids
    links = j.get("links", [])
    for ln in links:
        assert ln.get("from") in {i["span_id"] for i in j.get("indicators", [])}
        assert ln.get("to")   in {i["span_id"] for i in j.get("indicators", [])}