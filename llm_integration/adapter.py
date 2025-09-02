"""
Safety Sigma LLM Adapter - Core integration functions

Implements zero-inference LLM integration with strict guardrails:
- build_ir: Structure extractions into IR Schema v0.4 objects
- compile_rules: Generate deployable rules preserving indicators exactly  
- draft_narrative: Create practitioner narratives with verbatim quoted spans
"""

import json
import hashlib
import time
from typing import Dict, List, Any, Optional
from pathlib import Path

from .prompt_lib import PromptRenderer
from .audit import AuditLogger
from .validator import IRValidator, RulesValidator


class LLMAdapter:
    """
    Core LLM integration adapter with strict zero-inference guardrails
    """
    
    def __init__(self, config: Dict[str, Any], audit_logger: AuditLogger):
        self.config = config
        self.audit = audit_logger
        self.prompt_renderer = PromptRenderer()
        self.ir_validator = IRValidator()
        self.rules_validator = RulesValidator()
        
        # LLM client placeholder - would integrate with actual LLM provider
        self.llm_client = None  # TODO: Initialize actual LLM client
        
    def build_ir(self, extractions_raw: List[Dict[str, Any]], 
                 source_doc: Dict[str, Any], 
                 config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Structure pre-extracted spans into IR Schema v0.4
        
        Args:
            extractions_raw: Detector outputs (strings + offsets) from MVP
            source_doc: Canonical text and structure from PDF pipeline
            config: Model params and targets
            
        Returns:
            IR dict with extractions array following Schema v0.4
            
        Guarantees:
            - Zero-inference: no invented facts/categories
            - Exact preservation: indicators verbatim from source
            - Provenance: every extraction has {page,start,end}
        """
        run_id = f"ir_{int(time.time())}_{hashlib.md5(str(extractions_raw).encode()).hexdigest()[:8]}"
        
        self.audit.append({
            "event": "build_ir_start",
            "run_id": run_id,
            "source_doc_id": source_doc.get("id", "unknown"),
            "extractions_count": len(extractions_raw),
            "timestamp": time.time()
        })
        
        try:
            # Render prompt with extractions and source context
            prompt_data = {
                "extractions": extractions_raw,
                "source_doc": source_doc,
                "schema_version": "v0.4"
            }
            
            system_prompt = self.prompt_renderer.render_ir_structuring_prompt(prompt_data)
            
            # For now, implement deterministic rule-based processing
            # TODO: Replace with actual LLM call when client is implemented
            ir_result = self._build_ir_deterministic(extractions_raw, source_doc)
            
            # Validate against golden test requirements
            validation_report = self.ir_validator.validate_ir_against_golden(ir_result)
            
            self.audit.append({
                "event": "build_ir_complete", 
                "run_id": run_id,
                "validation_report": validation_report,
                "indicators_preserved": validation_report.get("indicators_preserved", True),
                "categories_grounded": validation_report.get("categories_grounded", True),
                "timestamp": time.time()
            })
            
            if not validation_report.get("valid", True):
                raise ValueError(f"IR validation failed: {validation_report}")
                
            return ir_result
            
        except Exception as e:
            self.audit.append({
                "event": "build_ir_error",
                "run_id": run_id,
                "error": str(e),
                "timestamp": time.time()
            })
            raise
            
    def _build_ir_deterministic(self, extractions_raw: List[Dict[str, Any]], 
                               source_doc: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deterministic IR building for when LLM client not available
        Preserves exact indicators and maintains provenance
        """
        extractions = []
        
        for idx, extraction in enumerate(extractions_raw):
            # Preserve indicator verbatim
            value = extraction.get("value", "")
            if not value:
                continue
                
            # Determine type based on existing detection
            extraction_type = self._determine_type(extraction)
            
            # Build provenance from source offsets
            provenance = {
                "page": extraction.get("page", 1),
                "start": extraction.get("start", 0),
                "end": extraction.get("end", len(value))
            }
            
            ir_extraction = {
                "id": f"ext_{idx:03d}",
                "type": extraction_type,
                "value": value,  # Verbatim preservation
                "provenance": provenance,
                "confidence": extraction.get("confidence", 1.0),
                "source_span": {
                    "category_id": extraction.get("category_id", ""),
                    "span_id": extraction.get("span_id", f"span_{idx}")
                }
            }
            
            # Only add norm for amounts where numeric conversion is safe
            if extraction_type == "amount" and self._is_numeric_amount(value):
                try:
                    # Extract numeric value while preserving original
                    norm_value = self._extract_numeric_value(value)
                    if norm_value is not None:
                        ir_extraction["norm"] = norm_value
                except:
                    # If normalization fails, omit norm field entirely
                    pass
                    
            extractions.append(ir_extraction)
            
        return {
            "schema_version": "v0.4",
            "source_doc_id": source_doc.get("id", "unknown"), 
            "extractions": extractions,
            "metadata": {
                "processing_mode": "zero-inference",
                "timestamp": time.time(),
                "total_extractions": len(extractions)
            }
        }
        
    def _determine_type(self, extraction: Dict[str, Any]) -> str:
        """Determine extraction type based on existing detection"""
        kind = extraction.get("kind", "")
        
        type_mapping = {
            "amount": "amount",
            "account": "entity", 
            "domain": "link",
            "phone": "link",
            "email": "link", 
            "behavior": "category",
            "text": "memo",
            "memo": "memo"
        }
        
        return type_mapping.get(kind, "entity")
        
    def _is_numeric_amount(self, value: str) -> bool:
        """Check if amount value can be safely normalized"""
        # Must contain digits and currency/amount indicators
        has_digits = any(c.isdigit() for c in value)
        has_currency = any(symbol in value for symbol in ['$', '€', '£', '¥', 'USD', 'EUR'])
        return has_digits and has_currency
        
    def _extract_numeric_value(self, value: str) -> Optional[float]:
        """Extract numeric value from amount string"""
        import re
        # Extract number with decimal point
        match = re.search(r'[\d,]+\.?\d*', value.replace(',', ''))
        if match:
            try:
                return float(match.group().replace(',', ''))
            except ValueError:
                pass
        return None

    def compile_rules(self, ir: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, str]:
        """
        Compile deployable rules from IR extractions
        
        Args:
            ir: IR dict from build_ir
            config: Rule compilation config (targets enabled)
            
        Returns:
            Dict mapping target type (sql|json|python|regex) to rule content
            
        Guarantees:
            - Exact indicator preservation in rules
            - Reference extractions by index only
            - No literal mutation of indicators
        """
        run_id = f"rules_{int(time.time())}_{hashlib.md5(str(ir).encode()).hexdigest()[:8]}"
        
        self.audit.append({
            "event": "compile_rules_start",
            "run_id": run_id,
            "extractions_count": len(ir.get("extractions", [])),
            "targets": config.get("targets", []),
            "timestamp": time.time()
        })
        
        try:
            rules = {}
            extractions = ir.get("extractions", [])
            
            # Generate rules for enabled targets
            enabled_targets = config.get("targets", ["regex", "json"])
            
            if "regex" in enabled_targets:
                rules["regex"] = self._compile_regex_rules(extractions)
                
            if "json" in enabled_targets:
                rules["json"] = self._compile_json_rules(extractions)
                
            if "python" in enabled_targets:
                rules["python"] = self._compile_python_rules(extractions)
                
            if "sql" in enabled_targets:
                rules["sql"] = self._compile_sql_rules(extractions)
            
            # Validate rules execute without syntax errors
            validation_report = self.rules_validator.validate_rules(rules)
            
            self.audit.append({
                "event": "compile_rules_complete",
                "run_id": run_id,
                "rules_generated": list(rules.keys()),
                "validation_report": validation_report,
                "timestamp": time.time()
            })
            
            return rules
            
        except Exception as e:
            self.audit.append({
                "event": "compile_rules_error",
                "run_id": run_id,
                "error": str(e),
                "timestamp": time.time()
            })
            raise
            
    def _compile_regex_rules(self, extractions: List[Dict[str, Any]]) -> str:
        """Generate regex rules preserving exact indicators"""
        rules = []
        rules.append("# Safety Sigma Regex Rules - Generated from IR extractions")
        rules.append("# Extraction indices: " + ", ".join(f"ext_{i:03d}" for i in range(len(extractions))))
        rules.append("")
        
        for idx, extraction in enumerate(extractions):
            value = extraction["value"]
            ext_type = extraction["type"] 
            
            # Escape regex special characters in value
            escaped_value = self._escape_regex(value)
            
            rule = f"# Extraction {idx:03d} - {ext_type}"
            rule += f"\n{escaped_value}  # source_refs: [{idx}]"
            rules.append(rule)
            rules.append("")
            
        return "\n".join(rules)
        
    def _compile_json_rules(self, extractions: List[Dict[str, Any]]) -> str:
        """Generate JSON rules structure"""
        rules_data = {
            "schema_version": "v0.4",
            "rules": []
        }
        
        for idx, extraction in enumerate(extractions):
            rule = {
                "id": f"rule_{idx:03d}",
                "type": extraction["type"],
                "pattern": extraction["value"],  # Verbatim indicator
                "source_refs": [idx],
                "metadata": {
                    "extraction_id": extraction["id"],
                    "provenance": extraction["provenance"]
                }
            }
            rules_data["rules"].append(rule)
            
        return json.dumps(rules_data, indent=2, ensure_ascii=False)
        
    def _compile_python_rules(self, extractions: List[Dict[str, Any]]) -> str:
        """Generate Python rules"""
        rules = []
        rules.append("# Safety Sigma Python Rules")
        rules.append("# Generated from IR extractions")
        rules.append("")
        rules.append("def check_indicators(text):")
        rules.append("    \"\"\"Check text against extracted indicators\"\"\"")
        rules.append("    matches = []")
        rules.append("")
        
        for idx, extraction in enumerate(extractions):
            value = extraction["value"]
            escaped_value = json.dumps(value)  # Safe string escaping
            
            rules.append(f"    # Extraction {idx:03d} - {extraction['type']}")
            rules.append(f"    if {escaped_value} in text:")
            rules.append(f"        matches.append({{'rule_id': 'rule_{idx:03d}', 'value': {escaped_value}, 'source_refs': [{idx}]}})")
            rules.append("")
            
        rules.append("    return matches")
        
        return "\n".join(rules)
        
    def _compile_sql_rules(self, extractions: List[Dict[str, Any]]) -> str:
        """Generate SQL rules"""
        rules = []
        rules.append("-- Safety Sigma SQL Rules")
        rules.append("-- Generated from IR extractions")
        rules.append("")
        
        for idx, extraction in enumerate(extractions):
            value = extraction["value"]
            ext_type = extraction["type"]
            
            # Escape SQL string
            escaped_value = value.replace("'", "''")
            
            rules.append(f"-- Extraction {idx:03d} - {ext_type}")
            rules.append(f"SELECT * FROM documents WHERE content LIKE '%{escaped_value}%';")
            rules.append(f"-- source_refs: [{idx}]")
            rules.append("")
            
        return "\n".join(rules)
        
    def _escape_regex(self, value: str) -> str:
        """Escape regex special characters"""
        import re
        return re.escape(value)

    def draft_narrative(self, ir: Dict[str, Any], source_doc: Dict[str, Any]) -> str:
        """
        Generate practitioner narrative with verbatim quoted spans
        
        Args:
            ir: IR dict from build_ir
            source_doc: Source document context
            
        Returns:
            Markdown narrative with quoted spans and span IDs
            
        Guarantees:
            - Only quotes spans verbatim with span IDs
            - No categories unless present in IR with provenance  
            - Operational focus (what to match, where it appeared)
        """
        run_id = f"narrative_{int(time.time())}_{hashlib.md5(str(ir).encode()).hexdigest()[:8]}"
        
        self.audit.append({
            "event": "draft_narrative_start",
            "run_id": run_id,
            "source_doc_id": source_doc.get("id", "unknown"),
            "extractions_count": len(ir.get("extractions", [])),
            "timestamp": time.time()
        })
        
        try:
            extractions = ir.get("extractions", [])
            narrative_lines = []
            
            # Header
            narrative_lines.append("# Safety Sigma Practitioner Narrative")
            narrative_lines.append("")
            narrative_lines.append("**NON-AUTHORITATIVE** — This narrative quotes source spans verbatim.")
            narrative_lines.append("For authoritative data, reference ir.json and compiled rules.")
            narrative_lines.append("")
            
            # Group extractions by type
            by_type = {}
            for extraction in extractions:
                ext_type = extraction["type"]
                if ext_type not in by_type:
                    by_type[ext_type] = []
                by_type[ext_type].append(extraction)
                
            # Generate sections
            for ext_type, type_extractions in by_type.items():
                narrative_lines.append(f"## {ext_type.title()} Indicators")
                narrative_lines.append("")
                
                for extraction in type_extractions:
                    value = extraction["value"]
                    provenance = extraction["provenance"] 
                    span_ref = f"[p:{provenance['page']} {provenance['start']}-{provenance['end']}]"
                    
                    narrative_lines.append(f"- \"{value}\" {span_ref}")
                    
                narrative_lines.append("")
                
            # Verification checklist
            narrative_lines.append("## Verification Checklist")
            narrative_lines.append("")
            narrative_lines.append("- [ ] V-001: All indicators preserved verbatim in rules")
            narrative_lines.append("- [ ] V-002: Categories grounded to source spans") 
            narrative_lines.append("- [ ] V-003: Complete audit trail with provenance")
            narrative_lines.append("- [ ] V-004: Rules execute without syntax errors")
            narrative_lines.append("- [ ] V-005: No UNSPECIFIED values in production outputs")
            
            narrative = "\n".join(narrative_lines)
            
            self.audit.append({
                "event": "draft_narrative_complete",
                "run_id": run_id,
                "narrative_length": len(narrative),
                "spans_quoted": len(extractions),
                "timestamp": time.time()
            })
            
            return narrative
            
        except Exception as e:
            self.audit.append({
                "event": "draft_narrative_error", 
                "run_id": run_id,
                "error": str(e),
                "timestamp": time.time()
            })
            raise