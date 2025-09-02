"""
Tests for EDAP (Evidence-Driven Auto-Promotion) functionality
"""
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.proactive.narrative_expander import extract_evidence, Evidence

def test_alt_enum_autopromotes_ready():
    """Test that ALT_ENUM patterns are auto-promoted to ready status"""
    s = [Evidence(sent_id="S1", text="Victims are redirected to WhatsApp or Telegram.", spans=["s_link"])]
    exps = extract_evidence(s)
    
    # Should find ALT_ENUM expansion that gets promoted to ready
    alt_enum_exps = [e for e in exps if e.operator == "ALT_ENUM"]
    assert len(alt_enum_exps) > 0, "Should find ALT_ENUM expansions"
    assert any(e.status == "ready" for e in alt_enum_exps), "ALT_ENUM should be promoted to ready"

def test_range_digits_autopromotes_ready():
    """Test that RANGE_DIGITS patterns are auto-promoted to ready status"""
    s = [Evidence(sent_id="S2", text="VOID followed by a 3-4 digit code.", spans=["s_void"])]
    exps = extract_evidence(s)
    
    # Should find RANGE_DIGITS expansion
    range_exps = [e for e in exps if e.operator == "RANGE_DIGITS"]
    assert len(range_exps) > 0, "Should find RANGE_DIGITS expansions"
    
    # Check pattern format
    patterns = [e.pattern for e in range_exps]
    assert any("VOID[ ]\\\\d{3,4}" in p for p in patterns), f"Should generate VOID digit range pattern, got: {patterns}"
    
    # Check status
    assert any(e.status == "ready" for e in range_exps), "RANGE_DIGITS should be promoted to ready"

def test_literal_set_with_enumeration_promotes():
    """Test that LITERAL_SET with explicit enumeration promotes to ready"""
    s = [Evidence(sent_id="S3", text="Fraudulent domains include paypaI.com, paypai.com, paypa1.com", spans=["s_domains"])]
    exps = extract_evidence(s)
    
    # Should find LITERAL_SET expansions
    literal_exps = [e for e in exps if e.operator == "LITERAL_SET"]
    assert len(literal_exps) > 0, "Should find LITERAL_SET expansions"
    
    # With multiple explicit variants, should promote to ready
    ready_literals = [e for e in literal_exps if e.status == "ready"]
    assert len(ready_literals) > 0, "LITERAL_SET with multiple variants should promote to ready"

def test_traceability_and_evidence_quote():
    """Test that all expansions maintain traceability and evidence quotes"""
    s = [Evidence(sent_id="S3", text="Use paypai.com such as paypaI.com, paypai.com", spans=["s_dom"])]
    exps = extract_evidence(s)
    
    for exp in exps:
        assert exp.parent_spans, f"Expansion {exp.pattern} should have parent_spans"
        assert exp.evidence_quote, f"Expansion {exp.pattern} should have evidence_quote" 
        assert exp.evidence_sent_id, f"Expansion {exp.pattern} should have evidence_sent_id"
        assert exp.operator in ["ALT_ENUM", "RANGE_DIGITS", "LITERAL_SET"], f"Invalid operator: {exp.operator}"

def test_no_expansion_without_evidence():
    """Test that sentences without expansion evidence don't generate expansions"""
    s = [Evidence(sent_id="S4", text="This is a normal sentence without expansion patterns.", spans=["s_normal"])]
    exps = extract_evidence(s)
    
    assert len(exps) == 0, "Sentences without expansion evidence should not generate expansions"

def test_such_as_pattern_extraction():
    """Test extraction of 'such as' enumeration patterns"""
    s = [Evidence(sent_id="S5", text="Payment methods such as gift cards, wire transfers, cryptocurrency.", spans=["s_payment"])]
    exps = extract_evidence(s)
    
    alt_enum_exps = [e for e in exps if e.operator == "ALT_ENUM"]
    assert len(alt_enum_exps) > 0, "Should extract 'such as' enumerations"
    assert any(e.status == "ready" for e in alt_enum_exps), "Such as patterns should promote to ready"

def test_expansion_pattern_format():
    """Test that expansion patterns are properly formatted"""
    s = [
        Evidence(sent_id="S6", text="Contact via WhatsApp or Telegram apps.", spans=["s_contact"]),
        Evidence(sent_id="S7", text="Enter a 4-6 digit verification code.", spans=["s_verify"])
    ]
    exps = extract_evidence(s)
    
    for exp in exps:
        assert exp.pattern, "Pattern should not be empty"
        if exp.operator == "RANGE_DIGITS":
            assert "\\d{" in exp.pattern, "RANGE_DIGITS should contain regex digit pattern"
        if exp.operator in ["ALT_ENUM", "LITERAL_SET"]:
            # Pattern should be valid regex (escaped if literal)
            assert len(exp.pattern) > 0, "Pattern should have content"

def test_edap_criteria_coverage():
    """Test coverage of all EDAP criteria E1, E2, E3"""
    sentences = [
        # E1: ALT_ENUM
        Evidence(sent_id="E1", text="Platforms include WhatsApp or Telegram or Signal.", spans=["s1"]),
        # E2: RANGE_DIGITS  
        Evidence(sent_id="E2", text="Check contains VOID followed by 3-4 digit code.", spans=["s2"]),
        # E3: LITERAL_SET
        Evidence(sent_id="E3", text="Typosquatting sites: paypaI.com, paypai.com, paypa1.com", spans=["s3"])
    ]
    
    exps = extract_evidence(sentences)
    
    # Should have representatives of each EDAP criteria
    operators = {e.operator for e in exps}
    assert "ALT_ENUM" in operators, "Should find ALT_ENUM (E1)"
    assert "RANGE_DIGITS" in operators, "Should find RANGE_DIGITS (E2)" 
    assert "LITERAL_SET" in operators, "Should find LITERAL_SET (E3)"
    
    # All should be promoted to ready
    ready_exps = [e for e in exps if e.status == "ready"]
    assert len(ready_exps) > 0, "EDAP criteria should promote expansions to ready"