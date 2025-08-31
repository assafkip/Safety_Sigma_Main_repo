"""
Base Agent for Safety Sigma 2.0

Provides abstract base class for all agents with:
- Deterministic decision making
- Comprehensive audit logging  
- Input analysis capabilities
- Tool integration
"""

import abc
import json
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import os

from tools.base_tool import ToolResult


@dataclass
class AgentDecision:
    """
    Record of an agent decision with full audit trail
    """
    decision_id: str
    agent_name: str
    agent_version: str
    timestamp: float
    input_analysis: Dict[str, Any]
    decision_logic: str
    selected_workflow: str
    confidence_score: float
    reasoning: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_json(self) -> str:
        """Serialize decision to JSON for audit logging"""
        return json.dumps({
            "decision_id": self.decision_id,
            "agent_name": self.agent_name,
            "agent_version": self.agent_version,
            "timestamp": self.timestamp,
            "timestamp_iso": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(self.timestamp)),
            "input_analysis": self.input_analysis,
            "decision_logic": self.decision_logic,
            "selected_workflow": self.selected_workflow,
            "confidence_score": self.confidence_score,
            "reasoning": self.reasoning,
            "metadata": self.metadata,
        }, ensure_ascii=False, indent=2)


@dataclass
class AgentResult:
    """
    Agent execution result with decision audit trail
    """
    success: bool
    agent_name: str
    decision: AgentDecision
    workflow_result: Optional[Any] = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    tool_results: List[ToolResult] = field(default_factory=list)
    audit_trail: List[str] = field(default_factory=list)
    
    def add_audit_entry(self, entry: str) -> None:
        """Add entry to agent audit trail"""
        timestamp = time.strftime('%H:%M:%S.%f')[:-3]
        self.audit_trail.append(f"[{timestamp}] {entry}")


