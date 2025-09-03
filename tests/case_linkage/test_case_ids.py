import json
from pathlib import Path

def test_indicators_carry_report_and_case(tmp_path: Path):
    """Test that indicators can carry case and report IDs."""
    dr = tmp_path/"artifacts"/"demo_rules.json"
    dr.parent.mkdir(parents=True, exist_ok=True)
    data = {"indicators":[
      {"kind":"amount","verbatim":"$1,998.88","category_id":"fin","span_id":"s1","report_id":"R1","case_id":"C123"}
    ]}
    dr.write_text(json.dumps(data), encoding="utf-8")
    got = json.loads(dr.read_text(encoding="utf-8"))
    i = got["indicators"][0]
    assert i["report_id"]=="R1" and i["case_id"]=="C123"

def test_normalize_indicator():
    """Test indicator normalization with case/behavioral fields."""
    from src.pdf_processor.ir import normalize_indicator
    
    # Valid case
    valid = {"kind": "amount", "verbatim": "$123", "report_id": "R1", "case_id": "C1", "ip_reputation": "high"}
    result = normalize_indicator(valid)
    assert result["report_id"] == "R1"
    assert result["case_id"] == "C1"
    assert result["ip_reputation"] == "high"
    
    # Invalid ip_reputation should be removed
    invalid_ip = {"kind": "amount", "verbatim": "$123", "ip_reputation": "invalid"}
    result = normalize_indicator(invalid_ip)
    assert "ip_reputation" not in result
    
    # Non-string case_id should be removed
    invalid_case = {"kind": "amount", "verbatim": "$123", "case_id": 123}
    result = normalize_indicator(invalid_case)
    assert "case_id" not in result

def test_indicators_with_ids():
    """Test indicator enrichment with case/report IDs."""
    from src.pdf_processor.ir import indicators_with_ids
    
    indicators = [
        {"kind": "amount", "verbatim": "$123"},
        {"kind": "domain", "verbatim": "evil.com", "report_id": "existing"}
    ]
    
    enriched = list(indicators_with_ids(indicators, report_id="R1", case_id="C1"))
    
    # First indicator should get both IDs
    assert enriched[0]["report_id"] == "R1"
    assert enriched[0]["case_id"] == "C1"
    
    # Second indicator should keep existing report_id, add case_id
    assert enriched[1]["report_id"] == "existing"
    assert enriched[1]["case_id"] == "C1"