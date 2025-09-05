#!/usr/bin/env python3
"""Integration tests for v1.0 pilot readiness workflow."""

import unittest
import json
import tempfile
from pathlib import Path
import sys
import shutil

# Add root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

class TestV10Integration(unittest.TestCase):
    """Integration tests for complete v1.0 pilot readiness workflow."""
    
    def setUp(self):
        """Set up test environment."""
        self.root = Path(__file__).resolve().parents[2]
        self.test_dir = Path(tempfile.mkdtemp())
        self.artifacts_dir = self.test_dir / "artifacts"
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        
        # Mock expansions data
        self.test_expansions = {
            "expansions": [
                {
                    "pattern": "gift.*card",
                    "operator": "match",
                    "status": "ready",
                    "justification": "Explicit enumeration in PDF section 3.2",
                    "evidence_quote": "The scammer will ask for gift cards",
                    "parent_spans": ["span_123"]
                },
                {
                    "pattern": "wire.*transfer",
                    "operator": "match", 
                    "status": "ready",
                    "justification": "Common payment method referenced",
                    "evidence_quote": "Request wire transfer to overseas account",
                    "parent_spans": ["span_456"]
                },
                {
                    "pattern": "crypto.*currency",
                    "operator": "match",
                    "status": "advisory"  # Should be filtered out
                }
            ]
        }
        
        # Mock backtest data
        self.test_backtest = {
            "rules": {
                "gift.*card": {
                    "false_positive_rate": 0.002,  # Low FPR - should pass
                    "true_positive_rate": 0.85,
                    "samples_tested": 100
                },
                "wire.*transfer": {
                    "false_positive_rate": 0.02,   # High FPR - should fail
                    "true_positive_rate": 0.9,
                    "samples_tested": 150
                }
            }
        }
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_complete_pilot_readiness_workflow(self):
        """Test the complete v1.0 pilot readiness workflow end-to-end."""
        
        # Step 1: Write test data files
        expansions_file = self.artifacts_dir / "proactive" / "expansions.json"
        backtest_file = self.artifacts_dir / "proactive" / "backtest_report.json"
        
        expansions_file.parent.mkdir(parents=True, exist_ok=True)
        backtest_file.parent.mkdir(parents=True, exist_ok=True)
        
        expansions_file.write_text(json.dumps(self.test_expansions))
        backtest_file.write_text(json.dumps(self.test_backtest))
        
        # Step 2: Run confidence scoring annotation
        from scripts.annotate_confidence import main as annotate_main
        
        # Mock sys.argv for the script
        original_argv = sys.argv
        sys.argv = [
            "annotate_confidence.py",
            "--backtest", str(backtest_file),
            "--expansions", str(expansions_file),
            "--output", str(expansions_file)  # Update in place
        ]
        
        try:
            result = annotate_main()
            self.assertEqual(result, 0)  # Success
        except SystemExit as e:
            self.assertEqual(e.code, 0)
        finally:
            sys.argv = original_argv
        
        # Step 3: Verify confidence scoring results
        enhanced_data = json.loads(expansions_file.read_text())
        enhanced_expansions = enhanced_data["expansions"]
        
        for exp in enhanced_expansions:
            if exp.get("status") in ["ready", "ready-deploy"]:
                self.assertIn("confidence_score", exp)
                self.assertIn("risk_tier", exp)
                self.assertIsInstance(exp["confidence_score"], float)
                self.assertGreaterEqual(exp["confidence_score"], 0.0)
                self.assertLessEqual(exp["confidence_score"], 1.0)
        
        # Step 4: Run governance decision workflow
        from src.agentic.decisions import pick_candidates, assign_targets
        from src.agentic.policy import DEFAULT_POLICY
        
        candidates = pick_candidates(enhanced_data, self.test_backtest, DEFAULT_POLICY)
        
        # Verify candidate selection
        self.assertEqual(len(candidates), 2)  # Only ready/ready-deploy items
        
        candidate_patterns = [c["pattern"] for c in candidates]
        self.assertIn("gift.*card", candidate_patterns)
        self.assertIn("wire.*transfer", candidate_patterns)
        
        # Step 5: Check governance decisions
        for candidate in candidates:
            if candidate["pattern"] == "gift.*card":
                # Low FPR should pass
                self.assertEqual(candidate["decision"], "ready-deploy")
                self.assertTrue(candidate["deployment_candidate"])
            elif candidate["pattern"] == "wire.*transfer":
                # High FPR should require review
                self.assertEqual(candidate["decision"], "ready-review")
                self.assertFalse(candidate["deployment_candidate"])
        
        # Step 6: Enhance candidates with metadata (simulate governance requirements)
        for c in candidates:
            if c["decision"] == "ready-deploy":
                c.update({
                    "severity_label": "Medium",
                    "rule_owner": "Sigma",
                    "detection_type": "hunting",
                    "sla": 48
                })
        
        # Step 7: Run target assignment (governance gates)
        proposals = assign_targets(candidates, DEFAULT_POLICY)
        
        # Only gift.*card should generate proposals (has required metadata and passes FPR)
        self.assertGreater(len(proposals), 0)
        proposal_patterns = [p["pattern"] for p in proposals]
        self.assertIn("gift.*card", proposal_patterns)
        
        # Verify governance attestation
        for proposal in proposals:
            self.assertEqual(proposal["governance_status"], "approved")
            self.assertIn("target_system", proposal)
            self.assertIn(proposal["target_system"], DEFAULT_POLICY.allowed_targets)
        
        # Step 8: Test orchestrator integration
        from src.agentic.orchestrator import Orchestrator
        
        # Mock the orchestrator's artifact paths to use our test directory
        orchestrator = Orchestrator(self.test_dir)
        orchestrator.art = self.artifacts_dir
        
        try:
            output_dir = orchestrator.run()
            
            # Verify orchestrator outputs
            self.assertTrue(output_dir.exists())
            self.assertTrue((output_dir / "plan.json").exists())
            self.assertTrue((output_dir / "decisions.json").exists())
            self.assertTrue((output_dir / "governance_report.json").exists())
            
            # Verify governance report content
            governance_report = json.loads((output_dir / "governance_report.json").read_text())
            
            self.assertIn("governance_summary", governance_report)
            self.assertIn("escalations", governance_report)
            self.assertIn("ready_for_review", governance_report)
            self.assertIn("approved_for_deployment", governance_report)
            
            governance_stats = governance_report["governance_summary"]
            self.assertGreater(governance_stats["total_candidates"], 0)
            self.assertGreaterEqual(governance_stats["governance_pass_rate"], 0.0)
            
        except Exception as e:
            # Skip orchestrator test if memory module not available
            if "memory" in str(e):
                self.skipTest(f"Memory module not available: {e}")
            else:
                raise
    
    def test_risk_tier_policy_compliance(self):
        """Test risk tier policy compliance validation."""
        
        # Test data with various FPR/confidence combinations
        test_cases = [
            {"fpr": 0.001, "confidence": 0.95, "expected_tier": "blocking"},
            {"fpr": 0.01, "confidence": 0.75, "expected_tier": "hunting"},
            {"fpr": 0.05, "confidence": 0.5, "expected_tier": "enrichment"},
            {"fpr": 0.15, "confidence": 0.3, "expected_tier": None}  # Should fail all tiers
        ]
        
        from src.metrics.confidence import assign_risk_tier_from_confidence
        
        for case in test_cases:
            tier = assign_risk_tier_from_confidence(case["confidence"], case["fpr"])
            self.assertEqual(tier, case["expected_tier"], 
                           f"FPR {case['fpr']}, confidence {case['confidence']} should map to {case['expected_tier']}, got {tier}")
    
    def test_governance_escalation_paths(self):
        """Test that governance escalation paths work correctly."""
        
        from src.agentic.decisions import assign_targets
        from unittest.mock import MagicMock
        
        policy = MagicMock()
        policy.allowed_targets = ["shadow"]
        
        # Test various escalation scenarios
        scenarios = [
            {
                "name": "missing_confidence",
                "candidate": {
                    "decision": "ready-deploy",
                    "risk_tier": "hunting",
                    "severity_label": "Medium",
                    "rule_owner": "Sigma",
                    "detection_type": "hunting",
                    "sla": 48
                },
                "expected_escalation": "escalate-missing-confidence"
            },
            {
                "name": "missing_risk_tier",
                "candidate": {
                    "decision": "ready-deploy",
                    "confidence_score": 0.8,
                    "severity_label": "Medium", 
                    "rule_owner": "Sigma",
                    "detection_type": "hunting",
                    "sla": 48
                },
                "expected_escalation": "escalate-missing-tier"
            },
            {
                "name": "missing_metadata",
                "candidate": {
                    "decision": "ready-deploy",
                    "confidence_score": 0.8,
                    "risk_tier": "hunting"
                    # Missing required metadata
                },
                "expected_escalation": "escalate-missing-metadata"
            }
        ]
        
        for scenario in scenarios:
            candidate = scenario["candidate"].copy()
            proposals = assign_targets([candidate], policy)
            
            # Should generate no proposals due to escalation
            self.assertEqual(len(proposals), 0, f"Scenario {scenario['name']} should generate no proposals")
            
            # Should update decision to escalation
            self.assertEqual(candidate["decision"], scenario["expected_escalation"],
                           f"Scenario {scenario['name']} should escalate to {scenario['expected_escalation']}")
            
            # Should have escalation reason
            self.assertIn("escalation_reason", candidate, 
                         f"Scenario {scenario['name']} should have escalation reason")
    
    def test_report_rendering_with_v10_features(self):
        """Test that v1.0 report rendering includes pilot readiness features."""
        
        # Create mock data with v1.0 features
        expansions_with_v10 = {
            "expansions": [
                {
                    "pattern": "test.*pattern",
                    "operator": "match",
                    "status": "ready",
                    "confidence_score": 0.85,
                    "risk_tier": "hunting",
                    "decision": "ready-deploy",
                    "fpr": 0.002,
                    "justification": "Test justification",
                    "evidence_quote": "Test evidence"
                }
            ]
        }
        
        # Write test data
        expansions_file = self.artifacts_dir / "proactive" / "expansions.json"
        expansions_file.parent.mkdir(parents=True, exist_ok=True)
        expansions_file.write_text(json.dumps(expansions_with_v10))
        
        # Create mock governance report  
        governance_report = {
            "governance_summary": {
                "total_candidates": 1,
                "ready_deploy": 1,
                "ready_review": 0,
                "governance_pass_rate": 1.0
            }
        }
        
        # Create agentic run directory
        agentic_dir = self.test_dir / "agentic" / "run_12345"
        agentic_dir.mkdir(parents=True, exist_ok=True)
        (agentic_dir / "governance_report.json").write_text(json.dumps(governance_report))
        
        # Mock the paths for the report renderer
        import sys
        original_root = None
        original_art = None
        
        try:
            # Temporarily modify the render script's paths
            sys.path.insert(0, str(self.root / "scripts"))
            
            from scripts.render_report_v10_pilot import ROOT, ART
            
            # Backup original values
            original_root = ROOT
            original_art = ART
            
            # Override with test paths
            import scripts.render_report_v10_pilot as render_module
            render_module.ROOT = self.test_dir
            render_module.ART = self.artifacts_dir
            
            # Run the renderer
            render_module.render()
            
            # Check that report was generated
            report_file = self.artifacts_dir / "demo_report_v10_pilot.html"
            self.assertTrue(report_file.exists())
            
            content = report_file.read_text()
            
            # Verify v1.0 pilot readiness features are present
            self.assertIn("v1.0 Pilot Readiness", content)
            self.assertIn("Governance Dashboard", content)
            self.assertIn("confidence-bar", content)  # CSS class for confidence bars
            self.assertIn("tier-hunting", content)    # CSS class for risk tiers
            self.assertIn("gov-approved", content)    # CSS class for governance status
            
        except ImportError as e:
            self.skipTest(f"Report renderer not available: {e}")
        
        finally:
            # Restore original values
            if original_root and original_art:
                try:
                    import scripts.render_report_v10_pilot as render_module
                    render_module.ROOT = original_root
                    render_module.ART = original_art
                except:
                    pass

if __name__ == '__main__':
    unittest.main()