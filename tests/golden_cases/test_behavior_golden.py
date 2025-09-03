from src.pdf_processor.extract_behavior import extract_behaviors

def test_g060_redirect():
    """G-060: redirect behavior preserved verbatim."""
    text="Victim redirected to WhatsApp."
    behs=extract_behaviors(text,"R1")
    assert any("WhatsApp" in b["value"] for b in behs)
    
    # Verify full structure
    whatsapp_behaviors = [b for b in behs if "WhatsApp" in b["value"]]
    assert len(whatsapp_behaviors) > 0
    behavior = whatsapp_behaviors[0]
    assert behavior["type"] == "behavior"
    assert behavior["category"] == "redirect"
    assert behavior["report_id"] == "R1"

def test_g061_spoofed_caller_id():
    """G-061: spoofed caller ID phrase preserved."""
    text="The scammer spoofed caller ID to appear local."
    behs=extract_behaviors(text,"R2")
    assert len(behs) > 0, "Should extract at least one behavior"
    
    # Look for spoofing behaviors
    spoof_behaviors = [b for b in behs if b.get("category") == "spoof"]
    assert len(spoof_behaviors) > 0, f"Should find spoof behaviors, got: {behs}"
    
    behavior = spoof_behaviors[0]
    assert behavior["type"] == "behavior"
    assert behavior["category"] == "spoof"
    assert behavior["report_id"] == "R2"
    assert "spoofed caller id" in behavior["value"].lower()

def test_g062_payment_methods():
    """G-062: payment method enumeration preserved (gift cards, wire, crypto)."""
    text="They asked for gift cards, wire transfers, or crypto."
    behs=extract_behaviors(text,"R3")
    vals=" ".join([b["value"] for b in behs]).lower()
    assert "gift card" in vals and "wire" in vals and "crypto" in vals
    
    # Verify multiple payment methods extracted
    payment_behaviors = [b for b in behs if b["category"] == "payment"]
    assert len(payment_behaviors) >= 2  # Should capture multiple payment types
    
    # Verify structure
    for behavior in payment_behaviors:
        assert behavior["type"] == "behavior"
        assert behavior["category"] == "payment"
        assert behavior["report_id"] == "R3"

def test_behavioral_structure_compliance():
    """Test that behavioral indicators maintain required structure."""
    text="Scammer spoofing caller ID demanded urgent action via gift cards on WhatsApp."
    behs=extract_behaviors(text,"TEST")
    
    for behavior in behs:
        # V-001..V-005 compliance: verbatim value, provenance, no inference
        assert "type" in behavior
        assert "value" in behavior
        assert "category" in behavior
        assert "report_id" in behavior
        assert "span_id" in behavior
        
        # Zero-inference: values should be literal matches
        assert behavior["value"] in text or behavior["value"].lower() in text.lower()
        
        # Provenance: span_id should reference location
        assert behavior["span_id"].startswith(behavior["category"])

def test_no_inference_principle():
    """Test that extractor doesn't infer behaviors not literally present."""
    text="The victim lost money in a financial scam."
    behs=extract_behaviors(text,"NOINF")
    
    # Should not extract behaviors that aren't literally mentioned
    # (no "redirected", no "spoofed", no specific payment methods)
    assert len(behs) == 0 or all(b["value"].lower() in text.lower() for b in behs)

def test_multi_behavior_text():
    """Test extraction from text with multiple behavioral indicators."""
    text="The fraudster redirected to Telegram, spoofed caller ID, and demanded gift cards with urgent action required."
    behs=extract_behaviors(text,"MULTI")
    
    # Should extract multiple behaviors
    assert len(behs) >= 2
    
    # Should have different categories
    categories = set(b["category"] for b in behs)
    assert len(categories) >= 2  # Multiple behavior types
    
    # All should be from same report
    assert all(b["report_id"] == "MULTI" for b in behs)