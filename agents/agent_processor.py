"""
Agent Processor for Safety Sigma 2.0

Provides agent-based processing that routes through the tool abstraction layer.
Integrates with the existing processor architecture while adding agent decision making.
"""

import os
from typing import Dict, Any, Optional
from pathlib import Path

from .simple_agent import SimpleAgent
from .enhanced_agent import EnhancedAgent
from orchestration.tool_orchestrator import ToolOrchestrator


class AgentProcessor:
    """
    Agent-based processor that wraps Safety Sigma functionality with agent decision making
    
    Provides:
    - Agent-based workflow selection
    - Integration with tool abstraction layer
    - Comprehensive decision audit logging
    - Backward compatibility with existing interfaces
    """
    
    def __init__(self, agent_type: str = "simple", audit_dir: Optional[str] = None):
        """
        Initialize agent processor
        
        Args:
            agent_type: Type of agent to use ("simple" for Stage 2, "enhanced" for Stage 3)
            audit_dir: Directory for audit logs
        """
        self.agent_type = agent_type
        self.audit_dir = audit_dir or os.getenv('SS2_AUDIT_DIR', 'audit_logs')
        
        # Initialize agent
        if agent_type == "simple":
            self.agent = SimpleAgent(audit_dir=self.audit_dir)
            self._stage = "Stage 2: Simple Agent Logic (simple)"
        elif agent_type == "enhanced":
            self.agent = EnhancedAgent(audit_dir=self.audit_dir)
            self._stage = "Stage 3: Advanced Decision Trees (enhanced)"
        else:
            raise ValueError(f"Unsupported agent type: {agent_type}. Supported: 'simple', 'enhanced'")
        
        # Also maintain tool orchestrator for direct access if needed
        self.tool_orchestrator = ToolOrchestrator(audit_dir=self.audit_dir)
    
    def extract_pdf_text(self, pdf_path: str) -> str:
        """
        Extract text from PDF file using agent decision making
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extracted text content
        """
        # For Stage 2, agent analyzes input and routes through tools
        # This maintains interface compatibility while adding agent logic
        
        agent_result = self.agent.execute(
            pdf_file=pdf_path,
            instructions="Extract all text content from the document",
            operation_type="pdf_extraction",
            simulate=True  # Default to simulation for Stage 2
        )
        
        if not agent_result.success:
            raise RuntimeError(f"Agent PDF extraction failed: {agent_result.error}")
        
        # Extract the PDF text from the workflow result
        workflow_result = agent_result.workflow_result
        if isinstance(workflow_result, dict):
            orchestration_result = workflow_result.get('orchestration_result')
            if orchestration_result and 'extracted_text' in orchestration_result.context:
                return orchestration_result.context['extracted_text']
        
        # Fallback: use tool orchestrator directly
        from tools import PDFTool
        pdf_tool = PDFTool()
        tool_result = pdf_tool.execute(pdf_path=pdf_path)
        
        if not tool_result.success:
            raise RuntimeError(f"PDF extraction failed: {tool_result.error}")
            
        return tool_result.data
    
    def read_instruction_file(self, md_path: str) -> str:
        """
        Read instruction file (agent-enhanced but maintains compatibility)
        
        Args:
            md_path: Path to markdown instruction file
            
        Returns:
            Instruction content
        """
        # For Stage 2, reading instructions is straightforward
        # Agent logic is applied during processing, not instruction reading
        try:
            with open(md_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Basic validation
            if len(content.strip()) < 10:
                raise ValueError(f"Instruction file too short: {len(content)} characters")
            
            return content
            
        except Exception as e:
            raise Exception(f"Error reading instruction file: {str(e)}")
    
    def process_report(self, instructions: str, report_content: str) -> str:
        """
        Process report using agent-based workflow selection
        
        Args:
            instructions: Processing instructions
            report_content: Source content to analyze
            
        Returns:
            Analysis result with agent processing metadata
        """
        # This is where the agent logic really kicks in
        agent_result = self.agent.execute(
            instructions=instructions,
            document_content=report_content,
            operation_type="report_processing",
            simulate=True  # Default to simulation for Stage 2
        )
        
        if not agent_result.success:
            raise RuntimeError(f"Agent report processing failed: {agent_result.error}")
        
        # Extract the analysis result
        workflow_result = agent_result.workflow_result
        if isinstance(workflow_result, dict):
            return workflow_result.get('analysis_result', 'Agent processing completed but no result available')
        
        return str(workflow_result)
    
    def save_results(self, results: str, output_path: str) -> None:
        """
        Save results with agent metadata
        
        Args:
            results: Analysis results to save
            output_path: Output directory path
        """
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"safety_sigma_results_{timestamp}.md"
        full_path = Path(output_path) / filename
        
        # Create enhanced output with Stage 2 metadata
        enhanced_results = f"""{results}

---
## Agent Processing Summary (Safety Sigma 2.0 - Stage 2)
- **Processing Stage**: {self._stage}
- **Agent Type**: {self.agent_type}
- **Agent Decision Making**: ENABLED
- **Tool Abstraction**: ENABLED
- **Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Audit Logging**: COMPREHENSIVE (Agent + Tool + Orchestration)
- **Zero-Inference Mode**: {os.getenv('SS2_ZERO_INFERENCE', 'true')}

## Agent Capabilities:
- Deterministic workflow selection based on document analysis
- Hardcoded decision trees for reliable processing
- Integration with tool abstraction layer
- Comprehensive audit trail of all decisions
"""
        
        with open(full_path, 'w', encoding='utf-8') as file:
            file.write(enhanced_results)
        
        print(f"Results saved to: {full_path}")
    
    def get_stage_info(self) -> Dict[str, Any]:
        """
        Get information about current processing stage
        
        Returns:
            Dictionary with stage and agent information
        """
        return {
            "stage": self._stage,
            "agent_type": self.agent_type,
            "backend_type": type(self.agent).__name__,
            "supported_workflows": self.agent.get_supported_workflows(),
            "tools_enabled": True,
            "agent_enabled": True,
        }
    
    def get_agent_info(self) -> Dict[str, Any]:
        """
        Get detailed agent information
        
        Returns:
            Dictionary with agent capabilities and configuration
        """
        return {
            "agent_name": self.agent.name,
            "agent_version": self.agent.version,
            "supported_workflows": self.agent.get_supported_workflows(),
            "decision_logic": "Hardcoded decision trees with deterministic behavior",
            "audit_capabilities": [
                "Input analysis logging",
                "Decision reasoning capture",
                "Workflow selection audit",
                "Tool execution tracking",
                "Performance metrics"
            ]
        }