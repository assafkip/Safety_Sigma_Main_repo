"""
Safety Sigma LLM Integration Tests

Comprehensive tests for LLM integration including:
- Unit tests for each function
- Golden tests (positive + negative/fail-first) 
- Snapshot tests verifying verbatim indicators
- Validation gate tests V-001 through V-005
"""

import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import Mock, patch

# Import modules under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from llm_integration.adapter import LLMAdapter
from llm_integration.validator import IRValidator, RulesValidator, ValidationGateChecker
from llm_integration.audit import AuditLogger, AuditContext
from llm_integration.prompt_lib import PromptRenderer, PromptValidator


class TestLLMAdapter:
    """Test suite for LLM adapter core functions"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.audit_log = self.temp_dir / "audit.jsonl" 
        self.audit_logger = AuditLogger(self.audit_log)
        self.config = {
            "model_name": "test-model",
            "targets": ["regex", "json"],
            "temperature": 0
        }
        self.adapter = LLMAdapter(self.config, self.audit_logger)
        
    def teardown_method(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_build_ir_preserves_exact_indicators(self):
        """Test V-001: Exact indicator preservation in IR"""
        # Critical indicators that must be preserved verbatim
        extractions_raw = [
            {
                "value": "$1,998.88",
                "kind": "amount",
                "page": 1,
                "start": 100,
                "end": 109,
                "category_id": "financial",
                "span_id": "span_001"
            },
            {
                "value": "VOID 2000", 
                "kind": "text",
                "page": 1,
                "start": 200,
                "end": 209,
                "category_id": "codes",
                "span_id": "span_002"
            },
            {
                "value": "wa.me/123456789",
                "kind": "domain",
                "page": 2,
                "start": 50,
                "end": 66,
                "category_id": "contact",
                "span_id": "span_003"
            }
        ]
        
        source_doc = {
            "id": "test_doc_001",
            "pages": 2
        }
        
        # Build IR
        ir = self.adapter.build_ir(extractions_raw, source_doc, self.config)
        
        # Verify exact preservation
        assert ir["schema_version"] == "v0.4"
        assert len(ir["extractions"]) == 3
        
        # Check each critical indicator is preserved verbatim
        values = [ext["value"] for ext in ir["extractions"]]
        assert "$1,998.88" in values
        assert "VOID 2000" in values  
        assert "wa.me/123456789" in values
        
        # Verify no normalization artifacts
        for extraction in ir["extractions"]:
            value = extraction["value"]
            assert not any(artifact in value.lower() for artifact in 
                          ["normalized:", "cleaned:", "processed:"])
        
        # Verify provenance completeness
        for extraction in ir["extractions"]:
            provenance = extraction["provenance"]
            assert all(field in provenance for field in ["page", "start", "end"])
            assert isinstance(provenance["page"], int)
            assert isinstance(provenance["start"], int)
            assert isinstance(provenance["end"], int)
    
    def test_build_ir_fails_on_invented_categories(self):
        """Test V-002: Fail-first test for category invention"""
        extractions_raw = [
            {
                "value": "benign text",
                "kind": "text",
                "page": 1,
                "start": 0,
                "end": 11,
                "category_id": "normal",
                "span_id": "span_001"
            }
        ]
        
        source_doc = {"id": "test_doc", "pages": 1}
        
        # Build IR - should not invent threat categories
        ir = self.adapter.build_ir(extractions_raw, source_doc, self.config)
        
        # Verify no invented threat categories
        for extraction in ir["extractions"]:
            assert extraction["type"] != "threat"  # Should not be invented
            assert "malware" not in extraction.get("value", "").lower()
            assert "attack" not in extraction.get("value", "").lower()
    
    def test_compile_rules_preserves_indicators(self):
        """Test V-004: Rules preserve exact indicators"""
        ir = {
            "schema_version": "v0.4",
            "extractions": [
                {
                    "id": "ext_001",
                    "type": "amount",
                    "value": "$1,998.88",
                    "provenance": {"page": 1, "start": 100, "end": 109}
                },
                {
                    "id": "ext_002", 
                    "type": "link",
                    "value": "wa.me/123456789",
                    "provenance": {"page": 2, "start": 50, "end": 66}
                }
            ]
        }
        
        rules = self.adapter.compile_rules(ir, self.config)
        
        # Verify rules contain exact indicators
        assert "regex" in rules
        assert "json" in rules
        
        regex_rules = rules["regex"]
        json_rules = rules["json"]
        
        # Check verbatim preservation in regex
        assert "$1,998.88" in regex_rules or "\\$1,998\\.88" in regex_rules  # Escaped or literal
        assert "wa.me/123456789" in regex_rules or "wa\\.me/123456789" in regex_rules
        
        # Check JSON rules structure
        json_data = json.loads(json_rules)
        patterns = [rule["pattern"] for rule in json_data["rules"]]
        assert "$1,998.88" in patterns
        assert "wa.me/123456789" in patterns
    
    def test_draft_narrative_quotes_spans_verbatim(self):
        """Test narrative generation quotes spans exactly"""
        ir = {
            "extractions": [
                {
                    "id": "ext_001",
                    "type": "amount", 
                    "value": "$1,998.88",
                    "provenance": {"page": 1, "start": 100, "end": 109}
                },
                {
                    "id": "ext_002",
                    "type": "memo",
                    "value": "VOID 2000",
                    "provenance": {"page": 1, "start": 200, "end": 209}
                }
            ]
        }
        
        source_doc = {"id": "test_doc", "pages": 2}
        
        narrative = self.adapter.draft_narrative(ir, source_doc)
        
        # Verify verbatim quotes with span references
        assert '"$1,998.88"' in narrative  # Quoted verbatim
        assert '"VOID 2000"' in narrative
        assert "[p:1 100-109]" in narrative  # Span reference
        assert "[p:1 200-209]" in narrative
        
        # Verify verification checklist present
        assert "V-001" in narrative
        assert "V-005" in narrative
        assert "Verification Checklist" in narrative


class TestValidators:
    """Test validation functions"""
    
    def test_ir_validator_detects_missing_provenance(self):
        """Test V-003: Audit completeness validation"""
        validator = IRValidator()
        
        # IR with missing provenance
        ir_invalid = {
            "extractions": [
                {
                    "id": "ext_001",
                    "type": "amount",
                    "value": "$1,000",
                    # Missing provenance
                }
            ]
        }
        
        report = validator.validate_ir_against_golden(ir_invalid)
        
        assert not report["valid"]
        assert not report["gates"]["V-003"]["passed"]
        assert "missing provenance" in str(report["issues"]).lower()
    
    def test_rules_validator_catches_syntax_errors(self):
        """Test V-004: Rules syntax validation"""
        validator = RulesValidator()
        
        # Invalid regex rule
        rules_invalid = {
            "regex": "invalid[regex(pattern",  # Unmatched brackets
            "json": '{"invalid": json}',        # Invalid JSON
            "python": "def invalid_syntax(:\n    pass"  # Python syntax error
        }
        
        report = validator.validate_rules(rules_invalid)
        
        assert not report["valid"]
        assert not report["gates"]["V-004"]["passed"]
        
        # Check specific validations failed
        assert not report["rule_validations"]["regex"]["passed"]
        assert not report["rule_validations"]["json"]["passed"]
        assert not report["rule_validations"]["python"]["passed"]
    
    def test_validation_gate_checker_comprehensive(self):
        """Test comprehensive gate checking V-001 through V-005"""
        checker = ValidationGateChecker()
        
        # Valid IR and rules
        ir_valid = {
            "extractions": [
                {
                    "id": "ext_001",
                    "type": "amount",
                    "value": "$1,998.88",
                    "provenance": {"page": 1, "start": 100, "end": 109},
                    "source_span": {"span_id": "span_001"}
                }
            ]
        }
        
        rules_valid = {
            "regex": "\\$1,998\\.88  # source_refs: [0]",
            "json": '{"rules": [{"pattern": "$1,998.88", "source_refs": [0]}]}'
        }
        
        config_valid = {
            "model_name": "test-model",
            "targets": ["regex", "json"]
        }
        
        report = checker.check_all_gates(ir_valid, rules_valid, config_valid)
        
        # All gates should pass
        assert report["all_gates_passed"]
        assert report["summary"]["passed_gates"] == 5
        
        for gate_id in ["V-001", "V-002", "V-003", "V-004", "V-005"]:
            assert report["gates"][gate_id]["passed"], f"Gate {gate_id} should pass"


class TestAuditLogger:
    """Test audit logging functionality"""
    
    def setup_method(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.log_file = self.temp_dir / "test_audit.jsonl"
        self.logger = AuditLogger(self.log_file)
    
    def teardown_method(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_audit_chain_integrity(self):
        """Test tamper-evident audit chain"""
        # Log several events
        events = [
            {"event": "test_event_1", "run_id": "run_001", "data": "test1"},
            {"event": "test_event_2", "run_id": "run_001", "data": "test2"},
            {"event": "test_event_3", "run_id": "run_002", "data": "test3"}
        ]
        
        hashes = []
        for event in events:
            hash_val = self.logger.append(event)
            hashes.append(hash_val)
        
        # Verify chain integrity
        integrity_report = self.logger.verify_chain_integrity()
        
        assert integrity_report["intact"]
        assert integrity_report["total_entries"] == 4  # 3 events + genesis
        assert integrity_report["verified_entries"] == 4
        assert len(integrity_report["issues"]) == 0
    
    def test_audit_redacts_sensitive_data(self):
        """Test sensitive data redaction"""
        logger_redacting = AuditLogger(self.temp_dir / "redacted.jsonl", redact_sensitive=True)
        
        sensitive_event = {
            "event": "test_with_secrets",
            "run_id": "run_001", 
            "api_key": "secret_key_12345",
            "model_response": "The API key sk-1234567890abcdef is sensitive",
            "normal_data": "this is fine"
        }
        
        logger_redacting.append(sensitive_event)
        
        # Read back and verify redaction
        entries = logger_redacting.get_recent_entries(limit=1)
        last_entry = entries[0]
        
        assert last_entry["data"]["api_key"] == "[REDACTED]"
        assert "secret_key_12345" not in json.dumps(last_entry)
        assert "this is fine" in json.dumps(last_entry)  # Normal data preserved


class TestGoldenCases:
    """Golden test cases for exact string preservation"""
    
    def setup_method(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.audit_log = self.temp_dir / "golden_audit.jsonl"
        self.audit_logger = AuditLogger(self.audit_log)
        self.config = {
            "model_name": "test-model",
            "targets": ["regex", "json", "python"],
            "temperature": 0
        }
        self.adapter = LLMAdapter(self.config, self.audit_logger)
    
    def teardown_method(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @pytest.mark.parametrize("indicator,expected_type", [
        ("$1,998.88", "amount"),
        ("VOID 2000", "memo"), 
        ("wa.me/123456789", "link"),
        ("bitcoin:1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", "link"),
        ("telegram: @scammer123", "link")
    ])
    def test_golden_indicator_preservation(self, indicator, expected_type):
        """Golden test: Critical indicators preserved exactly"""
        extraction_raw = {
            "value": indicator,
            "kind": expected_type if expected_type != "link" else "domain",
            "page": 1,
            "start": 0,
            "end": len(indicator),
            "category_id": "test",
            "span_id": f"span_{hash(indicator)}"
        }
        
        source_doc = {"id": "golden_test", "pages": 1}
        
        # Process through full pipeline
        ir = self.adapter.build_ir([extraction_raw], source_doc, self.config)
        rules = self.adapter.compile_rules(ir, self.config)
        narrative = self.adapter.draft_narrative(ir, source_doc)
        
        # Verify exact preservation in all outputs
        assert any(ext["value"] == indicator for ext in ir["extractions"])
        
        # For regex, check either literal or escaped version is present
        escaped_indicator = indicator.replace("\\", "\\\\").replace(".", "\\.").replace(" ", "\\ ")
        assert (indicator in rules["regex"] or 
                escaped_indicator in rules["regex"] or
                indicator.replace(".", "\\.") in rules["regex"]), f"Neither '{indicator}' nor '{escaped_indicator}' found in regex rules: {rules['regex']}"
        
        assert indicator in json.loads(rules["json"])["rules"][0]["pattern"]
        assert f'"{indicator}"' in narrative  # Quoted in narrative
    
    def test_golden_category_diff_empty(self):
        """Golden test G-010: Category diff must be empty"""
        # No categories in source -> no categories should be generated
        extractions_raw = [
            {
                "value": "normal text",
                "kind": "text", 
                "page": 1,
                "start": 0,
                "end": 11,
                "category_id": "general",
                "span_id": "span_001"
            }
        ]
        
        source_doc = {"id": "category_test", "pages": 1}
        
        ir = self.adapter.build_ir(extractions_raw, source_doc, self.config)
        
        # Should not generate category-type extractions from non-category source
        category_extractions = [ext for ext in ir["extractions"] if ext["type"] == "category"]
        assert len(category_extractions) == 0  # diff(generated, source) == ∅
    
    def test_negative_no_invention(self):
        """Negative test: No invention of facts or categories"""
        # Benign input with no threat indicators
        extractions_raw = [
            {
                "value": "contact support",
                "kind": "text",
                "page": 1, 
                "start": 0,
                "end": 15,
                "category_id": "help",
                "span_id": "span_help"
            }
        ]
        
        source_doc = {"id": "benign_test", "pages": 1}
        
        ir = self.adapter.build_ir(extractions_raw, source_doc, self.config)
        
        # Should not invent threat-related content
        forbidden_content = ["malware", "attack", "threat", "exploit", "phishing"]
        
        for extraction in ir["extractions"]:
            value_lower = extraction["value"].lower()
            for forbidden in forbidden_content:
                assert forbidden not in value_lower, f"Invented forbidden content: {forbidden}"


class TestDeterminism:
    """Test deterministic output requirements"""
    
    def setup_method(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.audit_log = self.temp_dir / "determinism_audit.jsonl"
        self.audit_logger = AuditLogger(self.audit_log)
        self.config = {
            "model_name": "test-model",
            "targets": ["regex", "json"],
            "temperature": 0  # Deterministic
        }
    
    def teardown_method(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_deterministic_ir_generation(self):
        """Test repeated runs yield identical IR"""
        extractions_raw = [
            {
                "value": "$1,998.88",
                "kind": "amount",
                "page": 1,
                "start": 100,
                "end": 109,
                "category_id": "financial",
                "span_id": "span_001"
            }
        ]
        
        source_doc = {"id": "determinism_test", "pages": 1}
        
        # Run twice
        adapter1 = LLMAdapter(self.config, self.audit_logger)
        adapter2 = LLMAdapter(self.config, self.audit_logger)
        
        ir1 = adapter1.build_ir(extractions_raw, source_doc, self.config)
        ir2 = adapter2.build_ir(extractions_raw, source_doc, self.config)
        
        # Remove timestamps for comparison
        ir1_clean = {k: v for k, v in ir1.items() if k != "metadata"}
        ir2_clean = {k: v for k, v in ir2.items() if k != "metadata"}
        
        # Should be identical (ignoring metadata timestamps)
        assert ir1_clean["extractions"] == ir2_clean["extractions"]
        assert ir1_clean["schema_version"] == ir2_clean["schema_version"]
    
    def test_deterministic_rules_generation(self):
        """Test repeated rule compilation yields identical results"""
        ir = {
            "schema_version": "v0.4",
            "extractions": [
                {
                    "id": "ext_001",
                    "type": "amount",
                    "value": "$1,998.88", 
                    "provenance": {"page": 1, "start": 100, "end": 109}
                }
            ]
        }
        
        adapter1 = LLMAdapter(self.config, self.audit_logger)
        adapter2 = LLMAdapter(self.config, self.audit_logger)
        
        rules1 = adapter1.compile_rules(ir, self.config)
        rules2 = adapter2.compile_rules(ir, self.config)
        
        # Rules should be byte-identical
        assert rules1 == rules2


# Pytest fixtures for integration tests
@pytest.fixture
def sample_extractions():
    """Sample extraction data for testing"""
    return [
        {
            "value": "$1,998.88",
            "kind": "amount",
            "page": 1,
            "start": 100,
            "end": 109,
            "category_id": "financial",
            "span_id": "span_001"
        },
        {
            "value": "wa.me/123456789",
            "kind": "domain", 
            "page": 2,
            "start": 50,
            "end": 66,
            "category_id": "contact",
            "span_id": "span_002"
        }
    ]

@pytest.fixture  
def sample_source_doc():
    """Sample source document for testing"""
    return {
        "id": "test_document_001",
        "pages": 2,
        "title": "Test Intelligence Report"
    }


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])