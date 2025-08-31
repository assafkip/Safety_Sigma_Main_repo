"""
Dynamic Rule Generator - Extract Detection Rules from Document Content

Analyzes document content to automatically generate YAML-based detection rules
for operational patterns, indicators, and techniques directly from source material.
"""

import re
import json
from typing import Dict, List, Any, Tuple, Set
from collections import defaultdict, Counter
from dataclasses import dataclass, asdict
import hashlib
from datetime import datetime


@dataclass
class RuleCondition:
    """Individual rule condition extracted from document"""
    field: str
    operator: str  
    value: Any
    confidence: float
    source_evidence: str


@dataclass  
class DetectionRule:
    """Complete detection rule with conditions and metadata"""
    rule_id: str
    name: str
    description: str
    conditions: List[RuleCondition]
    confidence_boost: float
    workflow_recommendation: str
    priority: str
    source_document: str
    extraction_confidence: float
    tags: List[str]


class DynamicRuleGenerator:
    """
    Extracts operational detection rules from document content
    
    Analyzes documents to identify:
    - Operational patterns and techniques
    - Infrastructure indicators (domains, IPs, tools)
    - Behavioral patterns and TTPs
    - Geographic and temporal indicators
    - Communication patterns and platforms
    """
    
    def __init__(self):
        self.generated_rules = []
        self.extraction_patterns = self._init_extraction_patterns()
        self.rule_templates = self._init_rule_templates()
    
    def _init_extraction_patterns(self) -> Dict[str, Dict[str, str]]:
        """Initialize regex patterns for rule extraction"""
        return {
            'infrastructure': {
                'domains': r'\b[a-zA-Z0-9.-]+\[?\.\]?(?:com|net|org|info|biz)\b',
                'ip_addresses': r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
                'email_patterns': r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b',
                'urls': r'https?://[^\s<>"{}|\\^`\[\]]+',
                'registrars': r'(?:registrar|registered|registration).*?([A-Za-z][A-Za-z0-9\s]+(?:Ltd|Inc|Corp|LLC)?)',
            },
            'techniques': {
                'ai_tools': r'\b(?:AI tools?|DALL-E|GPT|artificial intelligence|machine learning|automated|generated)\b',
                'social_engineering': r'\b(?:phishing|social engineering|manipulation|deception|impersonat)\w*\b',
                'content_manipulation': r'\b(?:launder|disguise|repackage|translate|summarize|modify|alter)\w*\b',
                'coordination': r'\b(?:coordinated|network|campaign|operation|systematic)\b',
                'evasion': r'\b(?:evade|avoid|bypass|circumvent|hide|conceal)\w*\b',
            },
            'platforms': {
                'social_media': r'\b(?:Facebook|Instagram|TikTok|Twitter|X|LinkedIn|YouTube|Telegram|WhatsApp|Discord|Reddit)\b',
                'messaging': r'\b(?:Signal|Telegram|WhatsApp|encrypted|messaging|chat)\b',
                'hosting': r'\b(?:Amazon|AWS|Google Cloud|Microsoft Azure|Cloudflare|hosting)\b',
                'payment': r'\b(?:Bitcoin|cryptocurrency|PayPal|wire transfer|money transfer)\b',
            },
            'indicators': {
                'financial': r'\$[\d,]+\.?\d*|\£[\d,]+\.?\d*|€[\d,]+\.?\d*|\b\d+k?\s+(?:dollars?|USD|EUR|GBP)\b',
                'geographic': r'\b(?:China|Beijing|Russia|Moscow|Iran|North Korea|US|USA|UK|European?)\b',
                'temporal': r'\b(?:\d{4}|\d{1,2}\/\d{1,2}\/\d{4}|January|February|March|April|May|June|July|August|September|October|November|December)\b',
                'quantities': r'\b\d+\s*(?:domains?|accounts?|users?|victims?|targets?|sites?|pages?)\b',
            },
            'threat_actors': {
                'attributions': r'\b(?:APT\d+|Lazarus|Fancy Bear|Cozy Bear|state-sponsored|nation-state)\b',
                'motivations': r'\b(?:financial|political|espionage|disruption|propaganda|disinformation)\b',
                'capabilities': r'\b(?:sophisticated|advanced|professional|technical|organized)\b',
            }
        }
    
    def _init_rule_templates(self) -> Dict[str, Dict[str, Any]]:
        """Initialize rule templates for different pattern types"""
        return {
            'infrastructure_cluster': {
                'name_template': "{infrastructure_type}_cluster_detection",
                'description_template': "Detects {infrastructure_type} infrastructure patterns based on {source_doc}",
                'workflow': 'threat_intelligence_workflow',
                'base_confidence': 0.3,
                'priority': 'medium'
            },
            'technique_signature': {
                'name_template': "{technique_name}_technique_detection", 
                'description_template': "Identifies {technique_name} technique usage patterns",
                'workflow': 'fraud_analysis_workflow',
                'base_confidence': 0.4,
                'priority': 'high'
            },
            'campaign_pattern': {
                'name_template': "{campaign_name}_campaign_indicators",
                'description_template': "Detects indicators associated with {campaign_name} campaign",
                'workflow': 'threat_intelligence_workflow', 
                'base_confidence': 0.5,
                'priority': 'high'
            },
            'actor_behavior': {
                'name_template': "{actor_name}_behavioral_indicators",
                'description_template': "Behavioral patterns associated with {actor_name}",
                'workflow': 'threat_intelligence_workflow',
                'base_confidence': 0.35,
                'priority': 'medium'
            }
        }
    
    def generate_rules_from_document(self, document_content: str, document_name: str = "unknown", 
                                   analyst_instructions: str = "") -> List[DetectionRule]:
        """
        Generate detection rules from document content
        
        Args:
            document_content: Document text to analyze
            document_name: Name/identifier for source document
            analyst_instructions: Additional context for rule generation
            
        Returns:
            List of generated detection rules
        """
        self.generated_rules = []
        
        # Extract operational patterns
        infrastructure_patterns = self._extract_infrastructure_patterns(document_content)
        technique_patterns = self._extract_technique_patterns(document_content)
        campaign_patterns = self._extract_campaign_patterns(document_content)
        behavioral_patterns = self._extract_behavioral_patterns(document_content)
        
        # Generate rules for each pattern type
        self._generate_infrastructure_rules(infrastructure_patterns, document_name, document_content)
        self._generate_technique_rules(technique_patterns, document_name, document_content)
        self._generate_campaign_rules(campaign_patterns, document_name, document_content)
        self._generate_behavioral_rules(behavioral_patterns, document_name, document_content)
        
        # Filter and rank rules by confidence
        filtered_rules = self._filter_and_rank_rules()
        
        return filtered_rules
    
    def _extract_infrastructure_patterns(self, content: str) -> Dict[str, List[Dict]]:
        """Extract infrastructure-related patterns"""
        patterns = defaultdict(list)
        
        # Domain clustering
        domains = re.findall(self.extraction_patterns['infrastructure']['domains'], content, re.IGNORECASE)
        if len(domains) >= 2:
            # Look for registrar patterns
            registrar_matches = re.findall(self.extraction_patterns['infrastructure']['registrars'], content, re.IGNORECASE)
            
            for registrar_match in registrar_matches:
                if isinstance(registrar_match, tuple):
                    registrar = registrar_match[0] if registrar_match[0] else registrar_match[1] if len(registrar_match) > 1 else "Unknown"
                else:
                    registrar = registrar_match
                
                # Find context around registrar mention
                context = self._find_context_around_phrase(content, registrar, 200)
                
                patterns['domain_clusters'].append({
                    'registrar': registrar.strip(),
                    'domain_count': len(domains),
                    'domains_sample': domains[:5],  # First 5 domains
                    'context': context,
                    'confidence': min(0.9, len(domains) * 0.15)  # Higher confidence for more domains
                })
        
        return dict(patterns)
    
    def _extract_technique_patterns(self, content: str) -> Dict[str, List[Dict]]:
        """Extract technique and TTP patterns"""
        patterns = defaultdict(list)
        
        # AI-assisted techniques
        ai_mentions = re.finditer(self.extraction_patterns['techniques']['ai_tools'], content, re.IGNORECASE)
        ai_contexts = []
        for match in ai_mentions:
            context = self._find_context_around_match(content, match, 150)
            ai_contexts.append({
                'tool_mention': match.group(),
                'context': context,
                'position': match.start()
            })
        
        if ai_contexts:
            # Look for content manipulation context
            manipulation_terms = re.findall(self.extraction_patterns['techniques']['content_manipulation'], content, re.IGNORECASE)
            
            patterns['ai_content_manipulation'].append({
                'ai_tools': [ctx['tool_mention'] for ctx in ai_contexts],
                'manipulation_terms': manipulation_terms,
                'technique_confidence': min(0.8, len(ai_contexts) * 0.2 + len(manipulation_terms) * 0.1),
                'contexts': ai_contexts
            })
        
        # Coordination patterns
        coord_matches = re.finditer(self.extraction_patterns['techniques']['coordination'], content, re.IGNORECASE)
        if coord_matches:
            coord_contexts = []
            for match in coord_matches:
                context = self._find_context_around_match(content, match, 100)
                coord_contexts.append(context)
            
            # Look for scale indicators
            quantity_matches = re.findall(self.extraction_patterns['indicators']['quantities'], content, re.IGNORECASE)
            
            patterns['coordinated_operations'].append({
                'coordination_terms': [match.group() for match in re.finditer(self.extraction_patterns['techniques']['coordination'], content, re.IGNORECASE)],
                'scale_indicators': quantity_matches,
                'contexts': coord_contexts,
                'confidence': min(0.7, len(coord_contexts) * 0.15)
            })
        
        return dict(patterns)
    
    def _extract_campaign_patterns(self, content: str) -> Dict[str, List[Dict]]:
        """Extract campaign-specific patterns and names"""
        patterns = defaultdict(list)
        
        # Look for campaign names (capitalized phrases, quoted terms)
        campaign_name_patterns = [
            r'"([A-Z][A-Za-z\s]{5,30})"',  # Quoted campaign names
            r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)(?:\s+[Nn]etwork|[Cc]ampaign|[Oo]peration)\b',  # Named operations
            r'\b(?:Operation|Campaign)\s+([A-Z][A-Za-z\s]{3,20})\b',  # Operation/Campaign X
        ]
        
        campaign_names = []
        for pattern in campaign_name_patterns:
            matches = re.findall(pattern, content)
            campaign_names.extend(matches)
        
        # Extract from document - look for "Falsos Amigos" type patterns
        title_matches = re.findall(r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)(?:\s+Network|\s+Group|\s+Campaign)\b', content)
        campaign_names.extend(title_matches)
        
        for campaign_name in set(campaign_names):
            if len(campaign_name.strip()) > 3:
                context = self._find_context_around_phrase(content, campaign_name, 200)
                
                # Look for associated techniques and infrastructure
                associated_techniques = []
                for tech_category, tech_patterns in self.extraction_patterns['techniques'].items():
                    if re.search(tech_patterns, context, re.IGNORECASE):
                        associated_techniques.append(tech_category)
                
                patterns['named_campaigns'].append({
                    'name': campaign_name.strip(),
                    'context': context,
                    'associated_techniques': associated_techniques,
                    'confidence': 0.6 if len(associated_techniques) > 1 else 0.4
                })
        
        return dict(patterns)
    
    def _extract_behavioral_patterns(self, content: str) -> Dict[str, List[Dict]]:
        """Extract behavioral and operational patterns"""
        patterns = defaultdict(list)
        
        # Multi-platform operations
        platform_mentions = re.findall(self.extraction_patterns['platforms']['social_media'], content, re.IGNORECASE)
        if len(platform_mentions) >= 3:  # Multi-platform indicates coordination
            unique_platforms = list(set(platform_mentions))
            
            patterns['multi_platform_operations'].append({
                'platforms': unique_platforms,
                'platform_count': len(unique_platforms),
                'total_mentions': len(platform_mentions),
                'confidence': min(0.8, len(unique_platforms) * 0.1),
                'context': self._find_context_around_phrase(content, ' '.join(unique_platforms[:3]), 150)
            })
        
        # Geographic clustering
        geo_mentions = re.findall(self.extraction_patterns['indicators']['geographic'], content, re.IGNORECASE)
        geo_counter = Counter(geo_mentions)
        
        for location, count in geo_counter.items():
            if count >= 3:  # Multiple mentions indicate focus
                context = self._find_context_around_phrase(content, location, 150)
                
                patterns['geographic_focus'].append({
                    'location': location,
                    'mention_count': count,
                    'context': context,
                    'confidence': min(0.7, count * 0.1)
                })
        
        return dict(patterns)
    
    def _generate_infrastructure_rules(self, patterns: Dict[str, List[Dict]], doc_name: str, content: str):
        """Generate rules for infrastructure patterns"""
        for pattern_type, pattern_list in patterns.items():
            for pattern in pattern_list:
                if pattern_type == 'domain_clusters':
                    rule = self._create_domain_cluster_rule(pattern, doc_name)
                    if rule:
                        self.generated_rules.append(rule)
    
    def _generate_technique_rules(self, patterns: Dict[str, List[Dict]], doc_name: str, content: str):
        """Generate rules for technique patterns"""
        for pattern_type, pattern_list in patterns.items():
            for pattern in pattern_list:
                if pattern_type == 'ai_content_manipulation':
                    rule = self._create_ai_technique_rule(pattern, doc_name)
                    if rule:
                        self.generated_rules.append(rule)
                elif pattern_type == 'coordinated_operations':
                    rule = self._create_coordination_rule(pattern, doc_name)
                    if rule:
                        self.generated_rules.append(rule)
    
    def _generate_campaign_rules(self, patterns: Dict[str, List[Dict]], doc_name: str, content: str):
        """Generate rules for campaign patterns"""
        for pattern_type, pattern_list in patterns.items():
            for pattern in pattern_list:
                if pattern_type == 'named_campaigns':
                    rule = self._create_campaign_rule(pattern, doc_name)
                    if rule:
                        self.generated_rules.append(rule)
    
    def _generate_behavioral_rules(self, patterns: Dict[str, List[Dict]], doc_name: str, content: str):
        """Generate rules for behavioral patterns"""
        for pattern_type, pattern_list in patterns.items():
            for pattern in pattern_list:
                if pattern_type == 'multi_platform_operations':
                    rule = self._create_multi_platform_rule(pattern, doc_name)
                    if rule:
                        self.generated_rules.append(rule)
                elif pattern_type == 'geographic_focus':
                    rule = self._create_geographic_rule(pattern, doc_name)
                    if rule:
                        self.generated_rules.append(rule)
    
    def _create_domain_cluster_rule(self, pattern: Dict, doc_name: str) -> DetectionRule:
        """Create rule for domain cluster detection"""
        rule_id = self._generate_rule_id(f"domain_cluster_{pattern['registrar']}")
        
        conditions = [
            RuleCondition(
                field="domain_registrar",
                operator="contains",
                value=[pattern['registrar']],
                confidence=pattern['confidence'],
                source_evidence=pattern['context'][:200]
            ),
            RuleCondition(
                field="domain_count", 
                operator="ge",
                value=max(2, pattern['domain_count'] // 2),
                confidence=0.7,
                source_evidence=f"Pattern shows {pattern['domain_count']} domains"
            )
        ]
        
        return DetectionRule(
            rule_id=rule_id,
            name=f"{pattern['registrar']}_domain_cluster",
            description=f"Detects domain clusters registered with {pattern['registrar']} based on {doc_name}",
            conditions=conditions,
            confidence_boost=pattern['confidence'],
            workflow_recommendation='threat_intelligence_workflow',
            priority='medium',
            source_document=doc_name,
            extraction_confidence=pattern['confidence'],
            tags=['infrastructure', 'domains', 'clustering']
        )
    
    def _create_ai_technique_rule(self, pattern: Dict, doc_name: str) -> DetectionRule:
        """Create rule for AI-assisted technique detection"""
        rule_id = self._generate_rule_id("ai_content_manipulation")
        
        conditions = [
            RuleCondition(
                field="ai_tool_mentions",
                operator="contains", 
                value=pattern['ai_tools'],
                confidence=pattern['technique_confidence'],
                source_evidence=pattern['contexts'][0]['context'][:200] if pattern['contexts'] else ""
            ),
            RuleCondition(
                field="content_manipulation_terms",
                operator="contains",
                value=pattern['manipulation_terms'],
                confidence=0.6,
                source_evidence="Content manipulation terminology detected"
            )
        ]
        
        return DetectionRule(
            rule_id=rule_id,
            name="ai_assisted_content_laundering",
            description=f"Detects AI-assisted content manipulation techniques from {doc_name}",
            conditions=conditions,
            confidence_boost=pattern['technique_confidence'],
            workflow_recommendation='fraud_analysis_workflow',
            priority='high',
            source_document=doc_name,
            extraction_confidence=pattern['technique_confidence'],
            tags=['ai', 'content_manipulation', 'techniques']
        )
    
    def _create_campaign_rule(self, pattern: Dict, doc_name: str) -> DetectionRule:
        """Create rule for named campaign detection"""
        rule_id = self._generate_rule_id(f"campaign_{pattern['name'].lower().replace(' ', '_')}")
        
        conditions = [
            RuleCondition(
                field="campaign_name_mentions",
                operator="contains",
                value=[pattern['name']],
                confidence=pattern['confidence'],
                source_evidence=pattern['context'][:200]
            )
        ]
        
        # Add technique conditions
        for technique in pattern['associated_techniques']:
            conditions.append(
                RuleCondition(
                    field=f"{technique}_indicators",
                    operator="gt",
                    value=0,
                    confidence=0.5,
                    source_evidence=f"Associated with {technique}"
                )
            )
        
        return DetectionRule(
            rule_id=rule_id,
            name=f"{pattern['name'].lower().replace(' ', '_')}_campaign_detection",
            description=f"Detects {pattern['name']} campaign indicators from {doc_name}",
            conditions=conditions,
            confidence_boost=pattern['confidence'],
            workflow_recommendation='threat_intelligence_workflow',
            priority='high',
            source_document=doc_name,
            extraction_confidence=pattern['confidence'],
            tags=['campaign', 'threat_intelligence', pattern['name'].lower().replace(' ', '_')]
        )
    
    def _create_coordination_rule(self, pattern: Dict, doc_name: str) -> DetectionRule:
        """Create rule for coordinated operation detection"""
        rule_id = self._generate_rule_id("coordinated_operations")
        
        conditions = [
            RuleCondition(
                field="coordination_terms",
                operator="contains",
                value=pattern['coordination_terms'],
                confidence=pattern['confidence'],
                source_evidence=pattern['contexts'][0][:200] if pattern['contexts'] else ""
            )
        ]
        
        if pattern['scale_indicators']:
            conditions.append(
                RuleCondition(
                    field="scale_indicators",
                    operator="contains",
                    value=pattern['scale_indicators'],
                    confidence=0.6,
                    source_evidence="Scale indicators detected"
                )
            )
        
        return DetectionRule(
            rule_id=rule_id,
            name="coordinated_operation_detection",
            description=f"Detects coordinated operation patterns from {doc_name}",
            conditions=conditions,
            confidence_boost=pattern['confidence'],
            workflow_recommendation='threat_intelligence_workflow',
            priority='high',
            source_document=doc_name,
            extraction_confidence=pattern['confidence'],
            tags=['coordination', 'operations', 'scale']
        )
    
    def _create_multi_platform_rule(self, pattern: Dict, doc_name: str) -> DetectionRule:
        """Create rule for multi-platform operation detection"""
        rule_id = self._generate_rule_id("multi_platform_operations")
        
        conditions = [
            RuleCondition(
                field="platform_mentions",
                operator="contains",
                value=pattern['platforms'],
                confidence=pattern['confidence'],
                source_evidence=pattern['context'][:200]
            ),
            RuleCondition(
                field="platform_count",
                operator="ge",
                value=3,
                confidence=0.7,
                source_evidence=f"Detected {pattern['platform_count']} platforms"
            )
        ]
        
        return DetectionRule(
            rule_id=rule_id,
            name="multi_platform_coordination",
            description=f"Detects multi-platform operational patterns from {doc_name}",
            conditions=conditions,
            confidence_boost=pattern['confidence'],
            workflow_recommendation='threat_intelligence_workflow',
            priority='medium',
            source_document=doc_name,
            extraction_confidence=pattern['confidence'],
            tags=['multi_platform', 'social_media', 'coordination']
        )
    
    def _create_geographic_rule(self, pattern: Dict, doc_name: str) -> DetectionRule:
        """Create rule for geographic focus detection"""
        rule_id = self._generate_rule_id(f"geographic_{pattern['location'].lower()}")
        
        conditions = [
            RuleCondition(
                field="geographic_mentions",
                operator="contains",
                value=[pattern['location']],
                confidence=pattern['confidence'],
                source_evidence=pattern['context'][:200]
            ),
            RuleCondition(
                field=f"{pattern['location'].lower()}_mention_count",
                operator="ge", 
                value=max(2, pattern['mention_count'] // 2),
                confidence=0.6,
                source_evidence=f"Mentioned {pattern['mention_count']} times"
            )
        ]
        
        return DetectionRule(
            rule_id=rule_id,
            name=f"{pattern['location'].lower()}_geographic_focus",
            description=f"Detects {pattern['location']}-focused operations from {doc_name}",
            conditions=conditions,
            confidence_boost=pattern['confidence'],
            workflow_recommendation='threat_intelligence_workflow',
            priority='medium',
            source_document=doc_name,
            extraction_confidence=pattern['confidence'],
            tags=['geographic', 'targeting', pattern['location'].lower()]
        )
    
    def _filter_and_rank_rules(self) -> List[DetectionRule]:
        """Filter and rank rules by confidence and quality"""
        # Filter by minimum confidence
        filtered = [rule for rule in self.generated_rules if rule.extraction_confidence >= 0.3]
        
        # Sort by confidence and priority
        priority_weights = {'high': 3, 'medium': 2, 'low': 1}
        
        filtered.sort(
            key=lambda r: (priority_weights.get(r.priority, 1), r.extraction_confidence),
            reverse=True
        )
        
        return filtered
    
    def export_rules_yaml(self, rules: List[DetectionRule], ruleset_name: str = "document_derived") -> str:
        """Export rules to YAML format for rule engine"""
        yaml_data = {
            'name': ruleset_name,
            'version': "1.0.0",
            'description': f"Dynamically generated rules from document analysis",
            'generated_date': datetime.now().isoformat(),
            'default_workflow': 'general_analysis_workflow',
            'rules': []
        }
        
        for rule in rules:
            rule_dict = {
                'id': rule.rule_id,
                'name': rule.name,
                'description': rule.description,
                'operator': 'AND',
                'workflow': rule.workflow_recommendation,
                'confidence_boost': rule.confidence_boost,
                'priority': rule.priority,
                'tags': rule.tags,
                'conditions': []
            }
            
            for condition in rule.conditions:
                condition_dict = {
                    'field': condition.field,
                    'operator': condition.operator,
                    'value': condition.value
                }
                rule_dict['conditions'].append(condition_dict)
            
            # Add metadata
            rule_dict['metadata'] = {
                'source_document': rule.source_document,
                'extraction_confidence': rule.extraction_confidence,
                'source_evidence_sample': rule.conditions[0].source_evidence if rule.conditions else ""
            }
            
            yaml_data['rules'].append(rule_dict)
        
        return json.dumps(yaml_data, indent=2)
    
    def _find_context_around_phrase(self, content: str, phrase: str, context_length: int) -> str:
        """Find context around a phrase"""
        match = re.search(re.escape(phrase), content, re.IGNORECASE)
        if not match:
            return f"Context not found for: {phrase}"
        
        start = max(0, match.start() - context_length // 2)
        end = min(len(content), match.end() + context_length // 2)
        
        return content[start:end].strip()
    
    def _find_context_around_match(self, content: str, match, context_length: int) -> str:
        """Find context around a regex match"""
        start = max(0, match.start() - context_length // 2)
        end = min(len(content), match.end() + context_length // 2)
        
        return content[start:end].strip()
    
    def _generate_rule_id(self, base_name: str) -> str:
        """Generate unique rule ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        hash_suffix = hashlib.md5(base_name.encode()).hexdigest()[:8]
        return f"{base_name}_{timestamp}_{hash_suffix}"


def generate_detection_rules(document_content: str, document_name: str = "document", 
                           analyst_instructions: str = "") -> Tuple[List[DetectionRule], str]:
    """
    Generate detection rules from document content
    
    Args:
        document_content: Document text to analyze
        document_name: Name/identifier for source document  
        analyst_instructions: Additional context for rule generation
        
    Returns:
        Tuple of (generated_rules_list, yaml_export)
    """
    generator = DynamicRuleGenerator()
    rules = generator.generate_rules_from_document(document_content, document_name, analyst_instructions)
    yaml_export = generator.export_rules_yaml(rules, f"{document_name}_derived_rules")
    
    return rules, yaml_export


if __name__ == "__main__":
    # Test with sample content
    test_content = """
    Falsos Amigos Network of Domains and Social Media Accounts Uses AI Tools to Launder Reports 
    From Chinese State Media Outlet CGTN in Multiple Languages.
    
    Graphika identified a network of 11 domains and 16 companion social media accounts that laundered 
    exclusively English-language articles originally published by the Chinese state media outlet CGTN.
    The assets almost certainly used AI tools to translate and summarize articles from CGTN.
    Facebook pages ran ads to promote their content. The domain registrar for all 11 domains 
    is Alibaba Cloud Computing Ltd. located in Beijing, China. Posts received thousands of likes.
    """
    
    rules, yaml_output = generate_detection_rules(test_content, "atlas_test")
    print(f"Generated {len(rules)} rules:")
    for rule in rules:
        print(f"- {rule.name} (confidence: {rule.extraction_confidence:.2f})")
    
    print("\nYAML Export:")
    print(yaml_output)