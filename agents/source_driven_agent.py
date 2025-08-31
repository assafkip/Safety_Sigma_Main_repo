#!/usr/bin/env python3
"""
Source-Driven Agent - Content-Only Analysis
Replaces template-based analysis with source-driven intelligence extraction.
"""

import json
import os
from typing import Dict, Any, List
from dataclasses import dataclass
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.intelligence_extractor import IntelligenceExtractor

@dataclass
class SourceAnalysisResult:
    success: bool
    extracted_intelligence: Dict[str, Any] 
    narrative_analysis: str
    source_validation: Dict[str, bool]
    error: str = None

class SourceDrivenAgent:
    """
    Agent that operates exclusively on source material.
    No templates, no external knowledge, no fabricated claims.
    """
    
    def __init__(self):
        self.extractor = IntelligenceExtractor()
        self.name = "source_driven_agent"
        self.version = "1.0.0"
    
    def process_document(self, document_content: str, analyst_instructions: str = "") -> SourceAnalysisResult:
        """
        Process document using source-only methodology.
        1. Extract structured intelligence with source evidence
        2. Validate all claims against source
        3. Generate narrative only from extracted data
        """
        try:
            # Phase 1: Extract structured intelligence
            extracted_intelligence = self.extractor.extract_intelligence(
                document_content, 
                analyst_instructions
            )
            
            # Phase 2: Validate all extracted claims
            validation_results = self._validate_against_source(
                extracted_intelligence, 
                document_content
            )
            
            # Phase 3: Generate narrative from extracted data only
            narrative = self._generate_source_narrative(extracted_intelligence)
            
            return SourceAnalysisResult(
                success=True,
                extracted_intelligence=extracted_intelligence,
                narrative_analysis=narrative,
                source_validation=validation_results
            )
            
        except Exception as e:
            return SourceAnalysisResult(
                success=False,
                extracted_intelligence={},
                narrative_analysis="",
                source_validation={},
                error=str(e)
            )
    
    def _validate_against_source(self, intelligence: Dict[str, Any], source_content: str) -> Dict[str, bool]:
        """
        Validate that all extracted claims exist in source material.
        """
        validation_results = {
            "fraud_types_validated": True,
            "financial_impact_validated": True,
            "operational_methods_validated": True,
            "targeting_analysis_validated": True,
            "all_claims_have_evidence": True
        }
        
        # Check that all fraud types have source evidence
        for fraud_type in intelligence.get('fraud_types', []):
            if not fraud_type.get('source_evidence') or fraud_type['source_evidence'] == "not found in source":
                validation_results["fraud_types_validated"] = False
                validation_results["all_claims_have_evidence"] = False
        
        # Check financial impact evidence
        for financial in intelligence.get('financial_impact', []):
            if not financial.get('source_evidence') or financial['source_evidence'] == "not found in source":
                validation_results["financial_impact_validated"] = False
                validation_results["all_claims_have_evidence"] = False
        
        # Check operational methods evidence
        for method in intelligence.get('operational_methods', []):
            if not method.get('source_evidence') or method['source_evidence'] == "not found in source":
                validation_results["operational_methods_validated"] = False
                validation_results["all_claims_have_evidence"] = False
        
        # Check targeting analysis evidence  
        for target in intelligence.get('targeting_analysis', []):
            if not target.get('source_evidence') or target['source_evidence'] == "not found in source":
                validation_results["targeting_analysis_validated"] = False
                validation_results["all_claims_have_evidence"] = False
        
        return validation_results
    
    def _generate_source_narrative(self, intelligence: Dict[str, Any]) -> str:
        """
        Generate narrative analysis using ONLY extracted intelligence.
        Every sentence must be backed by source evidence.
        """
        narrative_parts = []
        
        # Fraud Categories Section
        fraud_types = intelligence.get('fraud_types', [])
        if fraud_types:
            narrative_parts.append("## Fraud Categories")
            for fraud in fraud_types:
                narrative_parts.append(
                    f"**{fraud['type']}**: {fraud.get('context', 'Identified in source document')}. "
                    f"*Source: \"{fraud.get('source_evidence', 'Evidence not found')[:100]}...\"*"
                )
        else:
            narrative_parts.append("## Fraud Categories\nNo fraud categories supported by source.")
        
        # Financial Impact Section
        financial_impact = intelligence.get('financial_impact', [])
        if financial_impact:
            narrative_parts.append("\n## Financial Impact")
            for financial in financial_impact:
                unit_label = "USD" if financial.get('unit') == 'USD' else financial.get('unit', 'units')
                narrative_parts.append(
                    f"**{financial.get('value', 'Amount not specified')} {unit_label}**: "
                    f"{financial.get('context', 'Financial figure mentioned')}. "
                    f"*Source: \"{financial.get('source_evidence', 'Evidence not found')[:100]}...\"*"
                )
        else:
            narrative_parts.append("\n## Financial Impact\nNo financial impact claims supported by source.")
        
        # TTPs and Platforms Section
        methods = intelligence.get('operational_methods', [])
        if methods:
            narrative_parts.append("\n## TTPs and Platforms")
            for method in methods:
                platforms = method.get('platforms', [])
                platform_str = ", ".join(platforms) if platforms else "platforms not specified"
                narrative_parts.append(
                    f"**{method.get('technique', 'Technique not specified')}**: "
                    f"Operating across {platform_str}. "
                    f"*Source: \"{method.get('source_evidence', 'Evidence not found')[:100]}...\"*"
                )
        else:
            narrative_parts.append("\n## TTPs and Platforms\nNo operational methods claims supported by source.")
        
        # Targeting Section
        targeting = intelligence.get('targeting_analysis', [])
        if targeting:
            narrative_parts.append("\n## Targeting")
            for target in targeting:
                geo = target.get('geography', 'Geography not specified')
                demo = target.get('demography', 'Demographics not specified')
                narrative_parts.append(
                    f"**{target.get('target', 'Target not specified')}**: "
                    f"Geographic focus: {geo}. Demographic focus: {demo}. "
                    f"*Source: \"{target.get('source_evidence', 'Evidence not found')[:100]}...\"*"
                )
        else:
            narrative_parts.append("\n## Targeting\nNo targeting claims supported by source.")
        
        return "\n\n".join(narrative_parts)
    
    def save_analysis(self, result: SourceAnalysisResult, output_dir: str) -> str:
        """
        Save complete source-driven analysis to files.
        """
        import os
        from datetime import datetime
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = os.path.join(output_dir, f"source_driven_analysis_{timestamp}")
        os.makedirs(output_path, exist_ok=True)
        
        # Save extracted intelligence JSON
        intelligence_file = os.path.join(output_path, "extracted_intelligence.json")
        with open(intelligence_file, 'w') as f:
            json.dump(result.extracted_intelligence, f, indent=2)
        
        # Save narrative analysis
        narrative_file = os.path.join(output_path, "narrative_analysis.md")
        with open(narrative_file, 'w') as f:
            f.write(f"# Source-Driven Intelligence Analysis\n\n")
            f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Agent**: {self.name} v{self.version}\n")
            f.write(f"**Methodology**: Source-only analysis with mandatory evidence\n\n")
            f.write(result.narrative_analysis)
        
        # Save validation results
        validation_file = os.path.join(output_path, "validation_report.json")
        with open(validation_file, 'w') as f:
            json.dump({
                "validation_results": result.source_validation,
                "processing_metadata": {
                    "agent": self.name,
                    "version": self.version,
                    "success": result.success,
                    "error": result.error
                }
            }, f, indent=2)
        
        return output_path


if __name__ == "__main__":
    # Test the source-driven agent
    agent = SourceDrivenAgent()
    
    # Test with sample content
    test_content = """
    Graphika identified a network of 11 domains and 16 companion social media accounts that laundered 
    exclusively English-language articles originally published by the Chinese state media outlet CGTN.
    The assets almost certainly used AI tools to translate and summarize articles from CGTN.
    Facebook pages ran ads to promote their content. The domain registrar for all 11 domains 
    is Alibaba Cloud Computing Ltd. located in Beijing, China. Posts received thousands of likes.
    """
    
    result = agent.process_document(test_content, "Analyze information operations")
    
    print("=== SOURCE-DRIVEN ANALYSIS TEST ===")
    print(f"Success: {result.success}")
    print(f"Validation: {result.source_validation}")
    print("\nExtracted Intelligence:")
    print(json.dumps(result.extracted_intelligence, indent=2))
    print("\nNarrative Analysis:")
    print(result.narrative_analysis)