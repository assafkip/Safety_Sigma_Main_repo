#!/usr/bin/env python3
"""Tests for v1.0 confidence scoring system."""

import unittest
from src.metrics.confidence import score_from_metrics, assign_risk_tier_from_confidence, batch_calculate_confidence
import json
import tempfile
from pathlib import Path

class TestConfidenceScoring(unittest.TestCase):
    """Test confidence scoring implementation."""
    
    def test_score_from_metrics_perfect_score(self):
        """Test confidence scoring with perfect metrics."""
        score = score_from_metrics(fp_rate=0.0, tp_rate=1.0, samples=100)
        self.assertEqual(score, 1.0)  # Perfect score: no FP, perfect TP, full samples
    
    def test_score_from_metrics_high_fpr_penalty(self):
        """Test that high FPR significantly reduces confidence."""
        score_high_fpr = score_from_metrics(fp_rate=0.5, tp_rate=1.0, samples=100)
        score_low_fpr = score_from_metrics(fp_rate=0.01, tp_rate=1.0, samples=100)
        self.assertLess(score_high_fpr, score_low_fpr)
        self.assertLess(score_high_fpr, 0.6)  # High FPR should significantly reduce confidence
    
    def test_score_from_metrics_sample_factor(self):
        """Test that sample size affects confidence appropriately."""
        score_few_samples = score_from_metrics(fp_rate=0.0, tp_rate=1.0, samples=10)
        score_many_samples = score_from_metrics(fp_rate=0.0, tp_rate=1.0, samples=100)
        self.assertLess(score_few_samples, score_many_samples)
    
    def test_score_from_metrics_edge_cases(self):
        """Test confidence scoring edge cases."""
        # Zero samples
        score = score_from_metrics(fp_rate=0.0, tp_rate=1.0, samples=0)
        self.assertEqual(score, 0.0)
        
        # Extreme FPR
        score = score_from_metrics(fp_rate=1.0, tp_rate=1.0, samples=100)
        self.assertLessEqual(score, 0.2)  # Should be very low due to 100% FPR
        
        # Zero TPR
        score = score_from_metrics(fp_rate=0.0, tp_rate=0.0, samples=100)
        self.assertEqual(score, 0.8)  # 80% base score for 0 FPR, 20% penalty for 0 TPR
    
    def test_assign_risk_tier_from_confidence(self):
        """Test risk tier assignment based on confidence scores."""
        # High confidence -> blocking tier possible
        tier = assign_risk_tier_from_confidence(0.95, 0.001)
        self.assertEqual(tier, "blocking")
        
        # Medium confidence -> hunting tier
        tier = assign_risk_tier_from_confidence(0.75, 0.01)  
        self.assertEqual(tier, "hunting")
        
        # Low confidence -> enrichment tier
        tier = assign_risk_tier_from_confidence(0.5, 0.05)
        self.assertEqual(tier, "enrichment")
        
        # Very low confidence -> no tier
        tier = assign_risk_tier_from_confidence(0.2, 0.2)
        self.assertIsNone(tier)
    
    def test_assign_risk_tier_fpr_thresholds(self):
        """Test that FPR thresholds are respected regardless of confidence."""
        # High confidence but high FPR -> lower tier
        tier = assign_risk_tier_from_confidence(0.95, 0.03)  # High conf but FPR > blocking threshold
        self.assertNotEqual(tier, "blocking")
        
        # Very high FPR -> enrichment at best
        tier = assign_risk_tier_from_confidence(0.95, 0.08)
        self.assertEqual(tier, "enrichment")
        
        # Extreme FPR -> no tier
        tier = assign_risk_tier_from_confidence(0.95, 0.15)
        self.assertIsNone(tier)
    
    def test_batch_calculate_confidence(self):
        """Test batch confidence calculation with mock data."""
        # Create mock backtest data
        backtest_data = {
            "rules": {
                "gift.*card": {
                    "false_positive_rate": 0.02,
                    "true_positive_rate": 0.8,
                    "samples_tested": 50
                },
                "crypto.*transfer": {
                    "false_positive_rate": 0.001,
                    "true_positive_rate": 0.95,
                    "samples_tested": 200
                }
            }
        }
        
        # Create mock expansions
        expansions = {
            "expansions": [
                {
                    "pattern": "gift.*card",
                    "operator": "match",
                    "status": "ready"
                },
                {
                    "pattern": "crypto.*transfer", 
                    "operator": "match",
                    "status": "ready"
                }
            ]
        }
        
        # Create temporary files
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as bt_file:
            json.dump(backtest_data, bt_file)
            bt_path = Path(bt_file.name)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as exp_file:
            json.dump(expansions, exp_file)
            exp_path = Path(exp_file.name)
        
        try:
            # Run batch calculation
            result_path = batch_calculate_confidence(bt_path, exp_path, Path("/tmp/test_result.json"))
            
            # Verify results
            self.assertTrue(result_path.exists())
            result_data = json.loads(result_path.read_text())
            
            self.assertIn("expansions", result_data)
            enhanced_expansions = result_data["expansions"]
            self.assertEqual(len(enhanced_expansions), 2)
            
            # Check that confidence scores were added
            for exp in enhanced_expansions:
                self.assertIn("confidence_score", exp)
                self.assertIn("risk_tier", exp)
                self.assertIsInstance(exp["confidence_score"], float)
                self.assertIn(exp["risk_tier"], ["blocking", "hunting", "enrichment"])
        
        finally:
            # Cleanup
            bt_path.unlink()
            exp_path.unlink()
            if result_path.exists():
                result_path.unlink()

if __name__ == '__main__':
    unittest.main()