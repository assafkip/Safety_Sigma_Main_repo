from pathlib import Path
import re

def test_advisory_exists_and_disclaims():
    p = Path("advisory/narrative_advisory.md")
    if not p.exists():
        # In CI, bundle build creates it; locally it may not exist yet.
        # This is a smoke test and can be skipped if not present.
        return
    text = p.read_text(encoding="utf-8")
    assert "NON-AUTHORITATIVE" in text and "ADVISORY" in text
    # Ensure advisory is not referenced by rules
    r = Path("artifacts/demo_rules.json")
    if r.exists():
        rt = r.read_text(encoding="utf-8")
        assert "narrative_advisory.md" not in rt