#!/usr/bin/env python3
"""Tests for v1.0 adapter metadata enhancements."""

import unittest
import json
import tempfile
from pathlib import Path
import sys
import os

# Add root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

class TestAdapterMetadata(unittest.TestCase):
    """Test adapter metadata enhancements for v1.0."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.root = Path(__file__).resolve().parents[2]
        self.test_rules = {
            "json": {
                "indicators": [
                    {
                        "kind": "verbatim",
                        "verbatim": "gift cards",
                        "category_id": "payment_method",
                        "span_id": "span_123"
                    },
                    {
                        "kind": "verbatim", 
                        "verbatim": "wire transfer",
                        "category_id": "payment_method",
                        "span_id": "span_456"
                    }
                ]
            }
        }
    
    def test_splunk_adapter_metadata(self):
        """Test Splunk adapter includes required metadata."""
        # Create temporary rules file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.test_rules, f)
            rules_path = Path(f.name)
        
        try:
            # Import and run Splunk compiler
            sys.path.insert(0, str(self.root / "adapters" / "splunk"))
            from adapters.splunk.compile import main
            
            # Mock the artifact path to point to our test file
            original_art = self.root / "artifacts" / "demo_rules.json"
            backup_exists = original_art.exists()
            if backup_exists:
                backup_content = original_art.read_text()
            
            # Write test data to expected location
            original_art.parent.mkdir(parents=True, exist_ok=True)
            original_art.write_text(json.dumps(self.test_rules))
            
            # Run compiler
            result = main()
            
            # Check output file
            output_file = self.root / "adapters" / "splunk" / "out" / "splunk_rules.spl"
            self.assertTrue(output_file.exists())
            
            content = output_file.read_text()
            
            # Verify metadata comments are present
            self.assertIn("/* severity_label: Medium */", content)
            self.assertIn("/* rule_owner: Sigma */", content)
            self.assertIn("/* detection_type: hunting */", content)
            self.assertIn("/* sla: 48 hours */", content)
            self.assertIn("/* log_field_targets: _raw, message */", content)
            
            # Verify field mapping guidance
            self.assertIn("/* Field Mapping Guide: Map to your index fields */", content)
            self.assertIn("/* Common fields: caller_id, payment_method, message */", content)
            
            # Verify actual search queries
            self.assertIn('search _raw=".*gift cards.*"', content)
            self.assertIn('search _raw=".*wire transfer.*"', content)
        
        finally:
            # Cleanup
            rules_path.unlink()
            if backup_exists:
                original_art.write_text(backup_content)
            elif original_art.exists():
                original_art.unlink()
    
    def test_elastic_adapter_metadata(self):
        """Test Elastic adapter includes required metadata."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.test_rules, f)
            rules_path = Path(f.name)
        
        try:
            # Import and run Elastic compiler
            sys.path.insert(0, str(self.root / "adapters" / "elastic"))
            from adapters.elastic.compile import main
            
            # Mock the artifact path
            original_art = self.root / "artifacts" / "demo_rules.json"
            backup_exists = original_art.exists()
            if backup_exists:
                backup_content = original_art.read_text()
            
            original_art.parent.mkdir(parents=True, exist_ok=True) 
            original_art.write_text(json.dumps(self.test_rules))
            
            # Run compiler
            result = main()
            
            # Check output file
            output_file = self.root / "adapters" / "elastic" / "out" / "elastic_rules.json"
            self.assertTrue(output_file.exists())
            
            content = output_file.read_text()
            data = json.loads(content)
            
            # Verify it's an array of rules
            self.assertIsInstance(data, list)
            self.assertGreater(len(data), 0)
            
            # Check first rule structure
            rule = data[0]
            self.assertIn("query", rule)
            self.assertIn("metadata", rule)
            
            # Verify metadata fields
            metadata = rule["metadata"]
            self.assertEqual(metadata["severity_label"], "Medium")
            self.assertEqual(metadata["rule_owner"], "Sigma")
            self.assertEqual(metadata["detection_type"], "hunting")
            self.assertEqual(metadata["sla"], 48)
            self.assertEqual(metadata["staleness_days"], 0)
            self.assertEqual(metadata["log_field_targets"], ["message"])
            
        finally:
            # Cleanup
            rules_path.unlink()
            if backup_exists:
                original_art.write_text(backup_content)
            elif original_art.exists():
                original_art.unlink()
    
    def test_sql_adapter_metadata(self):
        """Test SQL adapter includes required metadata."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.test_rules, f)
            rules_path = Path(f.name)
        
        try:
            # Import and run SQL compiler
            sys.path.insert(0, str(self.root / "adapters" / "sql"))
            from adapters.sql.compile import main
            
            # Mock the artifact path
            original_art = self.root / "artifacts" / "demo_rules.json" 
            backup_exists = original_art.exists()
            if backup_exists:
                backup_content = original_art.read_text()
            
            original_art.parent.mkdir(parents=True, exist_ok=True)
            original_art.write_text(json.dumps(self.test_rules))
            
            # Run compiler
            result = main()
            
            # Check output file
            output_file = self.root / "adapters" / "sql" / "out" / "sql_rules.sql"
            self.assertTrue(output_file.exists())
            
            content = output_file.read_text()
            
            # Verify SQL metadata comments
            self.assertIn("-- Rule Owner: Sigma", content)
            self.assertIn("-- Severity: Medium", content)
            self.assertIn("-- Detection Type: hunting", content)
            self.assertIn("-- SLA: 48 hours", content)
            self.assertIn("-- Log Field Targets: message", content)
            
            # Verify actual SQL queries
            self.assertIn("WHERE message REGEXP 'gift cards'", content)
            self.assertIn("WHERE message REGEXP 'wire transfer'", content)
            
        finally:
            # Cleanup
            rules_path.unlink()
            if backup_exists:
                original_art.write_text(backup_content)
            elif original_art.exists():
                original_art.unlink()
    
    def test_field_mapping_guides_exist(self):
        """Test that field mapping guides are present for all adapters."""
        adapters = ["splunk", "elastic", "sql"]
        
        for adapter in adapters:
            mapping_file = self.root / "adapters" / adapter / "MAPPING.md"
            self.assertTrue(mapping_file.exists(), f"Missing mapping guide for {adapter}")
            
            content = mapping_file.read_text()
            
            # Verify essential mapping content
            self.assertIn("Field Mapping", content)
            self.assertIn("message", content)  # Should have message field mapping
            self.assertIn("caller_id", content)  # Should have caller_id mapping
            self.assertIn("payment_method", content)  # Should have payment method mapping
    
    def test_adapter_compilation_logs(self):
        """Test that adapters generate proper compilation logs."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.test_rules, f)
            rules_path = Path(f.name)
        
        try:
            original_art = self.root / "artifacts" / "demo_rules.json"
            backup_exists = original_art.exists()
            if backup_exists:
                backup_content = original_art.read_text()
            
            original_art.parent.mkdir(parents=True, exist_ok=True)
            original_art.write_text(json.dumps(self.test_rules))
            
            # Test all adapters
            adapters = ["splunk", "elastic", "sql"]
            for adapter in adapters:
                sys.path.insert(0, str(self.root / "adapters" / adapter))
                
                if adapter == "splunk":
                    from adapters.splunk.compile import main
                elif adapter == "elastic":
                    from adapters.elastic.compile import main
                elif adapter == "sql":
                    from adapters.sql.compile import main
                
                result = main()
                
                # Check compilation log
                log_file = self.root / "adapters" / adapter / "compile_log.txt"
                self.assertTrue(log_file.exists(), f"Missing compile log for {adapter}")
                
                log_content = log_file.read_text()
                self.assertIn("compiled=", log_content)
                self.assertIn("errors=", log_content)
        
        finally:
            # Cleanup
            rules_path.unlink()
            if backup_exists:
                original_art.write_text(backup_content)
            elif original_art.exists():
                original_art.unlink()

