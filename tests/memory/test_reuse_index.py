import json
from pathlib import Path
from src.memory.reuse_index import build_or_update_index, _key_of

def test_key_of_function():
    """Test pattern key generation for different indicator types."""
    # Test verbatim value
    ind1 = {"kind": "domain", "verbatim": "paypaI.com"}
    assert _key_of(ind1) == "domain::paypaI.com"
    
    # Test literal value  
    ind2 = {"kind": "url", "literal": "https://evil.com"}
    assert _key_of(ind2) == "url::https://evil.com"
    
    # Test pattern value
    ind3 = {"kind": "pattern", "pattern": "VOID[ ]\\d{3,4}"}
    assert _key_of(ind3) == "pattern::VOID[ ]\\d{3,4}"
    
    # Test unknown kind
    ind4 = {"verbatim": "test"}
    assert _key_of(ind4) == "unknown::test"

def test_build_reuse_index(tmp_path: Path):
    """Test building reuse index from artifacts."""
    art = tmp_path/"artifacts"
    
    # Create demo_rules.json with indicators
    dr = art/"demo_rules.json"; dr.parent.mkdir(parents=True, exist_ok=True)
    dr.write_text(json.dumps({"indicators":[
      {"kind":"domain","verbatim":"paypaI.com","report_id":"R1","case_id":"C1"}
    ]}), encoding="utf-8")
    
    # Create proactive expansions
    exps = art/"proactive"/"expansions.json"; exps.parent.mkdir(parents=True, exist_ok=True)
    exps.write_text(json.dumps({"expansions":[
      {"kind":"domain_or_url","pattern":"paypaI\\.com","report_id":"R2","case_id":"C2"}
    ]}), encoding="utf-8")
    
    # Build index
    idx_path = build_or_update_index(tmp_path, case_id="C3")
    assert idx_path.exists()
    
    # Verify index contents
    idx = json.loads(Path(idx_path).read_text(encoding="utf-8"))
    items = idx["items"]
    
    # Should have entries for both domain patterns
    domain_key = "domain::paypaI.com"
    pattern_key = "pattern::paypaI\\.com"
    
    assert domain_key in items
    assert pattern_key in items
    
    # Check domain entry
    domain_rec = items[domain_key]
    assert domain_rec["count"] >= 1
    assert "C1" in domain_rec["cases"]
    assert "C3" in domain_rec["cases"]  # from case_id parameter
    
    # Check pattern entry  
    pattern_rec = items[pattern_key]
    assert pattern_rec["count"] >= 1
    assert "C2" in pattern_rec["cases"]

def test_index_updates_incrementally(tmp_path: Path):
    """Test that running build multiple times updates counts correctly."""
    art = tmp_path/"artifacts"
    dr = art/"demo_rules.json"; dr.parent.mkdir(parents=True, exist_ok=True)
    
    # First run
    dr.write_text(json.dumps({"indicators":[
      {"kind":"amount","verbatim":"$123","case_id":"C1"}
    ]}), encoding="utf-8")
    
    idx_path1 = build_or_update_index(tmp_path)
    idx1 = json.loads(Path(idx_path1).read_text(encoding="utf-8"))
    
    # Second run with same data should increment count
    idx_path2 = build_or_update_index(tmp_path)
    idx2 = json.loads(Path(idx_path2).read_text(encoding="utf-8"))
    
    key = "amount::$123"
    assert key in idx2["items"]
    
    # Count should be higher in second run
    assert idx2["items"][key]["count"] > idx1["items"][key]["count"]

def test_empty_artifacts_creates_empty_index(tmp_path: Path):
    """Test that build works even with no artifacts."""
    # Create empty artifacts directory
    (tmp_path/"artifacts").mkdir(parents=True, exist_ok=True)
    
    idx_path = build_or_update_index(tmp_path)
    assert idx_path.exists()
    
    idx = json.loads(Path(idx_path).read_text(encoding="utf-8"))
    assert idx["items"] == {}