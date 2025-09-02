"""
Safety Sigma LLM Validator

Validates IR and rules against golden test requirements and validation gates.
Implements strict checks for V-001 through V-005.
"""

import json
import re
import subprocess
import tempfile
from typing import Dict, List, Any, Set
from pathlib import Path


class IRValidator:
    """
    Validates IR against golden test requirements
    """
    
    def validate_ir_against_golden(self, ir: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate IR against golden test requirements (G-001..G-003, G-010)
        
        Args:
            ir: IR dictionary to validate
            
        Returns:
            Validation report with gate status
        """
        report = {
            "valid": True,
            "gates": {},
            "issues": [],
            "indicators_preserved": True,
            "categories_grounded": True
        }
        
        extractions = ir.get("extractions", [])
        
        # V-001: Indicator preservation (G-001..G-003)
        preservation_result = self._validate_indicator_preservation(extractions)
        report["gates"]["V-001"] = preservation_result
        if not preservation_result["passed"]:
            report["valid"] = False
            report["indicators_preserved"] = False
            report["issues"].extend(preservation_result["issues"])
        
        # V-002: Category grounding (G-010) 
        grounding_result = self._validate_category_grounding(extractions)
        report["gates"]["V-002"] = grounding_result
        if not grounding_result["passed"]:
            report["valid"] = False
            report["categories_grounded"] = False
            report["issues"].extend(grounding_result["issues"])
            
        # V-003: Audit completeness
        completeness_result = self._validate_audit_completeness(extractions)
        report["gates"]["V-003"] = completeness_result
        if not completeness_result["passed"]:
            report["valid"] = False
            report["issues"].extend(completeness_result["issues"])
            
        return report
    
    def _validate_indicator_preservation(self, extractions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate exact indicator preservation (V-001)
        Tests for verbatim preservation of critical indicators
        """
        result = {
            "passed": True,
            "issues": [],
            "test_cases": []
        }
        
        # Test cases for exact preservation 
        critical_indicators = [
            "$1,998.88",  # Amount with comma and decimal
            "VOID 2000",  # Alphanumeric code
            "wa.me/123456789"  # WhatsApp link format
        ]
        
        found_indicators = set()
        for extraction in extractions:
            value = extraction.get("value", "")
            found_indicators.add(value)
            
            # Check value is not empty or whitespace only
            if not value or not value.strip():
                result["passed"] = False
                result["issues"].append(f"Empty or whitespace-only value in extraction {extraction.get('id', 'unknown')}")
            
            # Check for verbatim preservation - no normalization artifacts
            if self._has_normalization_artifacts(value):
                result["passed"] = False  
                result["issues"].append(f"Normalization artifacts detected in value: '{value}'")
        
        # Test specific critical indicators if present
        for indicator in critical_indicators:
            if any(indicator in str(ext.get("value", "")) for ext in extractions):
                test_case = {
                    "indicator": indicator,
                    "found": indicator in found_indicators,
                    "verbatim": True
                }
                
                if not test_case["found"]:
                    result["passed"] = False
                    result["issues"].append(f"Critical indicator not preserved verbatim: {indicator}")
                
                result["test_cases"].append(test_case)
        
        return result
    
    def _has_normalization_artifacts(self, value: str) -> bool:
        """Check if value shows signs of unwanted normalization"""
        # Common normalization artifacts to detect
        artifacts = [
            r'^\s*normalized:\s*',  # Explicit normalization labels
            r'^\s*cleaned:\s*',
            r'^\s*processed:\s*',
            r'[Nn][Oo][Rr][Mm].*:',  # Normalization prefixes
        ]
        
        for pattern in artifacts:
            if re.search(pattern, value):
                return True
                
        return False
    
    def _validate_category_grounding(self, extractions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate category grounding (V-002)
        Ensures categories only appear if explicitly present in source
        """
        result = {
            "passed": True,
            "issues": [],
            "categories_found": [],
            "ungrounded_categories": []
        }
        
        for extraction in extractions:
            if extraction.get("type") == "category":
                category_value = extraction.get("value", "")
                result["categories_found"].append(category_value)
                
                # Check provenance exists
                provenance = extraction.get("provenance", {})
                if not provenance or not all(k in provenance for k in ["page", "start", "end"]):
                    result["passed"] = False
                    result["issues"].append(f"Category '{category_value}' lacks complete provenance")
                    result["ungrounded_categories"].append(category_value)
                
                # Check source span exists  
                source_span = extraction.get("source_span", {})
                if not source_span or not source_span.get("span_id"):
                    result["passed"] = False
                    result["issues"].append(f"Category '{category_value}' lacks source span ID")
                    result["ungrounded_categories"].append(category_value)
        
        return result
    
    def _validate_audit_completeness(self, extractions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate audit completeness (V-003)
        Every extraction must have provenance + spans + source tracking
        """
        result = {
            "passed": True,
            "issues": [],
            "missing_provenance": [],
            "missing_spans": []
        }
        
        for extraction in extractions:
            ext_id = extraction.get("id", "unknown")
            
            # Check provenance completeness
            provenance = extraction.get("provenance", {})
            required_prov_fields = ["page", "start", "end"]
            missing_prov = [f for f in required_prov_fields if f not in provenance]
            
            if missing_prov:
                result["passed"] = False
                result["issues"].append(f"Extraction {ext_id} missing provenance fields: {missing_prov}")
                result["missing_provenance"].append(ext_id)
            
            # Check source span exists
            source_span = extraction.get("source_span", {})
            if not source_span:
                result["passed"] = False
                result["issues"].append(f"Extraction {ext_id} missing source_span")
                result["missing_spans"].append(ext_id)
            else:
                # Validate span has required fields
                if not source_span.get("span_id"):
                    result["passed"] = False
                    result["issues"].append(f"Extraction {ext_id} source_span missing span_id")
                    result["missing_spans"].append(ext_id)
        
        return result


class RulesValidator:
    """
    Validates generated rules for syntax and executability
    """
    
    def validate_rules(self, rules: Dict[str, str]) -> Dict[str, Any]:
        """
        Validate rules execute without syntax errors (V-004)
        
        Args:
            rules: Dict mapping target type to rule content
            
        Returns:
            Validation report with syntax and execution status
        """
        report = {
            "valid": True,
            "gates": {"V-004": {"passed": True, "issues": []}},
            "rule_validations": {}
        }
        
        for target, rule_content in rules.items():
            validation = self._validate_rule_target(target, rule_content)
            report["rule_validations"][target] = validation
            
            if not validation["passed"]:
                report["valid"] = False
                report["gates"]["V-004"]["passed"] = False
                report["gates"]["V-004"]["issues"].extend(validation["issues"])
        
        return report
    
    def _validate_rule_target(self, target: str, content: str) -> Dict[str, Any]:
        """Validate specific rule target type"""
        result = {
            "passed": True,
            "issues": [],
            "syntax_valid": False,
            "executable": False
        }
        
        if target == "regex":
            return self._validate_regex_rules(content)
        elif target == "json":
            return self._validate_json_rules(content)
        elif target == "python":
            return self._validate_python_rules(content)
        elif target == "sql":
            return self._validate_sql_rules(content)
        else:
            result["passed"] = False
            result["issues"].append(f"Unknown rule target: {target}")
            
        return result
    
    def _validate_regex_rules(self, content: str) -> Dict[str, Any]:
        """Validate regex rules for syntax errors"""
        result = {
            "passed": True,
            "issues": [],
            "syntax_valid": True,
            "executable": True
        }
        
        # Extract regex patterns from content
        patterns = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                # Extract pattern (everything before comment)
                pattern = line.split('#')[0].strip()
                if pattern:
                    patterns.append(pattern)
        
        # Test each pattern
        for pattern in patterns:
            try:
                re.compile(pattern)
            except re.error as e:
                result["passed"] = False
                result["syntax_valid"] = False
                result["issues"].append(f"Invalid regex pattern '{pattern}': {str(e)}")
        
        return result
    
    def _validate_json_rules(self, content: str) -> Dict[str, Any]:
        """Validate JSON rules for syntax"""
        result = {
            "passed": True,
            "issues": [],
            "syntax_valid": True,
            "executable": True
        }
        
        try:
            data = json.loads(content)
            
            # Validate structure
            if not isinstance(data, dict):
                result["passed"] = False
                result["issues"].append("JSON rules must be an object")
            
            if "rules" not in data:
                result["passed"] = False
                result["issues"].append("JSON rules missing 'rules' array")
            
        except json.JSONDecodeError as e:
            result["passed"] = False
            result["syntax_valid"] = False
            result["issues"].append(f"Invalid JSON syntax: {str(e)}")
        
        return result
    
    def _validate_python_rules(self, content: str) -> Dict[str, Any]:
        """Validate Python rules for syntax"""
        result = {
            "passed": True,
            "issues": [],
            "syntax_valid": True,
            "executable": True
        }
        
        try:
            compile(content, '<rules>', 'exec')
        except SyntaxError as e:
            result["passed"] = False
            result["syntax_valid"] = False
            result["issues"].append(f"Python syntax error: {str(e)}")
        
        return result
    
    def _validate_sql_rules(self, content: str) -> Dict[str, Any]:
        """Validate SQL rules for basic syntax"""
        result = {
            "passed": True,
            "issues": [],
            "syntax_valid": True,
            "executable": False  # Can't easily test SQL without DB
        }
        
        # Basic SQL syntax validation
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if line and not line.startswith('--'):
                # Check for basic SQL structure
                if not any(keyword in line.upper() for keyword in ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE']):
                    continue  # Skip non-SQL lines
                
                # Check for unmatched quotes
                if line.count("'") % 2 != 0:
                    result["passed"] = False
                    result["syntax_valid"] = False
                    result["issues"].append(f"Unmatched quotes in line {line_num}: {line}")
        
        return result
        

class ValidationGateChecker:
    """
    Comprehensive checker for all validation gates V-001 through V-005
    """
    
    def __init__(self):
        self.ir_validator = IRValidator()
        self.rules_validator = RulesValidator()
    
    def check_all_gates(self, ir: Dict[str, Any], rules: Dict[str, str], 
                       config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check all validation gates V-001 through V-005
        
        Returns:
            Comprehensive validation report
        """
        report = {
            "all_gates_passed": True,
            "gates": {},
            "summary": {},
            "issues": []
        }
        
        # V-001, V-002, V-003: IR validation
        ir_report = self.ir_validator.validate_ir_against_golden(ir)
        report["gates"].update(ir_report["gates"])
        if not ir_report["valid"]:
            report["all_gates_passed"] = False
            report["issues"].extend(ir_report["issues"])
        
        # V-004: Rules validation  
        rules_report = self.rules_validator.validate_rules(rules)
        report["gates"]["V-004"] = rules_report["gates"]["V-004"]
        if not rules_report["valid"]:
            report["all_gates_passed"] = False
        
        # V-005: Execution guarantees (check for UNSPECIFIED)
        v005_result = self._check_execution_guarantees(ir, rules, config)
        report["gates"]["V-005"] = v005_result
        if not v005_result["passed"]:
            report["all_gates_passed"] = False
        
        # Generate summary
        report["summary"] = {
            "total_gates": 5,
            "passed_gates": sum(1 for gate in report["gates"].values() if gate.get("passed", False)),
            "gate_status": {f"V-{i:03d}": report["gates"].get(f"V-{i:03d}", {}).get("passed", False) 
                           for i in range(1, 6)}
        }
        
        return report
    
    def _check_execution_guarantees(self, ir: Dict[str, Any], rules: Dict[str, str], 
                                   config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check V-005: No UNSPECIFIED values in production outputs
        """
        result = {
            "passed": True,
            "issues": [],
            "unspecified_found": []
        }
        
        # Check IR for UNSPECIFIED
        ir_str = json.dumps(ir)
        if "UNSPECIFIED" in ir_str:
            result["passed"] = False
            result["issues"].append("UNSPECIFIED values found in IR")
            result["unspecified_found"].append("ir.json")
        
        # Check rules for UNSPECIFIED
        for target, content in rules.items():
            if "UNSPECIFIED" in content:
                result["passed"] = False
                result["issues"].append(f"UNSPECIFIED values found in {target} rules")
                result["unspecified_found"].append(f"rules/{target}")
        
        # Check config for required fields
        required_config = ["model_name", "targets"]
        for field in required_config:
            if field not in config:
                result["passed"] = False
                result["issues"].append(f"Required config field missing: {field}")
        
        return result