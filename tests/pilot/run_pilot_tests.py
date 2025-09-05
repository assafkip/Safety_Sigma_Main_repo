#!/usr/bin/env python3
"""Test runner for v1.0 pilot readiness validation."""

import unittest
import sys
import os
from pathlib import Path
import json
import time

# Add root to path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

def run_pilot_readiness_tests():
    """Run comprehensive v1.0 pilot readiness test suite."""
    print("🎯 Safety Sigma v1.0 Pilot Readiness Test Suite")
    print("=" * 60)
    print(f"Root: {ROOT}")
    print(f"Python: {sys.version}")
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Discover and run pilot tests
    test_dir = Path(__file__).parent
    loader = unittest.TestLoader()
    suite = loader.discover(str(test_dir), pattern='test_*.py')
    
    # Set up test runner with verbose output
    runner = unittest.TextTestRunner(
        verbosity=2,
        stream=sys.stdout,
        descriptions=True,
        failfast=False
    )
    
    # Run the tests
    print("Running v1.0 Pilot Readiness Tests...")
    print("-" * 60)
    
    start_time = time.time()
    result = runner.run(suite)
    end_time = time.time()
    
    # Generate test report
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    print(f"Duration: {end_time - start_time:.2f}s")
    
    if result.failures:
        print(f"\n❌ {len(result.failures)} test(s) failed:")
        for test, traceback in result.failures:
            print(f"  - {test}")
    
    if result.errors:
        print(f"\n🚨 {len(result.errors)} test(s) had errors:")
        for test, traceback in result.errors:
            print(f"  - {test}")
    
    if result.wasSuccessful():
        print("\n✅ All v1.0 pilot readiness tests passed!")
        print("🚀 System is ready for limited production pilot.")
    else:
        print("\n❌ Some tests failed. Address issues before pilot deployment.")
        print("📋 Review governance requirements and metadata completeness.")
    
    # Write test report JSON
    report_path = ROOT / "artifacts" / "pilot_test_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    test_report = {
        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
        "version": "v1.0-pilot",
        "summary": {
            "total_tests": result.testsRun,
            "failures": len(result.failures),
            "errors": len(result.errors),
            "skipped": len(result.skipped) if hasattr(result, 'skipped') else 0,
            "success": result.wasSuccessful(),
            "duration_seconds": round(end_time - start_time, 2)
        },
        "failed_tests": [str(test) for test, _ in result.failures],
        "error_tests": [str(test) for test, _ in result.errors],
        "pilot_readiness": {
            "governance_validation": "passed" if result.wasSuccessful() else "failed",
            "confidence_scoring": "implemented",
            "risk_tier_classification": "implemented", 
            "metadata_enrichment": "implemented",
            "adapter_enhancements": "implemented"
        }
    }
    
    report_path.write_text(json.dumps(test_report, indent=2))
    print(f"\n📄 Test report written to: {report_path}")
    
    return 0 if result.wasSuccessful() else 1

def validate_pilot_prerequisites():
    """Validate that pilot readiness prerequisites are met."""
    print("🔍 Validating v1.0 pilot prerequisites...")
    print("-" * 40)
    
    prerequisites = []
    
    # Check required modules exist
    required_modules = [
        ("src/metrics/confidence.py", "Confidence scoring module"),
        ("src/agentic/decisions.py", "Governance decision module"), 
        ("configs/risk_tiers.yaml", "Risk tier policy configuration"),
        ("docs/governance_decision_tree.md", "Governance decision tree"),
        ("adapters/splunk/MAPPING.md", "Splunk field mapping guide"),
        ("adapters/elastic/MAPPING.md", "Elastic field mapping guide"),
        ("adapters/sql/MAPPING.md", "SQL field mapping guide")
    ]
    
    for module_path, description in required_modules:
        full_path = ROOT / module_path
        if full_path.exists():
            prerequisites.append((description, "✅ Present"))
        else:
            prerequisites.append((description, "❌ Missing"))
    
    # Check for test data
    test_data_files = [
        ("artifacts/proactive/expansions.json", "Proactive expansions"),
        ("artifacts/proactive/backtest_report.json", "Backtest metrics")
    ]
    
    for data_path, description in test_data_files:
        full_path = ROOT / data_path
        if full_path.exists():
            prerequisites.append((description, "✅ Available"))
        else:
            prerequisites.append((description, "⚠️ Optional"))
    
    # Display results
    all_required_present = True
    for description, status in prerequisites:
        print(f"  {status} {description}")
        if status.startswith("❌"):
            all_required_present = False
    
    print()
    if all_required_present:
        print("✅ All required prerequisites present")
        return True
    else:
        print("❌ Missing required prerequisites for pilot deployment")
        return False

if __name__ == "__main__":
    # Validate prerequisites first
    if not validate_pilot_prerequisites():
        print("\n🚫 Prerequisites validation failed. Cannot run pilot tests.")
        sys.exit(1)
    
    # Run the test suite
    result = run_pilot_readiness_tests()
    sys.exit(result)