class TestMetadataValidation(unittest.TestCase):
    """Test metadata validation for v1.0 compliance."""
    
    def test_required_metadata_fields(self):
        """Test that required metadata fields are defined."""
        required_fields = [
            "severity_label", 
            "rule_owner",
            "detection_type",
            "sla"
        ]
        
        # Check that governance decisions module references these fields
        decisions_file = Path(__file__).resolve().parents[2] / "src" / "agentic" / "decisions.py"
        self.assertTrue(decisions_file.exists())
        
        content = decisions_file.read_text()
        
        # Verify required metadata fields are checked
        self.assertIn("required_metadata", content)
        for field in required_fields:
            self.assertIn(field, content)
    
    def test_metadata_field_validation_logic(self):
        """Test the metadata validation logic directly."""
        from src.agentic.decisions import assign_targets
        from unittest.mock import MagicMock
        
        policy = MagicMock()
        policy.allowed_targets = ["shadow"]
        
        # Test complete metadata
        complete_candidate = {
            "decision": "ready-deploy",
            "confidence_score": 0.8,
            "risk_tier": "hunting",
            "severity_label": "Medium",
            "rule_owner": "Sigma", 
            "detection_type": "hunting",
            "sla": 48
        }
        
        proposals = assign_targets([complete_candidate], policy)
        self.assertGreater(len(proposals), 0)
        
        # Test incomplete metadata
        incomplete_candidate = {
            "decision": "ready-deploy",
            "confidence_score": 0.8,
            "risk_tier": "hunting"
            # Missing required metadata
        }
        
        proposals = assign_targets([incomplete_candidate], policy)
        self.assertEqual(len(proposals), 0)  # Should be escalated, no proposals
        
        # Check escalation
        self.assertEqual(incomplete_candidate["decision"], "escalate-missing-metadata")
        self.assertIn("escalation_reason", incomplete_candidate)

if __name__ == '__main__':
    unittest.main()