#!/usr/bin/env python3
"""Tests for v1.0 governance decision system."""

import unittest
from unittest.mock import MagicMock
from src.agentic.decisions import pick_candidates, assign_targets, _has_strong_justification

class MockPolicy:
    """Mock policy for testing."""
    def __init__(self):
        self.max_fpr = 0.005
        self.require_justification = True
        self.allowed_targets = ["shadow", "limited"]

class TestGovernanceDecisions(unittest.TestCase):
    """Test governance decision logic."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.policy = MockPolicy()
    
    def test_has_strong_justification_complete(self):
        """Test justification validation with complete fields."""
        expansion = {
            "justification": "Explicit enumeration in PDF section 3.2",
            "evidence_quote": "The scammer will ask for gift cards, wire transfers, or crypto",
            "operator": "match"
        }
        self.assertTrue(_has_strong_justification(expansion))
    
    def test_has_strong_justification_missing_fields(self):
        """Test justification validation with missing fields."""
        # Missing justification
        expansion = {
            "evidence_quote": "Some evidence",
            "operator": "match"
        }
        self.assertFalse(_has_strong_justification(expansion))
        
        # Empty justification
        expansion = {
            "justification": "",
            "evidence_quote": "Some evidence", 
            "operator": "match"
        }
        self.assertFalse(_has_strong_justification(expansion))
        
        # Missing evidence quote
        expansion = {
            "justification": "Some justification",
            "operator": "match"
        }
        self.assertFalse(_has_strong_justification(expansion))
    
    def test_pick_candidates_status_filtering(self):
        """Test that only ready/ready-deploy items are considered."""
        expansions = {
            "expansions": [
                {"pattern": "test1", "status": "ready", "justification": "test", "evidence_quote": "test", "operator": "match"},
                {"pattern": "test2", "status": "advisory"}, # Should be filtered out
                {"pattern": "test3", "status": "ready-deploy", "justification": "test", "evidence_quote": "test", "operator": "match"}
            ]
        }
        backtest = {"rules": {"test1": {"false_positive_rate": 0.001}, "test3": {"false_positive_rate": 0.001}}}
        
        candidates = pick_candidates(expansions, backtest, self.policy)
        
        # Only ready and ready-deploy should be included
        self.assertEqual(len(candidates), 2)
        patterns = [c["pattern"] for c in candidates]
        self.assertIn("test1", patterns)
        self.assertIn("test3", patterns)
        self.assertNotIn("test2", patterns)
    
    def test_pick_candidates_fpr_filtering(self):
        """Test FPR threshold filtering."""
        expansions = {
            "expansions": [
                {"pattern": "low_fpr", "status": "ready", "justification": "test", "evidence_quote": "test", "operator": "match"},
                {"pattern": "high_fpr", "status": "ready", "justification": "test", "evidence_quote": "test", "operator": "match"}
            ]
        }
        backtest = {
            "rules": {
                "low_fpr": {"false_positive_rate": 0.001},   # Under threshold
                "high_fpr": {"false_positive_rate": 0.01}    # Over threshold  
            }
        }
        
        candidates = pick_candidates(expansions, backtest, self.policy)
        
        # Check deployment decisions
        for c in candidates:
            if c["pattern"] == "low_fpr":
                self.assertEqual(c["decision"], "ready-deploy")
                self.assertTrue(c["deployment_candidate"])
            elif c["pattern"] == "high_fpr":
                self.assertEqual(c["decision"], "ready-review") 
                self.assertFalse(c["deployment_candidate"])
    
    def test_pick_candidates_justification_requirement(self):
        """Test justification requirement enforcement."""
        expansions = {
            "expansions": [
                {"pattern": "with_justification", "status": "ready", "justification": "test", "evidence_quote": "test", "operator": "match"},
                {"pattern": "without_justification", "status": "ready"}  # Missing justification
            ]
        }
        backtest = {
            "rules": {
                "with_justification": {"false_positive_rate": 0.001},
                "without_justification": {"false_positive_rate": 0.001}
            }
        }
        
        candidates = pick_candidates(expansions, backtest, self.policy)
        
        for c in candidates:
            if c["pattern"] == "with_justification":
                self.assertEqual(c["decision"], "ready-deploy")
            elif c["pattern"] == "without_justification":
                self.assertEqual(c["decision"], "ready-review")  # Should fail justification check
    
    def test_assign_targets_confidence_validation(self):
        """Test confidence score validation gate."""
        candidates = [
            {
                "pattern": "with_confidence",
                "decision": "ready-deploy",
                "confidence_score": 0.85,
                "risk_tier": "hunting",
                "severity_label": "Medium",
                "rule_owner": "Sigma",
                "detection_type": "hunting", 
                "sla": 48
            },
            {
                "pattern": "without_confidence",
                "decision": "ready-deploy",
                "risk_tier": "hunting",
                "severity_label": "Medium",
                "rule_owner": "Sigma",
                "detection_type": "hunting",
                "sla": 48
            }
        ]
        
        proposals = assign_targets(candidates, self.policy)
        
        # First candidate should generate proposals
        with_conf_patterns = [p["pattern"] for p in proposals if p["pattern"] == "with_confidence"]
        self.assertGreater(len(with_conf_patterns), 0)
        
        # Second candidate should be escalated
        escalated = [c for c in candidates if c["decision"] == "escalate-missing-confidence"]
        self.assertEqual(len(escalated), 1)
        self.assertEqual(escalated[0]["pattern"], "without_confidence")
    
    def test_assign_targets_risk_tier_validation(self):
        """Test risk tier validation gate."""
        candidates = [
            {
                "pattern": "with_tier",
                "decision": "ready-deploy", 
                "confidence_score": 0.85,
                "risk_tier": "hunting",
                "severity_label": "Medium",
                "rule_owner": "Sigma",
                "detection_type": "hunting",
                "sla": 48
            },
            {
                "pattern": "without_tier",
                "decision": "ready-deploy",
                "confidence_score": 0.85,
                "severity_label": "Medium", 
                "rule_owner": "Sigma",
                "detection_type": "hunting",
                "sla": 48
            }
        ]
        
        proposals = assign_targets(candidates, self.policy)
        
        # First should succeed, second should be escalated
        escalated = [c for c in candidates if c["decision"] == "escalate-missing-tier"]
        self.assertEqual(len(escalated), 1)
        self.assertEqual(escalated[0]["pattern"], "without_tier")
    
    def test_assign_targets_metadata_validation(self):
        """Test metadata validation gate.""" 
        candidates = [
            {
                "pattern": "complete_metadata",
                "decision": "ready-deploy",
                "confidence_score": 0.85,
                "risk_tier": "hunting",
                "severity_label": "Medium",
                "rule_owner": "Sigma", 
                "detection_type": "hunting",
                "sla": 48
            },
            {
                "pattern": "missing_metadata",
                "decision": "ready-deploy",
                "confidence_score": 0.85,
                "risk_tier": "hunting"
                # Missing severity_label, rule_owner, detection_type, sla
            }
        ]
        
        proposals = assign_targets(candidates, self.policy)
        
        # Complete metadata should generate proposals
        complete_proposals = [p for p in proposals if p["pattern"] == "complete_metadata"]
        self.assertGreater(len(complete_proposals), 0)
        
        # Missing metadata should be escalated
        escalated = [c for c in candidates if c["decision"] == "escalate-missing-metadata"]
        self.assertEqual(len(escalated), 1)
        self.assertEqual(escalated[0]["pattern"], "missing_metadata")
        self.assertIn("escalation_reason", escalated[0])
        self.assertIn("Missing required metadata", escalated[0]["escalation_reason"])
    
    def test_assign_targets_governance_attestation(self):
        """Test that approved proposals receive governance attestation."""
        candidates = [
            {
                "pattern": "approved_rule",
                "decision": "ready-deploy",
                "confidence_score": 0.85,
                "risk_tier": "hunting",
                "severity_label": "Medium",
                "rule_owner": "Sigma",
                "detection_type": "hunting",
                "sla": 48
            }
        ]
        
        proposals = assign_targets(candidates, self.policy)
        
        # Should have proposals for both allowed targets
        self.assertEqual(len(proposals), 2)  # shadow + limited targets
        
        for proposal in proposals:
            self.assertEqual(proposal["governance_status"], "approved")
            self.assertIsNotNone(proposal["governance_timestamp"])
            self.assertIn(proposal["target_system"], ["shadow", "limited"])
    
    def test_assign_targets_skip_non_deploy_decisions(self):
        """Test that non-ready-deploy decisions are skipped."""
        candidates = [
            {
                "pattern": "needs_review",
                "decision": "ready-review",
                "confidence_score": 0.85,
                "risk_tier": "hunting"
            }
        ]
        
        proposals = assign_targets(candidates, self.policy)
        
        # Should generate no proposals
        self.assertEqual(len(proposals), 0)

class TestGovernanceIntegration(unittest.TestCase):
    """Integration tests for governance workflow."""
    
    def test_end_to_end_governance_flow(self):
        """Test complete governance flow from expansions to proposals."""
        policy = MockPolicy()
        
        # Mock expansions with various scenarios
        expansions = {
            "expansions": [
                {
                    "pattern": "perfect_candidate",
                    "status": "ready",
                    "justification": "Explicit in PDF",
                    "evidence_quote": "Clear evidence",
                    "operator": "match"
                },
                {
                    "pattern": "high_fpr_candidate", 
                    "status": "ready",
                    "justification": "Explicit in PDF",
                    "evidence_quote": "Clear evidence",
                    "operator": "match"
                },
                {
                    "pattern": "advisory_candidate",
                    "status": "advisory"  # Should be filtered out
                }
            ]
        }
        
        # Mock backtest with different FPR values
        backtest = {
            "rules": {
                "perfect_candidate": {"false_positive_rate": 0.001},
                "high_fpr_candidate": {"false_positive_rate": 0.01}
            }
        }
        
        # Step 1: Pick candidates
        candidates = pick_candidates(expansions, backtest, policy)
        self.assertEqual(len(candidates), 2)  # Advisory filtered out
        
        # Step 2: Enhance with governance metadata (simulate)
        for c in candidates:
            if c["decision"] == "ready-deploy":
                c.update({
                    "confidence_score": 0.85,
                    "risk_tier": "hunting", 
                    "severity_label": "Medium",
                    "rule_owner": "Sigma",
                    "detection_type": "hunting",
                    "sla": 48
                })
        
        # Step 3: Assign targets (governance gates)
        proposals = assign_targets(candidates, policy)
        
        # Perfect candidate should generate proposals
        perfect_proposals = [p for p in proposals if p["pattern"] == "perfect_candidate"]
        self.assertGreater(len(perfect_proposals), 0)
        
        # High FPR candidate should not generate proposals (ready-review decision)
        high_fpr_proposals = [p for p in proposals if p["pattern"] == "high_fpr_candidate"]
        self.assertEqual(len(high_fpr_proposals), 0)

if __name__ == '__main__':
    unittest.main()