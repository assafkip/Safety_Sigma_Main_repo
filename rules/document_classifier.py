"""
Document Classification Rule Engine for Safety Sigma 2.0 Stage 3

Advanced decision trees for document type classification and workflow selection.
Extends the base rule engine with document-specific analysis capabilities.
"""

import re
from typing import Dict, List, Any
from .base_rule_engine import BaseRuleEngine, RuleSet


class DocumentClassifierEngine(BaseRuleEngine):
    """
    Rule engine specialized for document classification and workflow selection
    """
    
    def __init__(self, rules_dir: str = None):
        """Initialize document classifier engine"""
        super().__init__(rules_dir)
        self.supported_rulesets_list = [
            'document_classification',
            'fraud_detection_advanced', 
            'threat_intelligence_advanced',
            'policy_compliance_advanced'
        ]
    
    def get_supported_rulesets(self) -> List[str]:
        """Get list of supported ruleset names"""
        return self.supported_rulesets_list
    
    def analyze_document_context(self, document_content: str, instructions: str = "", 
                               pdf_file: str = "", **kwargs) -> Dict[str, Any]:
        """
        Create analysis context from document inputs for rule evaluation
        
        Args:
            document_content: Document text content
            instructions: Processing instructions
            pdf_file: PDF file path
            **kwargs: Additional context parameters
            
        Returns:
            Context dictionary for rule evaluation
        """
        context = {
            # Basic document characteristics
            'document_length': len(document_content),
            'word_count': len(document_content.split()),
            'line_count': document_content.count('\\n') + 1,
            'paragraph_count': document_content.count('\\n\\n') + 1,
            
            # Content analysis
            'content_lower': document_content.lower(),
            'instructions_lower': instructions.lower(),
            
            # File characteristics
            'has_pdf_file': bool(pdf_file),
            'pdf_filename': pdf_file,
            
            # Keyword density analysis
            'fraud_keyword_count': self._count_keywords(document_content, self._get_fraud_keywords()),
            'threat_keyword_count': self._count_keywords(document_content, self._get_threat_keywords()),
            'policy_keyword_count': self._count_keywords(document_content, self._get_policy_keywords()),
            'technical_keyword_count': self._count_keywords(document_content, self._get_technical_keywords()),
            
            # Structure indicators
            'has_headers': self._has_headers(document_content),
            'has_lists': self._has_lists(document_content),
            'has_tables': self._has_tables(document_content),
            'has_urls': self._has_urls(document_content),
            'has_emails': self._has_emails(document_content),
            'has_phone_numbers': self._has_phone_numbers(document_content),
            'has_financial_data': self._has_financial_data(document_content),
            
            # Instruction analysis
            'instructions_mention_fraud': 'fraud' in instructions.lower(),
            'instructions_mention_threat': any(word in instructions.lower() for word in ['threat', 'attack', 'malware']),
            'instructions_mention_policy': any(word in instructions.lower() for word in ['policy', 'compliance', 'regulation']),
            'instructions_mention_extraction': 'extract' in instructions.lower(),
            'instructions_mention_analysis': 'analy' in instructions.lower(),  # catches analyze, analysis, etc.
            
            # Calculated ratios
            'fraud_keyword_density': 0.0,
            'threat_keyword_density': 0.0,
            'policy_keyword_density': 0.0,
            'technical_keyword_density': 0.0,
        }
        
        # Calculate keyword densities
        word_count = max(1, context['word_count'])  # Avoid division by zero
        context['fraud_keyword_density'] = context['fraud_keyword_count'] / word_count
        context['threat_keyword_density'] = context['threat_keyword_count'] / word_count
        context['policy_keyword_density'] = context['policy_keyword_count'] / word_count
        context['technical_keyword_density'] = context['technical_keyword_count'] / word_count
        
        # Add any additional context from kwargs
        context.update(kwargs)
        
        return context
    
    def classify_document(self, document_content: str, instructions: str = "", 
                         pdf_file: str = "", **kwargs) -> Dict[str, Any]:
        """
        Classify document using advanced rule engine
        
        Args:
            document_content: Document text content
            instructions: Processing instructions
            pdf_file: PDF file path
            **kwargs: Additional parameters
            
        Returns:
            Classification results with workflow recommendation
        """
        # Create analysis context
        context = self.analyze_document_context(document_content, instructions, pdf_file, **kwargs)
        
        # Evaluate document classification rules
        classification_result = self.evaluate_rules('document_classification', context)
        
        # Enhance results with additional analysis
        enhanced_result = {
            'classification': classification_result,
            'context': context,
            'recommended_workflow': classification_result['recommended_workflow'],
            'confidence_score': min(1.0, 0.7 + classification_result['total_confidence_boost']),
            'decision_factors': {
                'keyword_analysis': {
                    'fraud_density': context['fraud_keyword_density'],
                    'threat_density': context['threat_keyword_density'],
                    'policy_density': context['policy_keyword_density'],
                    'technical_density': context['technical_keyword_density']
                },
                'structure_analysis': {
                    'has_headers': context['has_headers'],
                    'has_lists': context['has_lists'],
                    'has_tables': context['has_tables'],
                    'has_financial_data': context['has_financial_data']
                },
                'instruction_analysis': {
                    'mentions_fraud': context['instructions_mention_fraud'],
                    'mentions_threat': context['instructions_mention_threat'],
                    'mentions_policy': context['instructions_mention_policy']
                }
            },
            'matched_rules': [result['node_id'] for result in classification_result['root_results'] if result['matched']],
            'actions': classification_result['all_actions']
        }
        
        return enhanced_result
    
    def _count_keywords(self, text: str, keywords: List[str]) -> int:
        """Count occurrences of keywords in text"""
        text_lower = text.lower()
        count = 0
        for keyword in keywords:
            count += text_lower.count(keyword.lower())
        return count
    
    def _get_fraud_keywords(self) -> List[str]:
        """Get fraud-related keywords for analysis"""
        return [
            'fraud', 'fraudulent', 'scam', 'scammer', 'phishing', 'deception', 'deceptive',
            'fake', 'forged', 'counterfeit', 'suspicious', 'illegal', 'unauthorized',
            'embezzlement', 'money laundering', 'ponzi', 'pyramid scheme', 'identity theft',
            'credit card fraud', 'bank fraud', 'wire fraud', 'securities fraud'
        ]
    
    def _get_threat_keywords(self) -> List[str]:
        """Get threat-related keywords for analysis"""
        return [
            'threat', 'attack', 'malware', 'virus', 'ransomware', 'trojan', 'spyware',
            'vulnerability', 'exploit', 'breach', 'hack', 'hacker', 'cyber', 'security',
            'intrusion', 'backdoor', 'botnet', 'ddos', 'apt', 'zero-day'
        ]
    
    def _get_policy_keywords(self) -> List[str]:
        """Get policy-related keywords for analysis"""
        return [
            'policy', 'policies', 'compliance', 'regulation', 'regulatory', 'guideline',
            'standard', 'framework', 'governance', 'audit', 'controls', 'procedures',
            'requirements', 'mandatory', 'obligatory', 'sox', 'gdpr', 'hipaa', 'pci'
        ]
    
    def _get_technical_keywords(self) -> List[str]:
        """Get technical keywords for analysis"""
        return [
            'api', 'endpoint', 'database', 'server', 'network', 'protocol', 'encryption',
            'authentication', 'authorization', 'ssl', 'tls', 'certificate', 'firewall',
            'logs', 'monitoring', 'infrastructure', 'architecture', 'configuration'
        ]
    
    def _has_headers(self, text: str) -> bool:
        """Check if document has header structures"""
        return bool(re.search(r'#+\s+|^[A-Z][^\n]*:$', text, re.MULTILINE))
    
    def _has_lists(self, text: str) -> bool:
        """Check if document has list structures"""
        return bool(re.search(r'^\s*[-*+]\s+|^\s*\d+\.\s+', text, re.MULTILINE))
    
    def _has_tables(self, text: str) -> bool:
        """Check if document has table-like structures"""
        return bool(re.search(r'\|.*\||\t.*\t', text))
    
    def _has_urls(self, text: str) -> bool:
        """Check if document contains URLs"""
        return bool(re.search(r'https?://|www\.', text, re.IGNORECASE))
    
    def _has_emails(self, text: str) -> bool:
        """Check if document contains email addresses"""
        return bool(re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text))
    
    def _has_phone_numbers(self, text: str) -> bool:
        """Check if document contains phone numbers"""
        return bool(re.search(r'\b(?:\+?1[-.]?)?\(?[0-9]{3}\)?[-.]?[0-9]{3}[-.]?[0-9]{4}\b', text))
    
    def _has_financial_data(self, text: str) -> bool:
        """Check if document contains financial data patterns"""
        return bool(re.search(r'\$[0-9,]+|\b\d+\.\d{2}\b|account\s+number|routing\s+number', text, re.IGNORECASE))