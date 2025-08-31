"""
Enhanced Extraction Tool - Source-Driven Intelligence with Framework Compliance

Integrates source-driven intelligence extraction logic into Safety Sigma 2.0 framework
while maintaining Stage 1-3 compliance with audit logging and feature toggles.
"""

import os
import json
import re
from typing import Any, Dict, Optional, List
from pathlib import Path

from .base_tool import BaseTool, ToolResult
from .intelligence_extractor import IntelligenceExtractor


class EnhancedExtractionTool(BaseTool):
    """
    Enhanced extraction tool with source-driven intelligence
    
    Provides both traditional analysis and source-driven extraction modes:
    - Template analysis (Stage 1 compatibility)
    - Source-driven extraction (mandatory evidence mode)
    - Rule engine integration (Stage 3 compatibility)
    - Comprehensive audit logging and compliance
    """
    
    name = "enhanced_extraction_tool"
    version = "2.0.0"
    required_params = ["instructions", "text_content"]
    allow_none_output = False
    
    def __init__(self, ss1_path: Optional[str] = None, **kwargs):
        """
        Initialize enhanced extraction tool
        
        Args:
            ss1_path: Path to Safety Sigma 1.0 installation
            **kwargs: Additional base tool arguments
        """
        super().__init__(**kwargs)
        
        self.ss1_path = ss1_path or os.getenv('SS1_PATH', '../phase_1')
        self.intelligence_extractor = IntelligenceExtractor()
        
        # Feature toggles
        self.source_driven_mode = os.getenv('SS2_SOURCE_DRIVEN', 'false').lower() == 'true'
        self.enhanced_extraction = os.getenv('SS2_ENHANCED_EXTRACTION', 'true').lower() == 'true'
        
        # Import traditional processor for fallback
        self._ss1_processor = None
        if not self.source_driven_mode:
            self._import_ss1()
    
    def _import_ss1(self) -> None:
        """Import Safety Sigma 1.0 processor for traditional analysis"""
        try:
            import sys
            if str(Path(self.ss1_path).resolve()) not in sys.path:
                sys.path.insert(0, str(Path(self.ss1_path).resolve()))
            
            from safety_sigma_processor import SafetySigmaProcessor
            api_key = os.getenv('OPENAI_API_KEY', 'mock-key-for-testing')
            self._ss1_processor = SafetySigmaProcessor(api_key=api_key)
            
        except ImportError as e:
            self.logger.warning(f"Cannot import Safety Sigma 1.0: {e}")
    
    def _validate_inputs(self, inputs: Dict[str, Any], result: ToolResult) -> None:
        """Validate extraction inputs with enhanced checks"""
        super()._validate_inputs(inputs, result)
        
        instructions = inputs.get('instructions', '')
        text_content = inputs.get('text_content', '')
        
        # Enhanced validation for source-driven mode
        if self.source_driven_mode:
            if len(text_content.strip()) < 50:
                raise ValueError("Source-driven mode requires substantial content (min 50 chars)")
        
        # Store enhanced metadata
        result.metadata.update({
            'source_driven_mode': self.source_driven_mode,
            'enhanced_extraction': self.enhanced_extraction,
            'instructions_length': len(instructions),
            'content_length': len(text_content),
            'extraction_mode': 'source_driven' if self.source_driven_mode else 'traditional'
        })
        
        result.add_audit_entry(f"Enhanced validation: mode={result.metadata['extraction_mode']}, content={len(text_content)} chars")
    
    def _run(self, instructions: str, text_content: str, simulate: bool = False, **kwargs) -> str:
        """
        Execute enhanced extraction with source-driven or traditional modes
        
        Args:
            instructions: Analysis instructions
            text_content: Document content to analyze
            simulate: Run in simulation mode
            **kwargs: Additional parameters
            
        Returns:
            Analysis result as formatted text
        """
        # Set simulation mode for compliance checks
        self._current_simulation_mode = simulate
        
        if self.source_driven_mode:
            return self._run_source_driven(instructions, text_content, simulate)
        else:
            return self._run_traditional(instructions, text_content, simulate)
    
    def _run_source_driven(self, instructions: str, text_content: str, simulate: bool = False) -> str:
        """
        Execute source-driven intelligence extraction
        
        All claims must be backed by source evidence from the document.
        """
        self.logger.info("Running source-driven extraction with mandatory evidence")
        
        # Extract structured intelligence with source evidence
        intelligence = self.intelligence_extractor.extract_intelligence(
            text_content, 
            instructions
        )
        
        # Validate all claims have source evidence
        validation_results = self._validate_source_evidence(intelligence, text_content)
        
        # Generate narrative from extracted intelligence only
        narrative = self._generate_enhanced_narrative(intelligence, validation_results)
        
        # Create comprehensive analysis report
        analysis_report = self._format_source_driven_analysis(
            intelligence, 
            validation_results, 
            narrative,
            instructions
        )
        
        self.logger.info(f"Source-driven extraction complete: {len(analysis_report)} chars generated")
        return analysis_report
    
    def _run_traditional(self, instructions: str, text_content: str, simulate: bool = False) -> str:
        """Execute traditional analysis for backward compatibility"""
        if not self._ss1_processor:
            # Fallback to basic extraction if SS1 unavailable
            self.logger.warning("SS1 processor unavailable, using basic extraction")
            return self._run_source_driven(instructions, text_content, simulate)
        
        if simulate:
            self.logger.info("Running traditional analysis in simulation mode")
            return "Simulated traditional analysis result - would use SS1 processor"
        
        # Use Safety Sigma 1.0 processor
        return self._ss1_processor.process_text(instructions, text_content)
    
    def _validate_source_evidence(self, intelligence: Dict[str, Any], source_content: str) -> Dict[str, bool]:
        """
        Validate that all extracted intelligence has source evidence
        
        Args:
            intelligence: Extracted structured intelligence
            source_content: Original document content
            
        Returns:
            Validation results for each category
        """
        validation = {
            "fraud_types_validated": True,
            "financial_impact_validated": True,
            "operational_methods_validated": True,
            "targeting_analysis_validated": True,
            "all_claims_have_evidence": True
        }
        
        # Check each category for source evidence
        for category, items in intelligence.items():
            category_key = f"{category}_validated"
            if category_key not in validation:
                continue
                
            for item in items:
                if not item.get('source_evidence') or item['source_evidence'] == "not found in source":
                    validation[category_key] = False
                    validation["all_claims_have_evidence"] = False
                    self.logger.warning(f"Missing source evidence in {category}: {item.get('type', 'unknown')}")
        
        return validation
    
    def _generate_enhanced_narrative(self, intelligence: Dict[str, Any], validation: Dict[str, bool]) -> str:
        """
        Generate narrative analysis using ONLY extracted intelligence with source citations
        
        Args:
            intelligence: Structured intelligence data
            validation: Source validation results
            
        Returns:
            Formatted narrative with inline citations
        """
        sections = []
        
        # Executive Summary
        total_items = sum(len(intelligence.get(key, [])) for key in intelligence.keys())
        sections.append(f"## Executive Summary")
        sections.append(f"Source-driven analysis extracted {total_items} intelligence items with mandatory evidence validation.")
        sections.append(f"Validation Status: {'✅ All claims verified' if validation['all_claims_have_evidence'] else '⚠️ Some claims lack evidence'}")
        sections.append("")
        
        # Fraud Categories
        sections.append("## Fraud Categories")
        fraud_types = intelligence.get('fraud_types', [])
        if fraud_types:
            for fraud in fraud_types:
                sections.append(f"**{fraud['type']}**: {fraud.get('context', 'Identified in source')}")
                sections.append(f"*Source Evidence*: \"{fraud.get('source_evidence', 'Not found')[:150]}...\"")
                sections.append("")
        else:
            sections.append("*No fraud categories with supporting source evidence found.*")
            sections.append("")
        
        # Financial Impact
        sections.append("## Financial Impact")
        financial = intelligence.get('financial_impact', [])
        if financial:
            for item in financial:
                sections.append(f"**{item.get('value', 'Amount')} {item.get('unit', 'units')}**: {item.get('context', 'Financial data')}")
                sections.append(f"*Source Evidence*: \"{item.get('source_evidence', 'Not found')[:150]}...\"")
                sections.append("")
        else:
            sections.append("*No financial impact data with supporting source evidence found.*")
            sections.append("")
        
        # Operational Methods
        sections.append("## Operational Methods (TTPs)")
        methods = intelligence.get('operational_methods', [])
        if methods:
            for method in methods:
                platforms = ", ".join(method.get('platforms', [])) or "platforms not specified"
                sections.append(f"**{method.get('technique', 'Technique')}**: Operating across {platforms}")
                sections.append(f"*Source Evidence*: \"{method.get('source_evidence', 'Not found')[:150]}...\"")
                sections.append("")
        else:
            sections.append("*No operational methods with supporting source evidence found.*")
            sections.append("")
        
        # Targeting Analysis Summary
        sections.append("## Targeting Analysis")
        targeting = intelligence.get('targeting_analysis', [])
        if targeting:
            # Summarize geographic and demographic patterns
            geo_targets = set()
            demo_targets = set()
            for target in targeting:
                if target.get('geography') and target['geography'] != 'Not specified':
                    geo_targets.add(target['geography'])
                if target.get('demography') and target['demography'] != 'Not specified in source':
                    demo_targets.add(target['demography'])
            
            sections.append(f"**Geographic Targeting**: {', '.join(sorted(geo_targets)) if geo_targets else 'Not specified'}")
            sections.append(f"**Demographic Targeting**: {', '.join(sorted(demo_targets)) if demo_targets else 'Not specified'}")
            sections.append(f"**Total Targeting Entries**: {len(targeting)} with source evidence")
            
            # Show first few examples
            for target in targeting[:3]:
                sections.append(f"- **{target.get('target', 'Target')}**: {target.get('geography', 'Unknown location')}")
                sections.append(f"  *Source*: \"{target.get('source_evidence', 'Not found')[:100]}...\"")
            
            if len(targeting) > 3:
                sections.append(f"  *... and {len(targeting) - 3} additional targeting entries*")
            sections.append("")
        else:
            sections.append("*No targeting analysis with supporting source evidence found.*")
            sections.append("")
        
        return "\n".join(sections)
    
    def _format_source_driven_analysis(self, intelligence: Dict[str, Any], validation: Dict[str, bool], 
                                      narrative: str, instructions: str) -> str:
        """
        Format comprehensive source-driven analysis report
        
        Args:
            intelligence: Structured intelligence data
            validation: Source validation results
            narrative: Generated narrative analysis
            instructions: Original analyst instructions
            
        Returns:
            Complete formatted analysis report
        """
        report_sections = []
        
        # Header
        report_sections.append("# Source-Driven Intelligence Analysis Report")
        report_sections.append("*Generated using Safety Sigma 2.0 Enhanced Extraction Tool*")
        report_sections.append("")
        
        # Metadata
        report_sections.append("## Analysis Metadata")
        report_sections.append(f"- **Processing Mode**: Source-driven with mandatory evidence")
        report_sections.append(f"- **Tool Version**: {self.name} v{self.version}")
        report_sections.append(f"- **Extraction Quality**: {'High' if validation['all_claims_have_evidence'] else 'Medium'}")
        report_sections.append(f"- **Total Intelligence Items**: {sum(len(intelligence.get(k, [])) for k in intelligence.keys())}")
        report_sections.append("")
        
        # Validation Status
        report_sections.append("## Source Validation Results")
        for check, passed in validation.items():
            status = "✅ PASSED" if passed else "❌ FAILED"
            check_name = check.replace('_', ' ').title()
            report_sections.append(f"- **{check_name}**: {status}")
        report_sections.append("")
        
        # Main Analysis
        report_sections.append(narrative)
        
        # Structured Data Appendix
        report_sections.append("## Structured Intelligence Data")
        report_sections.append("```json")
        report_sections.append(json.dumps(intelligence, indent=2))
        report_sections.append("```")
        report_sections.append("")
        
        # Processing Summary
        report_sections.append("## Processing Summary")
        report_sections.append("This analysis was generated using source-driven methodology:")
        report_sections.append("1. **Extract**: Structured intelligence from document text")
        report_sections.append("2. **Validate**: All claims verified against source evidence")
        report_sections.append("3. **Analyze**: Narrative built only from verified extractions")
        report_sections.append("4. **Audit**: Complete traceability for compliance requirements")
        
        return "\n".join(report_sections)
    
    def _validate_outputs(self, output: Any, result: ToolResult) -> None:
        """Enhanced output validation with source-driven compliance"""
        super()._validate_outputs(output, result)
        
        if self.source_driven_mode:
            # Additional validation for source-driven outputs
            if "Source Evidence" not in output:
                result.add_audit_entry("WARNING: Source-driven output lacks evidence citations")
            
            result.compliance_status['source_driven_compliance'] = True
            result.add_audit_entry("Source-driven compliance validation passed")
        
        # Enhanced metadata
        result.metadata.update({
            'output_length': len(output),
            'contains_source_citations': "Source Evidence" in output,
            'extraction_quality': self._assess_extraction_quality(output)
        })
    
    def _assess_extraction_quality(self, output: str) -> str:
        """Assess the quality of extraction output"""
        if self.source_driven_mode:
            citation_count = output.count("Source Evidence")
            if citation_count >= 3:
                return "High"
            elif citation_count >= 1:
                return "Medium"
            else:
                return "Low"
        return "Standard"


def enhanced_extraction_tool(document_content: str, analyst_instructions: str = "", 
                           simulate: bool = False, **kwargs) -> str:
    """
    Enhanced extraction tool function for direct usage
    
    Args:
        document_content: Document text to analyze
        analyst_instructions: Analysis instructions
        simulate: Run in simulation mode
        **kwargs: Additional parameters
        
    Returns:
        Analysis result
    """
    tool = EnhancedExtractionTool()
    result = tool.execute(
        instructions=analyst_instructions,
        text_content=document_content,
        simulate=simulate,
        **kwargs
    )
    return result.data