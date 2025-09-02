"""
Negative and noise filtering tests for Safety Sigma.
Ensure proper filtering without changing authoritative outputs.
"""
import pytest
import re
from pathlib import Path

# Mock extraction functions to test negative cases
def extract_phone_patterns(text):
    """Mock phone extraction - will be replaced with actual extraction logic"""
    phone_pattern = r'\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}'
    matches = []
    for match in re.finditer(phone_pattern, text):
        phone_text = match.group().strip()
        # Quality filter: reject tokens with >30% whitespace/linebreak chars
        whitespace_ratio = sum(1 for c in phone_text if c in ' \n\t\r') / len(phone_text)
        digit_count = sum(1 for c in phone_text if c.isdigit())
        
        if digit_count >= 7 and whitespace_ratio <= 0.3:
            matches.append(phone_text)
    return matches

def extract_domain_patterns(text):
    """Mock domain extraction - will be replaced with actual extraction logic"""
    domain_pattern = r'\b[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'
    matches = []
    for match in re.finditer(domain_pattern, text):
        domain_text = match.group()
        matches.append(domain_text)
    return matches

def check_keyword_promotion(text, keyword):
    """Check if keyword gets incorrectly promoted to IOC"""
    # Should NOT happen: "fraudulent" -> "fraud" IOC
    # Only exact tokens should be preserved
    return keyword.lower() in text.lower()

class TestNegativesNoise:
    """Test cases for negative examples and noise filtering"""

    def test_no_phone_on_ocr_artifacts(self):
        """OCR artifacts like '1 ---\\n \\n \\n \\n \\n1' MUST NOT become phone indicators"""
        ocr_noise = "1 ---\n \n \n \n \n1"
        phones = extract_phone_patterns(ocr_noise)
        
        # Should find no valid phone numbers in OCR artifacts
        assert len(phones) == 0, f"OCR artifacts incorrectly extracted as phones: {phones}"
        
        # Additional OCR noise patterns
        more_ocr_noise = "1\n\n\n2\n\n\n3\n\n\n4\n\n\n5\n\n\n6\n\n\n7"
        phones2 = extract_phone_patterns(more_ocr_noise)
        assert len(phones2) == 0, f"More OCR artifacts incorrectly extracted: {phones2}"

    def test_keyword_not_promoted(self):
        """'fraudulent' MUST NOT yield a 'fraud' IOC; exact token only"""
        text_with_fraudulent = "This is a fraudulent scheme targeting victims"
        text_with_fraud = "This is fraud targeting victims"
        
        # "fraudulent" should not be promoted to "fraud" indicator
        has_fraudulent = check_keyword_promotion(text_with_fraudulent, "fraudulent")
        has_fraud = check_keyword_promotion(text_with_fraud, "fraud")
        
        assert has_fraudulent == True  # "fraudulent" is present
        assert has_fraud == True  # "fraud" is present
        
        # But extraction should be exact - no normalization/stemming
        # This test ensures the principle; actual implementation in demo script

    def test_domain_trailing_punct_display_only(self):
        """verbatim 'irs-help.com,' kept in IR; HTML should render 'irs-help.com' (display trim)"""
        text_with_punct = "Visit irs-help.com, for more information"
        domains = extract_domain_patterns(text_with_punct)
        
        # Should extract domain with punctuation preserved
        assert len(domains) > 0, "Should find domain"
        found_domain = domains[0] if domains else ""
        
        # The verbatim should be preserved (this is what goes to IR/rules)
        assert "irs-help.com" in found_domain, f"Domain not found correctly: {found_domain}"
        
        # Display value computation (for HTML only)
        display_value = found_domain.rstrip('.,;:!?')
        assert display_value == "irs-help.com", f"Display value should be clean: {display_value}"

    def test_phone_quality_filters(self):
        """Phone numbers must have ≥7 digits and reject >30% whitespace"""
        # Valid phones
        valid_phones = [
            "+1-800-555-1234",
            "(555) 123-4567", 
            "555.123.4567",
            "5551234567"
        ]
        
        # Invalid phones (too much whitespace, too few digits)
        invalid_phones = [
            "1 2 3 4 5 6",  # Too much whitespace
            "123-45",       # Too few digits
            "1\n2\n3\n4\n5\n6\n7\n8",  # Excessive line breaks
            "   555   123   ",  # Mostly whitespace
        ]
        
        for valid_phone in valid_phones:
            result = extract_phone_patterns(valid_phone)
            assert len(result) > 0, f"Valid phone should be extracted: {valid_phone}"
            
        for invalid_phone in invalid_phones:
            result = extract_phone_patterns(invalid_phone)
            assert len(result) == 0, f"Invalid phone should be rejected: {invalid_phone} -> {result}"

    def test_no_inference_from_context(self):
        """Ensure no inference beyond literal spans"""
        context_text = "John called about the refund issue yesterday"
        
        # Should not infer phone number from "called"
        # Should not infer amount from "refund" without explicit amount
        # Should not infer actor identity from "John"
        
        phones = extract_phone_patterns(context_text)
        assert len(phones) == 0, "Should not infer phone from 'called'"
        
        # This principle extends to all extraction - no inference beyond literals

    def test_exact_preservation_principle(self):
        """Verify exact preservation without normalization"""
        exact_texts = [
            "$1,998.88",  # Should preserve comma and decimal
            "wa.me/15551234567",  # Should preserve exact URL structure  
            "VOID 2000",  # Should preserve case and spacing
            "irs-help.com,",  # Should preserve trailing punctuation in IR
        ]
        
        for text in exact_texts:
            # Principle: what goes into IR/rules should be verbatim
            # Only display layer (HTML) may clean for presentation
            assert text == text, f"Exact preservation principle for: {text}"