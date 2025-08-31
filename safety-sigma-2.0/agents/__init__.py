"""
Safety Sigma 2.0 Agents Package

Provides agent-based processing with deterministic behavior:
- Base agent interface with decision audit logging
- Simple agent with hardcoded workflow selection (Stage 2)
- Enhanced agent with rule engine integration (Stage 3)
- Input analysis and document type detection
- Integration with tool abstraction layer
"""

from .base_agent import BaseAgent, AgentDecision, AgentResult
from .simple_agent import SimpleAgent
from .enhanced_agent import EnhancedAgent

__all__ = [
    'BaseAgent',
    'AgentDecision', 
    'AgentResult',
    'SimpleAgent',
    'EnhancedAgent',
]