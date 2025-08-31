"""
Simple Agent for Safety Sigma 2.0

Implements deterministic workflow selection with hardcoded decision trees.
Provides input analysis and routes through tool abstraction layer.
"""

import time
from typing import Any, Dict, List
from pathlib import Path

from .base_agent import BaseAgent, AgentDecision, AgentResult, analyze_document_type, analyze_document_complexity, analyze_document_structure
from orchestration.tool_orchestrator import ToolOrchestrator


class SimpleAgent(BaseAgent):
    """
    Simple agent with deterministic workflow selection
    
    Features:
    - Input analysis for document type and complexity
    - Hardcoded decision trees for workflow selection  
    - Integration with tool abstraction layer
    - Comprehensive audit logging of all decisions
    """
    
    name = "simple_agent"
    version = "1.0.0"
    
    # Supported workflows (hardcoded for Stage 2)
    supported_workflows = [
        'fraud_analysis_workflow',
        'threat_intelligence_workflow', 
        'policy_analysis_workflow',
        'general_analysis_workflow',
    ]
    
    def __init__(self, **kwargs):
        """Initialize simple agent with tool orchestrator"""
        super().__init__(**kwargs)
        self.tool_orchestrator = ToolOrchestrator(audit_dir=str(self.audit_dir))
    
    def _analyze_inputs(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze inputs to determine document characteristics
        
        Args:
            inputs: Must contain 'pdf_file' and 'instructions'
            
        Returns:
            Dictionary with comprehensive input analysis
        """
        # Extract content for analysis
        pdf_file = inputs.get('pdf_file', '')
        instructions = inputs.get('instructions', '')
        
        # Get document content (simplified for Stage 2)
        # In a real implementation, this would extract PDF text first
        document_content = inputs.get('document_content', '') or instructions
        
        # Analyze document type
        doc_type, type_confidence = analyze_document_type(document_content)
        
        # Analyze complexity
        complexity, complexity_confidence = analyze_document_complexity(document_content)
        
        # Analyze structure
        structure_analysis = analyze_document_structure(document_content)
        
        # Analyze instructions
        instruction_analysis = self._analyze_instructions(instructions)
        
        # File analysis
        file_analysis = self._analyze_file_characteristics(pdf_file)
        
        return {
            'document_type': doc_type,
            'document_type_confidence': type_confidence,
            'complexity_level': complexity,
            'complexity_confidence': complexity_confidence,
            'structure_analysis': structure_analysis,
            'instruction_analysis': instruction_analysis,
            'file_analysis': file_analysis,
            'content_length': len(document_content),
            'analysis_timestamp': time.time(),
        }
    
    def _analyze_instructions(self, instructions: str) -> Dict[str, Any]:
        """Analyze processing instructions"""
        instructions_lower = instructions.lower()
        
        return {
            'length': len(instructions),
            'word_count': len(instructions.split()),
            'has_specific_fields': bool('extract' in instructions_lower and 'field' in instructions_lower),
            'requests_structured_output': bool('json' in instructions_lower or 'format' in instructions_lower),
            'mentions_compliance': bool('compliance' in instructions_lower or 'regulation' in instructions_lower),
            'mentions_detection': bool('detect' in instructions_lower or 'identify' in instructions_lower),
            'urgency_indicators': sum(1 for word in ['urgent', 'immediate', 'critical', 'priority'] if word in instructions_lower),
        }
    
    def _analyze_file_characteristics(self, pdf_file: str) -> Dict[str, Any]:
        """Analyze file characteristics"""
        file_path = Path(pdf_file) if pdf_file else None
        
        analysis = {
            'file_provided': bool(pdf_file),
            'file_exists': file_path.exists() if file_path else False,
            'file_extension': file_path.suffix.lower() if file_path else '',
            'estimated_size': 'unknown',
        }
        
        if file_path and file_path.exists():
            try:
                file_size = file_path.stat().st_size
                analysis.update({
                    'file_size_bytes': file_size,
                    'estimated_size': self._categorize_file_size(file_size),
                })
            except Exception:
                pass
        
        return analysis
    
    def _categorize_file_size(self, size_bytes: int) -> str:
        """Categorize file size for workflow selection"""
        if size_bytes < 100_000:  # < 100KB
            return 'small'
        elif size_bytes < 1_000_000:  # < 1MB
            return 'medium'
        elif size_bytes < 10_000_000:  # < 10MB
            return 'large'
        else:
            return 'very_large'
    
    def _make_decision(self, decision_id: str, input_analysis: Dict[str, Any], inputs: Dict[str, Any]) -> AgentDecision:
        """
        Make deterministic workflow selection decision using hardcoded logic
        
        Args:
            decision_id: Unique decision identifier
            input_analysis: Results from input analysis
            inputs: Original input parameters
            
        Returns:
            AgentDecision with selected workflow and complete reasoning
        """
        reasoning = []
        workflow_scores = {}
        
        # Decision Tree Logic (Deterministic and Hardcoded)
        
        # Primary decision based on document type
        doc_type = input_analysis.get('document_type', 'general_analysis')
        type_confidence = input_analysis.get('document_type_confidence', 0.5)
        
        reasoning.append(f"Document type detected: {doc_type} (confidence: {type_confidence:.2f})")
        
        if doc_type == 'fraud_analysis' and type_confidence > 0.8:
            workflow_scores['fraud_analysis_workflow'] = 0.9
            reasoning.append("High confidence fraud content detected -> fraud_analysis_workflow prioritized")
        elif doc_type == 'threat_intelligence' and type_confidence > 0.8:
            workflow_scores['threat_intelligence_workflow'] = 0.9
            reasoning.append("High confidence threat intelligence detected -> threat_intelligence_workflow prioritized")
        elif doc_type == 'policy_analysis' and type_confidence > 0.8:
            workflow_scores['policy_analysis_workflow'] = 0.9
            reasoning.append("High confidence policy content detected -> policy_analysis_workflow prioritized")
        else:
            workflow_scores['general_analysis_workflow'] = 0.7
            reasoning.append("Using general analysis workflow as fallback")
        
        # Complexity adjustments
        complexity = input_analysis.get('complexity_level', 'moderate')
        if complexity == 'complex':
            # Boost specialized workflows for complex documents
            for workflow in ['fraud_analysis_workflow', 'threat_intelligence_workflow', 'policy_analysis_workflow']:
                if workflow in workflow_scores:
                    workflow_scores[workflow] = min(0.95, workflow_scores[workflow] + 0.05)
                    reasoning.append(f"Complex document detected -> boosted {workflow} confidence")
        
        # Instruction analysis adjustments
        instruction_analysis = input_analysis.get('instruction_analysis', {})
        if instruction_analysis.get('mentions_compliance', False):
            workflow_scores['policy_analysis_workflow'] = max(0.8, workflow_scores.get('policy_analysis_workflow', 0.6))
            reasoning.append("Compliance mentioned in instructions -> policy_analysis_workflow boosted")
        
        if instruction_analysis.get('mentions_detection', False):
            workflow_scores['fraud_analysis_workflow'] = max(0.75, workflow_scores.get('fraud_analysis_workflow', 0.6))
            workflow_scores['threat_intelligence_workflow'] = max(0.75, workflow_scores.get('threat_intelligence_workflow', 0.6))
            reasoning.append("Detection focus in instructions -> specialized workflows boosted")
        
        # File size considerations
        file_analysis = input_analysis.get('file_analysis', {})
        estimated_size = file_analysis.get('estimated_size', 'unknown')
        if estimated_size == 'very_large':
            # Prefer general workflow for very large files (performance consideration)
            workflow_scores['general_analysis_workflow'] = max(0.75, workflow_scores.get('general_analysis_workflow', 0.6))
            reasoning.append("Very large file detected -> general_analysis_workflow preferred for performance")
        
        # Select workflow with highest score
        if not workflow_scores:
            selected_workflow = 'general_analysis_workflow'
            confidence = 0.5
            reasoning.append("No specific workflow selected -> defaulting to general_analysis_workflow")
        else:
            selected_workflow = max(workflow_scores.items(), key=lambda x: x[1])[0]
            confidence = workflow_scores[selected_workflow]
            reasoning.append(f"Selected {selected_workflow} with confidence {confidence:.2f}")
        
        # Decision logic explanation
        decision_logic = f"""
Hardcoded Decision Tree Logic:
1. Primary classification by document type analysis
2. Confidence threshold filtering (>0.8 for specialized workflows)  
3. Complexity-based workflow boosting
4. Instruction analysis adjustments
5. File size performance considerations
6. Highest scoring workflow selection
        """.strip()
        
        return AgentDecision(
            decision_id=decision_id,
            agent_name=self.name,
            agent_version=self.version,
            timestamp=time.time(),
            input_analysis=input_analysis,
            decision_logic=decision_logic,
            selected_workflow=selected_workflow,
            confidence_score=confidence,
            reasoning=reasoning,
            metadata={
                'workflow_scores': workflow_scores,
                'decision_factors': {
                    'document_type': doc_type,
                    'complexity_level': complexity,
                    'instruction_focus': instruction_analysis,
                    'file_characteristics': file_analysis,
                }
            }
        )
    
    def _execute_workflow(self, decision: AgentDecision, inputs: Dict[str, Any], result: AgentResult) -> Any:
        """
        Execute selected workflow through tool abstraction layer
        
        Args:
            decision: Agent decision with selected workflow
            inputs: Original input parameters
            result: Agent result for audit trail
            
        Returns:
            Workflow execution result
        """
        workflow_name = decision.selected_workflow
        result.add_audit_entry(f"Executing workflow: {workflow_name}")
        
        # Route through tool orchestrator (Stage 1 integration)
        try:
            # Execute the Safety Sigma pipeline with workflow-specific configuration
            orchestration_result = self.tool_orchestrator.execute_safety_sigma_pipeline(
                pdf_file=inputs.get('pdf_file', ''),
                instructions=self._enhance_instructions_for_workflow(inputs.get('instructions', ''), workflow_name),
                output_dir=inputs.get('output_dir', '.'),
                simulate=inputs.get('simulate', True)  # Default to simulation for Stage 2
            )
            
            # Store tool results for audit trail
            result.tool_results = list(orchestration_result.step_results.values())
            
            if orchestration_result.success:
                result.add_audit_entry(f"Workflow {workflow_name} completed successfully")
                result.add_audit_entry(f"Tools executed: {orchestration_result.steps_executed}/{len(self.tool_orchestrator.ss_pipeline)}")
                
                # Create enhanced result with agent metadata
                enhanced_result = self._create_enhanced_result(orchestration_result, decision)
                return enhanced_result
            else:
                error_msg = f"Workflow {workflow_name} failed: {orchestration_result.error}"
                result.add_audit_entry(error_msg)
                raise RuntimeError(error_msg)
                
        except Exception as e:
            result.add_audit_entry(f"Workflow execution error: {str(e)}")
            raise
    
    def _enhance_instructions_for_workflow(self, original_instructions: str, workflow_name: str) -> str:
        """
        Enhance instructions based on selected workflow
        
        Args:
            original_instructions: Original processing instructions
            workflow_name: Selected workflow name
            
        Returns:
            Enhanced instructions for the specific workflow
        """
        enhancements = {
            'fraud_analysis_workflow': """
FRAUD ANALYSIS FOCUS:
- Prioritize detection of deceptive practices and fraudulent indicators
- Extract financial transaction patterns and suspicious account behaviors
- Identify social engineering tactics and victim targeting methods
- Document fraud techniques and evasion strategies
            """.strip(),
            
            'threat_intelligence_workflow': """
THREAT INTELLIGENCE FOCUS:
- Prioritize technical indicators of compromise (IoCs)
- Extract malware signatures, network artifacts, and attack patterns
- Identify threat actor methodologies and campaign linkages
- Document defensive countermeasures and detection opportunities
            """.strip(),
            
            'policy_analysis_workflow': """
POLICY ANALYSIS FOCUS:
- Prioritize regulatory compliance requirements and guidelines
- Extract policy recommendations and implementation frameworks
- Identify governance structures and accountability mechanisms
- Document compliance gaps and remediation strategies
            """.strip(),
            
            'general_analysis_workflow': """
GENERAL ANALYSIS FOCUS:
- Comprehensive extraction of key findings and recommendations
- Balanced coverage of technical and operational aspects
- Clear identification of actionable intelligence
- Structured presentation of analysis results
            """.strip(),
        }
        
        workflow_enhancement = enhancements.get(workflow_name, enhancements['general_analysis_workflow'])
        
        return f"""{original_instructions}

## Workflow-Specific Enhancement ({workflow_name}):
{workflow_enhancement}

## Agent Processing Note:
This analysis is being processed by Safety Sigma 2.0 Simple Agent with deterministic workflow selection.
Selected workflow: {workflow_name}
"""
    
    def _create_enhanced_result(self, orchestration_result, decision: AgentDecision) -> Dict[str, Any]:
        """
        Create enhanced result with agent metadata
        
        Args:
            orchestration_result: Result from tool orchestration
            decision: Agent decision information
            
        Returns:
            Enhanced result with agent processing metadata
        """
        # Get the final analysis result
        analysis_result = orchestration_result.context.get('analysis_result', 'No analysis result available')
        
        # Create enhanced result with agent metadata
        enhanced_result = f"""{analysis_result}

---
## Agent Processing Metadata (Safety Sigma 2.0 - Stage 2)
- **Agent**: {decision.agent_name} v{decision.agent_version}
- **Decision ID**: {decision.decision_id}
- **Workflow Selected**: {decision.selected_workflow}
- **Confidence Score**: {decision.confidence_score:.2f}
- **Processing Time**: {orchestration_result.duration_ms:.1f}ms
- **Tools Executed**: {orchestration_result.steps_executed}
- **Agent Reasoning**: {len(decision.reasoning)} decision factors analyzed

### Decision Factors:
{chr(10).join(f'- {reason}' for reason in decision.reasoning)}

### Input Analysis Summary:
- Document Type: {decision.input_analysis.get('document_type', 'unknown')}
- Complexity Level: {decision.input_analysis.get('complexity_level', 'unknown')}
- Content Length: {decision.input_analysis.get('content_length', 0)} characters
"""
        
        return {
            'analysis_result': enhanced_result,
            'orchestration_result': orchestration_result,
            'agent_decision': decision,
            'workflow_name': decision.selected_workflow,
            'confidence_score': decision.confidence_score,
        }