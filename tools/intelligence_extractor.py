#!/usr/bin/env python3
"""
Intelligence Extraction Tool - Content-Only Analysis
Operates exclusively on provided document text with mandatory source evidence.
"""

import re
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

@dataclass 
class ExtractionResult:
    fraud_types: List[Dict[str, str]]
    financial_impact: List[Dict[str, str]]
    operational_methods: List[Dict[str, Any]]
    targeting_analysis: List[Dict[str, str]]

class IntelligenceExtractor:
    """
    Extracts structured intelligence from document content.
    All claims must include source evidence from the provided text.
    """
    
    def __init__(self):
        # Define patterns for extraction - only match what's explicitly in text
        self.patterns = {
            'financial_amounts': r'\$[\d,]+\.?\d*|\£[\d,]+\.?\d*|€[\d,]+\.?\d*',
            'platforms': r'\b(?:Facebook|Instagram|TikTok|WhatsApp|Telegram|Mastodon|Threads|Twitter|X)\b',
            'domains': r'\b[a-zA-Z0-9.-]+\[?\.\]?(?:com|net|org)\b',
            'countries': r'\b(?:China|UK|U\.K\.|United States|U\.S\.|Beijing|London|US)\b',
            'agencies': r'\b(?:FTC|CFPB|IC3|FBI|CGTN|Graphika)\b'
        }
    
    def extract_intelligence(self, document_content: str, analyst_instructions: str = "") -> Dict[str, Any]:
        """
        Extract structured intelligence with source evidence.
        Returns JSON that can be passed to forced tool.
        """
        
        return {
            "fraud_types": self._extract_fraud_types(document_content),
            "financial_impact": self._extract_financial_impact(document_content), 
            "operational_methods": self._extract_operational_methods(document_content),
            "targeting_analysis": self._extract_targeting_analysis(document_content)
        }
    
    def _extract_fraud_types(self, content: str) -> List[Dict[str, str]]:
        """Extract fraud categories mentioned in source with evidence."""
        fraud_types = []
        
        # Look for information laundering operations
        if "information laundering" in content.lower():
            evidence = self._find_context_around_phrase(content, "information laundering", 100)
            fraud_types.append({
                "type": "Information laundering network", 
                "context": "AI-powered content manipulation to disguise origin",
                "source_evidence": evidence
            })
        
        # Look for AI-assisted fraud 
        if "AI tools" in content and ("translate" in content or "summarize" in content):
            evidence = self._find_context_around_phrase(content, "AI tools", 150)
            fraud_types.append({
                "type": "AI-assisted content laundering",
                "context": "Using AI to translate and disguise content origin",
                "source_evidence": evidence
            })
        
        # Look for coordinated inauthentic behavior
        if "coordinated network" in content.lower():
            evidence = self._find_context_around_phrase(content, "coordinated network", 100)
            fraud_types.append({
                "type": "Coordinated inauthentic behavior",
                "context": "Multiple accounts operating in coordination",
                "source_evidence": evidence
            })
        
        return fraud_types
    
    def _extract_financial_impact(self, content: str) -> List[Dict[str, str]]:
        """Extract financial data with exact source evidence."""
        financial_impacts = []
        
        # Find dollar amounts with context
        amounts = re.finditer(self.patterns['financial_amounts'], content)
        for match in amounts:
            value = match.group()
            context = self._find_context_around_match(content, match, 80)
            
            # Determine unit
            if '$' in value:
                unit = "USD"
            elif '£' in value:
                unit = "GBP" 
            elif '€' in value:
                unit = "EUR"
            else:
                unit = "other"
                
            financial_impacts.append({
                "value": value,
                "unit": unit,
                "context": "Amount mentioned in source document",
                "source_evidence": context
            })
        
        # Look for follower counts
        follower_pattern = r'(\d+k?)\s+followers?'
        followers = re.finditer(follower_pattern, content, re.IGNORECASE)
        for match in followers:
            value = match.group(1)
            context = self._find_context_around_match(content, match, 60)
            financial_impacts.append({
                "value": value,
                "unit": "count",
                "context": "Social media followers",
                "source_evidence": context
            })
        
        return financial_impacts
    
    def _extract_operational_methods(self, content: str) -> List[Dict[str, Any]]:
        """Extract operational techniques with platforms and evidence."""
        methods = []
        
        # Look for AI generation techniques
        if "DALL-E" in content:
            platforms = self._extract_platforms_from_context(content, "DALL-E")
            evidence = self._find_context_around_phrase(content, "DALL-E", 120)
            methods.append({
                "technique": "AI image generation for fake branding",
                "platforms": platforms,
                "source_evidence": evidence
            })
        
        # Look for advertising methods
        if "Facebook ads" in content:
            evidence = self._find_context_around_phrase(content, "Facebook ads", 100)
            methods.append({
                "technique": "Paid social media promotion",
                "platforms": ["Facebook"],
                "source_evidence": evidence
            })
        
        # Look for domain registration patterns
        if "Alibaba Cloud" in content and "registrar" in content.lower():
            evidence = self._find_context_around_phrase(content, "Alibaba Cloud", 150)
            methods.append({
                "technique": "Coordinated domain registration",
                "platforms": ["Web domains"],
                "source_evidence": evidence
            })
        
        # Look for multi-language operations
        if re.search(r'English.*French.*Spanish.*Vietnamese', content, re.IGNORECASE):
            evidence = self._find_context_around_phrase(content, "English, French, Spanish", 100)
            methods.append({
                "technique": "Multi-language content adaptation",
                "platforms": self._extract_platforms_from_context(content, "language"),
                "source_evidence": evidence
            })
        
        return methods
    
    def _extract_targeting_analysis(self, content: str) -> List[Dict[str, str]]:
        """Extract targeting information with geographic and demographic data."""
        targeting = []
        
        # Look for geographic targeting
        countries = re.finditer(self.patterns['countries'], content)
        for match in countries:
            country = match.group()
            context = self._find_context_around_match(content, match, 100)
            
            # Extract demographic info from context if available
            demo_info = "Not specified in source"
            if "young" in context.lower():
                demo_info = "Young audiences mentioned"
            elif "aged" in context.lower():
                demo_info = "Age-specific targeting mentioned"
            
            targeting.append({
                "target": f"Audiences in {country}",
                "geography": country,
                "demography": demo_info,
                "source_evidence": context
            })
        
        # Look for age-specific targeting
        age_pattern = r'aged?\s+(\d+)-?(\d+)?|children|young|youth'
        age_matches = re.finditer(age_pattern, content, re.IGNORECASE)
        for match in age_matches:
            context = self._find_context_around_match(content, match, 80)
            targeting.append({
                "target": "Age-specific demographic targeting",
                "geography": "Global", 
                "demography": match.group(),
                "source_evidence": context
            })
        
        return targeting
    
    def _extract_platforms_from_context(self, content: str, search_term: str) -> List[str]:
        """Extract platform names from context around search term."""
        # Find context around search term
        context = self._find_context_around_phrase(content, search_term, 200)
        
        # Extract platforms mentioned in context
        platforms = []
        for platform_match in re.finditer(self.patterns['platforms'], context):
            platform = platform_match.group()
            if platform not in platforms:
                platforms.append(platform)
        
        return platforms
    
    def _find_context_around_phrase(self, content: str, phrase: str, context_length: int) -> str:
        """Find context around a phrase with specified character length."""
        match = re.search(re.escape(phrase), content, re.IGNORECASE)
        if not match:
            return "Phrase not found in source"
        
        start = max(0, match.start() - context_length//2)
        end = min(len(content), match.end() + context_length//2)
        
        return content[start:end].strip()
    
    def _find_context_around_match(self, content: str, match, context_length: int) -> str:
        """Find context around a regex match object."""
        start = max(0, match.start() - context_length//2)
        end = min(len(content), match.end() + context_length//2)
        
        return content[start:end].strip()


def extract_intelligence_tool(document_content: str, analyst_instructions: str = "") -> Dict[str, Any]:
    """
    Tool function for forced extraction.
    Returns structured intelligence with mandatory source evidence.
    """
    extractor = IntelligenceExtractor()
    return extractor.extract_intelligence(document_content, analyst_instructions)


if __name__ == "__main__":
    # Test with sample content
    test_content = """
    Graphika identified a network of 11 domains and 16 companion social media accounts that laundered 
    exclusively English-language articles originally published by the Chinese state media outlet CGTN.
    The assets almost certainly used AI tools to translate and summarize articles from CGTN.
    Facebook pages ran ads to promote their content. The domain registrar for all 11 domains 
    is Alibaba Cloud Computing Ltd. located in Beijing, China.
    """
    
    extractor = IntelligenceExtractor()
    result = extractor.extract_intelligence(test_content)
    print(json.dumps(result, indent=2))