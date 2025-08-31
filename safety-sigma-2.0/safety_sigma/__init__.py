"""
Safety Sigma 2.0 - Advanced Threat Intelligence Detection System

A modular, agent-based evolution of the original Safety Sigma system with:
- Tool abstraction layer for extensibility
- Agent-based processing with deterministic behavior
- Comprehensive audit trails and compliance guarantees
- Zero-inference mode for regulatory compliance
- Backward compatibility with Safety Sigma 1.0
"""

__version__ = "2.0.0"
__author__ = "Safety Sigma Team"

# Feature toggles (read from environment)
import os
from typing import Dict

FEATURE_TOGGLES: Dict[str, bool] = {
    'SS2_ENABLE_TOOLS': os.getenv('SS2_ENABLE_TOOLS', 'false').lower() == 'true',
    'SS2_USE_AGENT': os.getenv('SS2_USE_AGENT', 'false').lower() == 'true',
    'SS2_ENHANCE_DOCS': os.getenv('SS2_ENHANCE_DOCS', 'false').lower() == 'true', 
    'SS2_SOURCE_DRIVEN': os.getenv('SS2_SOURCE_DRIVEN', 'false').lower() == 'true',
    'SS2_DYNAMIC_WORKFLOWS': os.getenv('SS2_DYNAMIC_WORKFLOWS', 'false').lower() == 'true',
    'SS2_MULTI_AGENT': os.getenv('SS2_MULTI_AGENT', 'false').lower() == 'true',
    'SS2_SELF_IMPROVE': os.getenv('SS2_SELF_IMPROVE', 'false').lower() == 'true',
}

def get_active_stage() -> str:
    """Determine the active stage based on enabled features"""
    if FEATURE_TOGGLES['SS2_SELF_IMPROVE']:
        return "Stage 6: Self-Improvement Loop"
    elif FEATURE_TOGGLES['SS2_MULTI_AGENT']:
        return "Stage 5: Multi-Agent System"
    elif FEATURE_TOGGLES['SS2_DYNAMIC_WORKFLOWS']:
        return "Stage 4: Dynamic Workflows"
    elif FEATURE_TOGGLES['SS2_ENHANCE_DOCS']:
        return "Stage 3: Advanced Decision Trees"
    elif FEATURE_TOGGLES['SS2_USE_AGENT']:
        return "Stage 2: Simple Agent Logic"
    elif FEATURE_TOGGLES['SS2_ENABLE_TOOLS']:
        return "Stage 1: Tool Abstraction"
    else:
        return "Stage 0: Bootstrap (v1.0 Parity Mode)"

def get_version_info() -> Dict[str, any]:
    """Get comprehensive version and configuration information"""
    return {
        'version': __version__,
        'active_stage': get_active_stage(),
        'feature_toggles': FEATURE_TOGGLES,
        'compliance_mode': {
            'zero_inference': os.getenv('SS2_ZERO_INFERENCE', 'true').lower() == 'true',
            'source_traceability': os.getenv('SS2_REQUIRE_SOURCE_TRACEABILITY', 'true').lower() == 'true',
            'fail_on_validation': os.getenv('SS2_FAIL_ON_VALIDATION_ERROR', 'true').lower() == 'true',
        }
    }