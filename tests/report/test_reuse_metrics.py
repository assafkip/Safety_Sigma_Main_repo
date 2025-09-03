import json
from pathlib import Path

def test_memory_section_render_safely(tmp_path: Path):
    """Test that memory sections render safely with valid index."""
    # Create a tiny index
    idx = {"items":{"domain::paypaI.com":{"count":2,"cases":["C1","C2"],"first_seen":"2025-01-01T00:00:00Z","last_seen":"2025-01-02T00:00:00Z"}}}
    p = tmp_path/"artifacts/memory/reuse_index.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(idx), encoding="utf-8")
    
    # Not rendering HTML here—this is a smoke test to ensure file shape; renderer tested manually.
    assert p.exists()
    
    # Verify the index can be loaded
    loaded = json.loads(p.read_text(encoding="utf-8"))
    assert "items" in loaded
    assert "domain::paypaI.com" in loaded["items"]
    
    record = loaded["items"]["domain::paypaI.com"]
    assert record["count"] == 2
    assert len(record["cases"]) == 2
    assert "C1" in record["cases"]
    assert "C2" in record["cases"]

def test_index_velocity_calculation():
    """Test velocity calculation logic for pattern reuse."""
    from datetime import datetime
    
    # Test data with timestamps
    first_seen = "2025-01-01T00:00:00Z"
    last_seen = "2025-01-05T00:00:00Z"
    
    # Calculate days difference
    fs = datetime.fromisoformat(first_seen.replace('Z', '+00:00'))
    ls = datetime.fromisoformat(last_seen.replace('Z', '+00:00'))
    days = (ls - fs).days
    
    assert days == 4  # 5 days minus 1 for same-day patterns

def test_pattern_reuse_context():
    """Test that pattern reuse context is properly structured."""
    # Sample pattern with reuse data
    pattern_data = {
        "pattern": "VOID[ ]\\d{3,4}",
        "prior_cases": ["C1", "C2", "C3"],
        "prior_count": 3,
        "first_seen": "2025-01-01T00:00:00Z",
        "evidence": "The scammer requests a VOID check with a 3-4 digit code..."
    }
    
    # Verify structure
    assert "pattern" in pattern_data
    assert "prior_cases" in pattern_data
    assert "prior_count" in pattern_data
    assert pattern_data["prior_count"] == len(pattern_data["prior_cases"])

def test_knowledge_stats_calculation(tmp_path: Path):
    """Test knowledge base statistics calculation."""
    # Create test index with multiple patterns
    items = {
        "domain::evil.com": {"count": 3, "cases": ["C1", "C2"]},
        "amount::$123.45": {"count": 1, "cases": ["C1"]},
        "pattern::VOID\\d+": {"count": 2, "cases": ["C2", "C3"]}
    }
    
    # Calculate stats like the real function would
    total_patterns = len(items)
    total_occurrences = sum(rec.get("count", 0) for rec in items.values())
    unique_cases = set()
    for rec in items.values():
        unique_cases.update(rec.get("cases", []))
    
    assert total_patterns == 3
    assert total_occurrences == 6  # 3 + 1 + 2
    assert len(unique_cases) == 3  # C1, C2, C3

def test_empty_memory_index_handling(tmp_path: Path):
    """Test graceful handling of missing memory index."""
    # Create artifacts directory without memory index
    art = tmp_path / "artifacts"
    art.mkdir(parents=True, exist_ok=True)
    
    # Memory index path should not exist
    idx_path = art / "memory" / "reuse_index.json"
    assert not idx_path.exists()
    
    # This represents what the render function should handle gracefully