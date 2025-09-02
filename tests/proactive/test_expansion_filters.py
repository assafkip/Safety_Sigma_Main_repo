from src.proactive.narrative_expander import extract_evidence, Evidence

def test_generic_tokens_are_filtered():
    s = [Evidence(sent_id="S1", text="Scheme involves apps, payments, transfers.", spans=["s1"])]
    exps = extract_evidence(s)
    bad = [e for e in exps if e.pattern.lower() in {"apps","payments","transfers"}]
    assert not bad, "Generic tokens must be filtered at generation time"