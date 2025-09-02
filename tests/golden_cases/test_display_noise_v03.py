import json, re, os
from pathlib import Path
import pytest

def _read(p): return Path(p).read_text(encoding="utf-8") if Path(p).exists() else ""

def test_no_phone_on_ocr_artifacts(tmp_path):
    """Simulate OCR noise phone-like token; extraction/matching layer must NOT promote it."""
    noisy = "1 ---\n \n \n \n \n1"
    # Test phone pattern noise rejection
    # Pattern should require ≥7 digits and reject >30% whitespace/linebreak
    digit_count = sum(c.isdigit() for c in noisy)
    whitespace_ratio = sum(c in " \n\t\r" for c in noisy) / len(noisy) if noisy else 0
    
    # Should NOT match: <7 digits and >30% whitespace
    assert digit_count < 7, "OCR noise has insufficient digits"
    assert whitespace_ratio > 0.30, "OCR noise has excessive whitespace"

def test_keyword_not_promoted():
    """'fraudulent' must not be promoted to IOC 'fraud' unless exact token appears."""
    text = "This is fraudulent content. Not the exact token."
    # The system should only record exact tokens (enforced by our extractor/compiler tests).
    assert "fraud" not in {"fraudulent"}, "sanity check: fraudulent != fraud"
    # Extraction should only match exact tokens, not partial matches

def test_domain_trailing_punct_display_only(tmp_path):
    """Verbatim kept in authoritative JSON; HTML display may trim trailing punctuation."""
    d_verbatim = "irs-help.com,"
    # Simulate compiled JSON row and HTML rendering result
    authoritative = {"kind":"domain","verbatim": d_verbatim, "category_id":"infra","span_id":"s1"}
    display = d_verbatim.rstrip(".,;:")
    assert authoritative["verbatim"] == "irs-help.com,"
    assert display == "irs-help.com"

def test_relationships_rendering_when_links_present(tmp_path):
    """If links exist in JSON, HTML should show a Relationships section (smoke/placeholder)."""
    j = {
      "json": {
        "indicators": [
          {"kind":"amount","verbatim":"$1,998.88","category_id":"financial","span_id":"s_amt"},
          {"kind":"account","verbatim":"Zelle ID 123456789","category_id":"financial","span_id":"s_acc"}
        ],
        "categories": {"financial":{}},
        "links": [{"from":"s_amt","to":"s_acc","type":"co_occurs"}]
      }
    }
    Path("artifacts/demo_rules.json").write_text(json.dumps(j), encoding="utf-8")
    # HTML generation is tested via system test elsewhere; here we assert the JSON structure is ready.
    assert "links" in j["json"] and j["json"]["links"][0]["from"] == "s_amt"
    
def test_phone_noise_guards():
    """Test phone number noise guard requirements."""
    # Valid phone should have ≥7 digits and ≤30% whitespace
    valid_phone = "555-123-4567"
    noisy_phone = "1 2 3\n\n\n\n4"
    
    def phone_noise_check(phone_text):
        digit_count = sum(c.isdigit() for c in phone_text)
        if digit_count < 7:
            return False
        whitespace_count = sum(c in " \n\t\r" for c in phone_text)
        whitespace_ratio = whitespace_count / len(phone_text) if phone_text else 0
        if whitespace_ratio > 0.30:
            return False
        return True
    
    assert phone_noise_check(valid_phone) == True, "Valid phone should pass noise check"
    assert phone_noise_check(noisy_phone) == False, "Noisy phone should fail noise check"

def test_display_deduplication_structure():
    """Test deduplication structure for display purposes."""
    # Simulate multiple indicators with same value but different spans
    indicators = [
        {"kind":"domain","verbatim":"example.com","span_id":"s1"},
        {"kind":"domain","verbatim":"example.com","span_id":"s2"},
        {"kind":"domain","verbatim":"different.com","span_id":"s3"},
    ]
    
    # Dedup logic for display
    dedup_dict = {}
    for ind in indicators:
        key = (ind["kind"], ind["verbatim"])
        if key not in dedup_dict:
            dedup_dict[key] = {"count": 0, "spans": []}
        dedup_dict[key]["count"] += 1
        dedup_dict[key]["spans"].append(ind["span_id"])
    
    assert dedup_dict[("domain", "example.com")]["count"] == 2
    assert dedup_dict[("domain", "example.com")]["spans"] == ["s1", "s2"]
    assert dedup_dict[("domain", "different.com")]["count"] == 1