class BaseAgent(abc.ABC):
    """
    Abstract base class for all Safety Sigma 2.0 agents
    
    Provides:
    - Deterministic input analysis and workflow selection
    - Comprehensive decision audit logging
    - Tool integration and orchestration
    - Standardized agent interface
    """
    
    name: str = "base_agent"
    version: str = "0.1.0"
    
    def __init__(self, audit_dir: Optional[str] = None):
        """
        Initialize base agent
        
        Args:
            audit_dir: Directory for audit logs (default: from env)
        """
        self.audit_dir = Path(audit_dir or os.getenv('SS2_AUDIT_DIR', 'audit_logs'))
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up agent-specific logger
        import logging
        self.logger = logging.getLogger(f'safety_sigma.agents.{self.name}')
    
    def execute(self, **inputs) -> AgentResult:
        """
        Execute agent with comprehensive decision audit logging
        
        Args:
            **inputs: Agent-specific input parameters
            
        Returns:
            AgentResult with complete decision audit trail
        """
        start_time = time.time()
        decision_id = str(uuid.uuid4())
        
        result = AgentResult(
            success=False,
            agent_name=self.name,
            decision=None  # Will be set after analysis
        )
        
        result.add_audit_entry(f"Agent {self.name} v{self.version} execution started")
        result.add_audit_entry(f"Decision ID: {decision_id}")
        
        try:
            # Step 1: Analyze inputs
            result.add_audit_entry("Performing input analysis...")
            input_analysis = self._analyze_inputs(inputs)
            result.add_audit_entry(f"Input analysis complete: {len(input_analysis)} characteristics detected")
            
            # Step 2: Make workflow selection decision
            result.add_audit_entry("Making workflow selection decision...")
            decision = self._make_decision(decision_id, input_analysis, inputs)
            result.decision = decision
            result.add_audit_entry(f"Decision made: {decision.selected_workflow} (confidence: {decision.confidence_score})")
            
            # Step 3: Execute selected workflow
            result.add_audit_entry(f"Executing workflow: {decision.selected_workflow}")
            workflow_result = self._execute_workflow(decision, inputs, result)
            result.workflow_result = workflow_result
            
            result.success = True
            result.add_audit_entry("Agent execution completed successfully")
            
        except Exception as e:
            error_msg = f"{type(e).__name__}: {e}"
            result.error = error_msg
            result.add_audit_entry(f"Agent execution failed: {error_msg}")
            self.logger.error(f"Agent {self.name} failed: {error_msg}")
            
        finally:
            end_time = time.time()
            result.execution_time_ms = (end_time - start_time) * 1000.0
            
            # Write decision audit record
            if result.decision:
                self._write_decision_audit(result.decision)
                result.add_audit_entry(f"Decision audit record written: {decision_id}")
        
        return result
    
    @abc.abstractmethod
    def _analyze_inputs(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze inputs to determine document characteristics
        
        Args:
            inputs: Agent input parameters
            
        Returns:
            Dictionary with input analysis results
        """
        raise NotImplementedError(f"Agent {self.name} must implement _analyze_inputs")
    
    @abc.abstractmethod
    def _make_decision(self, decision_id: str, input_analysis: Dict[str, Any], inputs: Dict[str, Any]) -> AgentDecision:
        """
        Make deterministic workflow selection decision
        
        Args:
            decision_id: Unique decision identifier
            input_analysis: Results from input analysis
            inputs: Original input parameters
            
        Returns:
            AgentDecision with selected workflow and reasoning
        """
        raise NotImplementedError(f"Agent {self.name} must implement _make_decision")
    
    @abc.abstractmethod  
    def _execute_workflow(self, decision: AgentDecision, inputs: Dict[str, Any], result: AgentResult) -> Any:
        """
        Execute the selected workflow
        
        Args:
            decision: Agent decision with selected workflow
            inputs: Original input parameters
            result: Agent result for audit trail
            
        Returns:
            Workflow execution result
        """
        raise NotImplementedError(f"Agent {self.name} must implement _execute_workflow")
    
    def get_supported_workflows(self) -> List[str]:
        """
        Get list of workflows supported by this agent
        
        Returns:
            List of workflow names
        """
        return getattr(self, 'supported_workflows', ['default'])
    
    def _write_decision_audit(self, decision: AgentDecision) -> None:
        """
        Write decision audit record to log
        
        Args:
            decision: Agent decision to log
        """
        try:
            # Write individual decision record
            decision_file = self.audit_dir / f"agent_decision_{decision.decision_id}.json"
            decision_file.write_text(decision.to_json(), encoding="utf-8")
            
            # Also append to daily agent log
            daily_log = self.audit_dir / f"agent_decisions_{time.strftime('%Y-%m-%d')}.jsonl"
            with open(daily_log, 'a', encoding='utf-8') as f:
                f.write(decision.to_json().replace('\n', '') + '\n')
                
        except Exception as e:
            self.logger.error(f"Failed to write decision audit: {e}")
            # Don't fail agent execution due to audit logging issues
            pass


# Utility functions for input analysis

def analyze_document_type(content: str) -> Tuple[str, float]:
    """
    Analyze document content to determine type
    
    Args:
        content: Document text content
        
    Returns:
        Tuple of (document_type, confidence_score)
    """
    content_lower = content.lower()
    
    # Fraud indicators
    fraud_keywords = ['fraud', 'scam', 'phishing', 'deception', 'fake', 'suspicious']
    fraud_score = sum(1 for keyword in fraud_keywords if keyword in content_lower)
    
    # Threat intelligence indicators  
    threat_keywords = ['threat', 'attack', 'malware', 'vulnerability', 'exploit', 'breach']
    threat_score = sum(1 for keyword in threat_keywords if keyword in content_lower)
    
    # Policy/compliance indicators
    policy_keywords = ['policy', 'compliance', 'regulation', 'guideline', 'standard']
    policy_score = sum(1 for keyword in policy_keywords if keyword in content_lower)
    
    # Determine primary type based on keyword density
    total_words = len(content.split())
    word_threshold = max(2, total_words * 0.02)  # At least 2% or 2 words minimum
    
    if fraud_score >= word_threshold:
        return "fraud_analysis", min(0.95, fraud_score / word_threshold)
    elif threat_score >= word_threshold:
        return "threat_intelligence", min(0.95, threat_score / word_threshold) 
    elif policy_score >= word_threshold:
        return "policy_analysis", min(0.95, policy_score / word_threshold)
    else:
        return "general_analysis", 0.7  # Default with moderate confidence


def analyze_document_complexity(content: str) -> Tuple[str, float]:
    """
    Analyze document complexity level
    
    Args:
        content: Document text content
        
    Returns:
        Tuple of (complexity_level, confidence_score)
    """
    # Simple metrics for complexity assessment
    word_count = len(content.split())
    sentence_count = content.count('.') + content.count('!') + content.count('?')
    paragraph_count = content.count('\n\n') + 1
    
    # Technical terminology indicators
    technical_patterns = ['API', 'URL', 'IP address', 'hash', 'encryption', 'protocol']
    technical_score = sum(1 for pattern in technical_patterns if pattern.lower() in content.lower())
    
    # Complexity scoring
    if word_count < 500:
        complexity = "simple"
        confidence = 0.9
    elif word_count < 2000 and technical_score < 5:
        complexity = "moderate" 
        confidence = 0.8
    else:
        complexity = "complex"
        confidence = 0.85
        
    return complexity, confidence


def analyze_document_structure(content: str) -> Dict[str, Any]:
    """
    Analyze document structure characteristics
    
    Args:
        content: Document text content
        
    Returns:
        Dictionary with structure analysis
    """
    return {
        'has_headers': bool('##' in content or content.count('#') > 0),
        'has_lists': bool('-' in content or '*' in content or content.count('\n•') > 0),
        'has_structured_data': bool('{' in content and '}' in content),
        'line_count': content.count('\n') + 1,
        'paragraph_count': content.count('\n\n') + 1,
        'avg_line_length': len(content) / max(1, content.count('\n') + 1),
        'has_technical_formatting': bool('```' in content or '`' in content),
    }