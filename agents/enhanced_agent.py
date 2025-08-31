"""
Enhanced Agent for Safety Sigma 2.0 Stage 3

Advanced agent with rule engine integration for sophisticated decision making.
Builds upon Stage 2 SimpleAgent with configurable rule-based workflow selection.
"""

import time
from typing import Any, Dict, List
from pathlib import Path

from .base_agent import BaseAgent, AgentDecision, AgentResult
from orchestration.tool_orchestrator import ToolOrchestrator
from tools.enhanced_extraction_tool import EnhancedExtractionTool
from rules.document_classifier import DocumentClassifierEngine


class EnhancedAgent(BaseAgent):
    """
    Enhanced agent with rule engine integration
    
    Features:
    - YAML-based rule configuration
    - Advanced decision trees with conditional logic
    - Sophisticated document analysis and classification
    - Configurable workflow selection with confidence scoring
    - Comprehensive audit logging of rule evaluations
    """
    
    name = "enhanced_agent"
    version = "1.0.0"
    
    # Supported workflows (expanded for Stage 3)
    supported_workflows = [
        'fraud_analysis_workflow',
        'threat_intelligence_workflow', 
        'policy_analysis_workflow',
        'general_analysis_workflow',
        'technical_analysis_workflow',  # New in Stage 3
        'compliance_audit_workflow',    # New in Stage 3
    ]
    
    def __init__(self, rules_dir: str = None, **kwargs):
        """
        Initialize enhanced agent with rule engine
        
        Args:
            rules_dir: Directory containing rule configuration files
            **kwargs: Additional base agent parameters
        """
        super().__init__(**kwargs)
        
        # Initialize rule engine
        self.rule_engine = DocumentClassifierEngine(rules_dir=rules_dir)
        
        # Initialize tool orchestrator with enhanced extraction
        self.tool_orchestrator = ToolOrchestrator(audit_dir=str(self.audit_dir))
        self.enhanced_extraction_tool = EnhancedExtractionTool()
        
        # Load default ruleset
        try:
            self.rule_engine.load_rules('document_classification')
            self.logger.info("Loaded document classification rules")
        except Exception as e:
            self.logger.warning(f"Could not load default rules: {e}")
    
    def _analyze_inputs(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhanced input analysis using rule engine
        
        Args:
            inputs: Must contain 'document_content' or 'pdf_file', and 'instructions'
            
        Returns:
            Comprehensive input analysis results
        """
        # Extract parameters
        document_content = inputs.get('document_content', '')
        instructions = inputs.get('instructions', '')
        pdf_file = inputs.get('pdf_file', '')
        
        # If no document content but have PDF file, note that for extraction
        if not document_content and pdf_file:
            document_content = f"[PDF FILE: {pdf_file}] - Content will be extracted during processing"
        
        # Use rule engine for document analysis
        try:
            # Filter out duplicate keys from inputs
            filtered_inputs = {k: v for k, v in inputs.items() 
                             if k not in ['document_content', 'instructions', 'pdf_file']}
            
            classification_result = self.rule_engine.classify_document(
                document_content=document_content,
                instructions=instructions,
                pdf_file=pdf_file,
                **filtered_inputs  # Pass through additional parameters
            )
            
            # Enhanced analysis combining rule engine results with traditional analysis
            analysis = {
                # Rule engine results
                'rule_classification': classification_result['classification'],
                'rule_recommended_workflow': classification_result['recommended_workflow'],
                'rule_confidence_score': classification_result['confidence_score'],
                'rule_matched_rules': classification_result['matched_rules'],
                'rule_actions': classification_result['actions'],
                'rule_decision_factors': classification_result['decision_factors'],
                
                # Traditional analysis (for backward compatibility)
                'document_type': self._map_workflow_to_document_type(classification_result['recommended_workflow']),
                'document_type_confidence': classification_result['confidence_score'],
                'complexity_level': self._assess_complexity(classification_result['context']),
                'complexity_confidence': 0.85,
                
                # Enhanced analysis
                'context': classification_result['context'],
                'keyword_analysis': classification_result['decision_factors']['keyword_analysis'],
                'structure_analysis': classification_result['decision_factors']['structure_analysis'],
                'instruction_analysis': classification_result['decision_factors']['instruction_analysis'],
                'file_analysis': {
                    'has_pdf': bool(pdf_file),
                    'pdf_filename': pdf_file,
                    'estimated_size': 'large' if classification_result['context']['word_count'] > 2000 
                                   else 'medium' if classification_result['context']['word_count'] > 500 
                                   else 'small'
                },
                
                # Content characteristics
                'content_length': len(document_content),
                'word_count': classification_result['context']['word_count'],
                'has_structured_content': classification_result['context']['has_headers'] or classification_result['context']['has_tables'],
                'has_contact_info': classification_result['context']['has_emails'] or classification_result['context']['has_phone_numbers'],
                'has_financial_data': classification_result['context']['has_financial_data'],
            }
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Rule engine analysis failed: {e}")
            # Fallback to simple analysis
            return self._fallback_analysis(document_content, instructions, pdf_file)
    
    def _make_decision(self, decision_id: str, input_analysis: Dict[str, Any], inputs: Dict[str, Any]) -> AgentDecision:
        """
        Make workflow selection decision using rule engine results
        
        Args:
            decision_id: Unique decision identifier
            input_analysis: Results from input analysis
            inputs: Original input parameters
            
        Returns:
            AgentDecision with rule-based workflow selection and reasoning
        """
        # Extract rule engine results
        rule_classification = input_analysis.get('rule_classification', {})
        recommended_workflow = input_analysis.get('rule_recommended_workflow', 'general_analysis_workflow')
        rule_confidence = input_analysis.get('rule_confidence_score', 0.7)
        matched_rules = input_analysis.get('rule_matched_rules', [])
        decision_factors = input_analysis.get('rule_decision_factors', {})
        
        # Build comprehensive reasoning
        reasoning = []
        reasoning.append(f"Rule engine analysis completed with {len(matched_rules)} matching rules")
        
        # Add keyword analysis reasoning
        keyword_analysis = decision_factors.get('keyword_analysis', {})
        if keyword_analysis.get('fraud_density', 0) > 0.01:
            reasoning.append(f"High fraud keyword density: {keyword_analysis['fraud_density']:.4f}")
        if keyword_analysis.get('threat_density', 0) > 0.01:
            reasoning.append(f"Threat indicators detected with density: {keyword_analysis['threat_density']:.4f}")
        if keyword_analysis.get('policy_density', 0) > 0.008:
            reasoning.append(f"Policy/compliance content detected with density: {keyword_analysis['policy_density']:.4f}")
        
        # Add structure analysis reasoning
        structure_analysis = decision_factors.get('structure_analysis', {})
        if structure_analysis.get('has_financial_data'):
            reasoning.append("Financial data patterns detected in document")
        if structure_analysis.get('has_headers') and structure_analysis.get('has_lists'):
            reasoning.append("Well-structured document with headers and lists detected")
        
        # Add instruction analysis reasoning
        instruction_analysis = decision_factors.get('instruction_analysis', {})
        if instruction_analysis.get('mentions_fraud'):
            reasoning.append("Instructions explicitly mention fraud analysis")
        if instruction_analysis.get('mentions_threat'):
            reasoning.append("Instructions explicitly mention threat analysis")
        if instruction_analysis.get('mentions_policy'):
            reasoning.append("Instructions explicitly mention policy/compliance analysis")
        
        # Add matched rules to reasoning
        if matched_rules:
            reasoning.append(f"Matched decision rules: {', '.join(matched_rules)}")
        
        reasoning.append(f"Selected {recommended_workflow} with confidence {rule_confidence:.2f}")
        
        # Enhanced decision logic explanation
        decision_logic = f"""
Advanced Rule Engine Decision Logic (Stage 3):
1. YAML-based rule evaluation with conditional logic trees
2. Multi-dimensional document analysis:
   - Keyword density analysis with domain-specific vocabularies
   - Document structure pattern recognition
   - Instruction intent analysis
   - Content complexity assessment
3. Rule confidence scoring and accumulation
4. Workflow recommendation with evidence-based reasoning
5. Comprehensive audit trail with decision factors

Rule Engine Results:
- Evaluated Rules: {len(rule_classification.get('root_results', []))}
- Matched Rules: {len(matched_rules)}
- Confidence Boosts Applied: {rule_classification.get('total_confidence_boost', 0):.3f}
- Final Confidence Score: {rule_confidence:.3f}
        """.strip()
        
        return AgentDecision(
            decision_id=decision_id,
            agent_name=self.name,
            agent_version=self.version,
            timestamp=time.time(),
            input_analysis=input_analysis,
            decision_logic=decision_logic,
            selected_workflow=recommended_workflow,
            confidence_score=rule_confidence,
            reasoning=reasoning,
            metadata={
                'rule_engine_version': '1.0.0',
                'rule_classification': rule_classification,
                'matched_rules': matched_rules,
                'decision_factors': decision_factors,
                'workflow_mapping': self._get_workflow_mapping(),
                'fallback_used': False
            }
        )
    
    def _execute_workflow(self, decision: AgentDecision, inputs: Dict[str, Any], result: AgentResult) -> Any:
        """
        Execute selected workflow with rule engine enhancements
        
        Args:
            decision: Agent decision with selected workflow
            inputs: Original input parameters
            result: Agent result for audit trail
            
        Returns:
            Enhanced workflow execution result
        """
        workflow_name = decision.selected_workflow
        result.add_audit_entry(f"Executing workflow: {workflow_name}")
        
        # Get rule actions from decision metadata
        rule_actions = decision.metadata.get('rule_classification', {}).get('all_actions', [])
        
        # Apply rule-based instruction enhancements
        enhanced_instructions = self._apply_rule_enhancements(
            inputs.get('instructions', ''), 
            rule_actions, 
            workflow_name
        )
        
        result.add_audit_entry(f"Applied {len(rule_actions)} rule-based enhancements")
        
        try:
            # Check if source-driven mode is enabled
            import os
            source_driven_mode = os.getenv('SS2_SOURCE_DRIVEN', 'false').lower() == 'true'
            
            if source_driven_mode:
                # Use enhanced extraction tool for source-driven analysis
                result.add_audit_entry("Using enhanced source-driven extraction")
                
                # Get document content (extract from PDF if needed)
                document_content = inputs.get('document_content', '')
                if not document_content and inputs.get('pdf_file'):
                    # Extract PDF content first
                    from tools.pdf_tool import PDFTool
                    pdf_tool = PDFTool()
                    pdf_result = pdf_tool.execute(pdf_file=inputs['pdf_file'])
                    document_content = pdf_result.data
                
                # Run enhanced extraction
                extraction_result = self.enhanced_extraction_tool.execute(
                    instructions=enhanced_instructions,
                    text_content=document_content,
                    simulate=inputs.get('simulate', True)
                )
                
                # Create orchestration-like result for compatibility
                class SourceDrivenResult:
                    def __init__(self, analysis_data):
                        self.success = True
                        self.steps_executed = 2  # PDF + Enhanced Extraction
                        self.step_results = {'enhanced_extraction': extraction_result}
                        self.context = {'analysis_result': analysis_data}
                        self.error = None
                
                orchestration_result = SourceDrivenResult(extraction_result.data)
                result.add_audit_entry("Source-driven extraction completed successfully")
                
            else:
                # Execute through traditional tool orchestrator
                orchestration_result = self.tool_orchestrator.execute_safety_sigma_pipeline(
                    pdf_file=inputs.get('pdf_file', ''),
                    instructions=enhanced_instructions,
                    output_dir=inputs.get('output_dir', '.'),
                    simulate=inputs.get('simulate', True)  # Default to simulation for Stage 3
                )
            
            # Store tool results for audit trail
            result.tool_results = list(orchestration_result.step_results.values())
            
            if orchestration_result.success:
                result.add_audit_entry(f"Workflow {workflow_name} completed successfully")
                result.add_audit_entry(f"Tools executed: {orchestration_result.steps_executed}/{len(self.tool_orchestrator.ss_pipeline)}")
                
                # Create enhanced result with rule engine metadata
                enhanced_result = self._create_enhanced_result(orchestration_result, decision)
                return enhanced_result
            else:
                error_msg = f"Workflow {workflow_name} failed: {orchestration_result.error}"
                result.add_audit_entry(error_msg)
                raise RuntimeError(error_msg)
                
        except Exception as e:
            result.add_audit_entry(f"Workflow execution error: {str(e)}")
            raise
    
    def _apply_rule_enhancements(self, instructions: str, rule_actions: List[Dict], workflow_name: str) -> str:
        """Apply rule-based instruction enhancements"""
        enhanced_instructions = instructions
        
        # Apply rule actions
        for action in rule_actions:
            if action.get('type') == 'enhance_instructions':
                enhancement = action.get('enhancement', '')
                if enhancement == 'fraud_detection_focus':
                    enhanced_instructions += "\\n\\nSPECIAL FOCUS: Pay particular attention to fraud indicators, financial irregularities, and deceptive practices."
                elif enhancement == 'technical_threat_focus':
                    enhanced_instructions += "\\n\\nTECHNICAL FOCUS: Analyze technical threat indicators, security vulnerabilities, and attack patterns."
        
        # Add workflow-specific enhancements
        if workflow_name == 'fraud_analysis_workflow':
            enhanced_instructions += f"""\\n\\n=== STAGE 3 RULE-BASED FRAUD ANALYSIS ===
This analysis is enhanced by the Stage 3 rule engine with advanced decision trees.
Focus areas determined by rule evaluation:
- Financial transaction patterns
- Deceptive language indicators
- Suspicious account activities
- Regulatory compliance violations
Enhanced by: {self.name} v{self.version}
"""
        elif workflow_name == 'threat_intelligence_workflow':
            enhanced_instructions += f"""\\n\\n=== STAGE 3 RULE-BASED THREAT ANALYSIS ===
This analysis uses advanced rule trees for threat classification.
Technical focus areas:
- Attack vector identification
- Vulnerability assessment
- Security control gaps
- Threat actor attribution
Enhanced by: {self.name} v{self.version}
"""
        elif workflow_name == 'policy_analysis_workflow':
            enhanced_instructions += f"""\\n\\n=== STAGE 3 RULE-BASED POLICY ANALYSIS ===
This analysis applies compliance-focused rule evaluation.
Regulatory focus areas:
- Policy adherence assessment
- Compliance gap identification
- Regulatory requirement mapping
- Control effectiveness evaluation
Enhanced by: {self.name} v{self.version}
"""
        
        return enhanced_instructions
    
    def _create_enhanced_result(self, orchestration_result: Any, decision: AgentDecision) -> Dict[str, Any]:
        """Create enhanced result with rule engine metadata"""
        return {
            'orchestration_result': orchestration_result,
            'agent_decision': decision,
            'rule_engine_version': '1.0.0',
            'enhanced_by_stage3': True,
            'analysis_result': orchestration_result.context.get('analysis_result', 'No analysis result available'),
            'rule_matched_count': len(decision.metadata.get('matched_rules', [])),
            'decision_confidence': decision.confidence_score,
            'workflow_selected': decision.selected_workflow,
            'rule_enhancements_applied': len(decision.metadata.get('rule_classification', {}).get('all_actions', []))
        }
    
    def _map_workflow_to_document_type(self, workflow: str) -> str:
        """Map workflow name to document type for backward compatibility"""
        mapping = {
            'fraud_analysis_workflow': 'fraud_analysis',
            'threat_intelligence_workflow': 'threat_intelligence',
            'policy_analysis_workflow': 'policy_analysis',
            'technical_analysis_workflow': 'technical_analysis',
            'compliance_audit_workflow': 'compliance_audit',
            'general_analysis_workflow': 'general_analysis'
        }
        return mapping.get(workflow, 'general_analysis')
    
    def _assess_complexity(self, context: Dict[str, Any]) -> str:
        """Assess document complexity from context"""
        word_count = context.get('word_count', 0)
        has_structure = context.get('has_headers', False) or context.get('has_tables', False)
        technical_density = context.get('technical_keyword_density', 0)
        
        if word_count > 2000 and (has_structure or technical_density > 0.01):
            return 'complex'
        elif word_count > 500 and (has_structure or technical_density > 0.005):
            return 'moderate'
        else:
            return 'simple'
    
    def _fallback_analysis(self, document_content: str, instructions: str, pdf_file: str) -> Dict[str, Any]:
        """Fallback analysis when rule engine fails"""
        return {
            'document_type': 'general_analysis',
            'document_type_confidence': 0.5,
            'complexity_level': 'moderate',
            'complexity_confidence': 0.6,
            'rule_engine_failed': True,
            'fallback_used': True,
            'content_length': len(document_content),
            'has_pdf_file': bool(pdf_file)
        }
    
    def _get_workflow_mapping(self) -> Dict[str, str]:
        """Get workflow to description mapping"""
        return {
            'fraud_analysis_workflow': 'Fraud Detection and Financial Crime Analysis',
            'threat_intelligence_workflow': 'Cybersecurity Threat Intelligence Analysis', 
            'policy_analysis_workflow': 'Policy Compliance and Regulatory Analysis',
            'technical_analysis_workflow': 'Technical Documentation Analysis',
            'compliance_audit_workflow': 'Compliance Audit and Control Assessment',
            'general_analysis_workflow': 'General Purpose Document Analysis'
        }
    
    def get_rule_engine_info(self) -> Dict[str, Any]:
        """Get information about the rule engine configuration"""
        return {
            'engine_type': 'DocumentClassifierEngine',
            'engine_version': '1.0.0',
            'supported_rulesets': self.rule_engine.get_supported_rulesets(),
            'loaded_rulesets': list(self.rule_engine.rulesets.keys()),
            'rules_directory': str(self.rule_engine.rules_dir)
        }