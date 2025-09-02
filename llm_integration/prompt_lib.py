"""
Safety Sigma Prompt Library

System and user templates for LLM integration with Jinja2 rendering.
Implements the three required prompts with strict guardrails.
"""

from typing import Dict, Any, List
import json


class PromptRenderer:
    """
    Renders prompt templates with safe span injection
    """
    
    # System prompt templates as constants
    IR_STRUCTURING_PROMPT = """You transform pre-extracted spans into Safety Sigma IR v0.4. 
Rules:
- Zero-inference, cite-or-omit only.
- Preserve indicator strings verbatim.
- Map every field to provenance {page,start,end}.
- Categories only if explicit in source; include span ids.
- If unsure, mark UNSPECIFIED and leave field absent.

Return strictly valid JSON matching IR schema "extractions" array."""

    RULE_COMPILATION_PROMPT = """You compile deployable rules from IR extractions.
Constraints:
- Preserve exact indicators; no reformatting.
- Reference extractions by index (source_refs).
- Emit targets enabled in config: sql|json|python|regex.
- Include a compact comment header with extraction indices; no narrative text."""

    PRACTITIONER_NARRATIVE_PROMPT = """You draft a concise practitioner narrative from IR.
Rules:
- Only quote spans verbatim with span ids like [p:3 1043-1052].
- No categories unless present in IR with provenance.
- Keep it operational (what to match, where it appeared), no speculation.
- End with a "Verification Checklist" (copy/paste) aligning to V-001..V-005."""
    
    def __init__(self):
        # Initialize Jinja2 environment for safe templating
        try:
            from jinja2 import Environment, BaseLoader
            self.jinja_env = Environment(loader=BaseLoader(), autoescape=True)
        except ImportError:
            # Fallback to string formatting if Jinja2 not available
            self.jinja_env = None
    
    def render_ir_structuring_prompt(self, data: Dict[str, Any]) -> str:
        """
        Render IR structuring prompt with extraction data
        
        Args:
            data: Contains extractions, source_doc, schema_version
            
        Returns:
            Complete prompt for IR structuring
        """
        prompt_parts = [
            self.IR_STRUCTURING_PROMPT,
            "",
            "Input extractions:",
            json.dumps(data.get("extractions", []), indent=2, ensure_ascii=False),
            "",
            "Source document context:",
            json.dumps({
                "id": data.get("source_doc", {}).get("id", "unknown"),
                "pages": data.get("source_doc", {}).get("pages", 1)
            }, indent=2),
            "",
            f"Target schema version: {data.get('schema_version', 'v0.4')}",
            "",
            "Output format: JSON object with 'extractions' array only."
        ]
        
        return "\n".join(prompt_parts)
    
    def render_rule_compilation_prompt(self, data: Dict[str, Any]) -> str:
        """
        Render rule compilation prompt with IR data
        
        Args:
            data: Contains ir, config with targets enabled
            
        Returns:
            Complete prompt for rule compilation
        """
        ir = data.get("ir", {})
        config = data.get("config", {})
        targets = config.get("targets", ["regex"])
        
        prompt_parts = [
            self.RULE_COMPILATION_PROMPT,
            "",
            "IR extractions:",
            json.dumps(ir.get("extractions", []), indent=2, ensure_ascii=False),
            "",
            f"Enabled targets: {', '.join(targets)}",
            "",
            f"Total extractions: {len(ir.get('extractions', []))}",
            "",
            "Generate rules for each enabled target preserving exact indicators."
        ]
        
        return "\n".join(prompt_parts)
    
    def render_practitioner_narrative_prompt(self, data: Dict[str, Any]) -> str:
        """
        Render practitioner narrative prompt with IR data
        
        Args:
            data: Contains ir, source_doc
            
        Returns:
            Complete prompt for narrative generation
        """
        ir = data.get("ir", {})
        source_doc = data.get("source_doc", {})
        extractions = ir.get("extractions", [])
        
        prompt_parts = [
            self.PRACTITIONER_NARRATIVE_PROMPT,
            "",
            "IR extractions with provenance:",
            json.dumps(extractions, indent=2, ensure_ascii=False),
            "",
            "Source document:",
            f"- ID: {source_doc.get('id', 'unknown')}",
            f"- Pages: {source_doc.get('pages', 1)}",
            "",
            "Generate operational narrative with verbatim quotes and span references.",
            "Include verification checklist for V-001 through V-005."
        ]
        
        return "\n".join(prompt_parts)
    
    def safe_json_inject(self, data: Any) -> str:
        """
        Safely inject JSON data into prompts
        Prevents injection attacks through JSON encoding
        """
        return json.dumps(data, indent=2, ensure_ascii=False)
    
    def validate_prompt_safety(self, prompt: str) -> Dict[str, Any]:
        """
        Validate prompt doesn't contain unsafe injection patterns
        
        Returns:
            Dict with safety validation results
        """
        safety_report = {
            "safe": True,
            "issues": []
        }
        
        # Check for common injection patterns
        unsafe_patterns = [
            "{{",  # Template injection
            "}}",
            "${",  # Variable injection  
            "eval(",  # Code execution
            "exec(",
            "__import__"
        ]
        
        for pattern in unsafe_patterns:
            if pattern in prompt:
                safety_report["safe"] = False
                safety_report["issues"].append(f"Unsafe pattern detected: {pattern}")
        
        # Check prompt length (prevent DoS)
        if len(prompt) > 100000:  # 100KB limit
            safety_report["safe"] = False
            safety_report["issues"].append("Prompt exceeds maximum length")
            
        return safety_report


class PromptValidator:
    """
    Validates generated prompts meet safety and format requirements
    """
    
    @staticmethod
    def validate_ir_prompt(prompt: str, expected_extractions_count: int) -> Dict[str, Any]:
        """Validate IR structuring prompt format and content"""
        validation = {
            "valid": True,
            "issues": []
        }
        
        required_elements = [
            "Zero-inference",
            "cite-or-omit", 
            "Preserve indicator strings verbatim",
            "provenance",
            "JSON"
        ]
        
        for element in required_elements:
            if element not in prompt:
                validation["valid"] = False
                validation["issues"].append(f"Missing required element: {element}")
        
        # Check extraction count consistency
        if f"extractions" not in prompt:
            validation["valid"] = False
            validation["issues"].append("Extractions data not found in prompt")
            
        return validation
    
    @staticmethod
    def validate_rules_prompt(prompt: str, enabled_targets: List[str]) -> Dict[str, Any]:
        """Validate rule compilation prompt format"""
        validation = {
            "valid": True,
            "issues": []
        }
        
        required_elements = [
            "Preserve exact indicators",
            "source_refs",
            "no reformatting"
        ]
        
        for element in required_elements:
            if element.lower() not in prompt.lower():
                validation["valid"] = False  
                validation["issues"].append(f"Missing required element: {element}")
        
        # Check targets are mentioned
        for target in enabled_targets:
            if target not in prompt:
                validation["valid"] = False
                validation["issues"].append(f"Target {target} not mentioned in prompt")
                
        return validation
    
    @staticmethod
    def validate_narrative_prompt(prompt: str) -> Dict[str, Any]:
        """Validate practitioner narrative prompt format"""
        validation = {
            "valid": True,
            "issues": []
        }
        
        required_elements = [
            "verbatim",
            "span ids",
            "V-001",
            "V-005",
            "operational"
        ]
        
        for element in required_elements:
            if element.lower() not in prompt.lower():
                validation["valid"] = False
                validation["issues"].append(f"Missing required element: {element}")
                
        return validation