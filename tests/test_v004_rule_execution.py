"""
Test for V-004 compliance: Rule execution script functionality.

Verifies that scripts/run_rule.py loads and executes regex rules correctly.
"""
import subprocess
import sys
from pathlib import Path
import pytest


def test_v004_rule_execution_script():
    """Test V-004: Rule execution script runs successfully."""
    # Path to the rule execution script
    script_path = Path(__file__).parent.parent / "scripts" / "run_rule.py"
    
    # Verify script exists
    assert script_path.exists(), f"Rule execution script not found: {script_path}"
    
    # Run the script
    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        cwd=script_path.parent.parent  # Run from repo root
    )
    
    # Verify successful execution
    assert result.returncode == 0, f"Script failed with code {result.returncode}. Stderr: {result.stderr}"
    
    # Verify expected output content
    output = result.stdout
    assert "V-004 COMPLIANCE" in output, "Missing V-004 compliance marker"
    assert "Rule execution completed successfully" in output, "Missing success message"
    assert "Compiled 2 regex rules successfully" in output, "Missing rule compilation message"
    
    # Verify rule matching results
    assert "MATCH amount_detection" in output, "Amount detection rule not triggered"
    assert "MATCH phone_detection" in output, "Phone detection rule not triggered"
    assert "$1,998.88" in output, "Golden test amount not extracted"
    assert "555-123-4567" in output, "Phone number not extracted"


def test_v004_rule_compilation():
    """Test V-004: Rule compilation works correctly."""
    # Import and test the rule compilation directly
    sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
    
    from scripts.run_rule import create_sample_regex_rule, compile_regex_rules
    
    # Create sample rule configuration
    rules_config = create_sample_regex_rule()
    
    # Verify rule configuration structure
    assert "rules" in rules_config
    assert len(rules_config["rules"]) == 2
    
    # Compile rules
    compiled_rules = compile_regex_rules(rules_config)
    
    # Verify compilation results
    assert len(compiled_rules) == 2
    
    # Test first rule (amount detection)
    amount_rule = compiled_rules[0]
    assert amount_rule.name == "amount_detection"
    assert amount_rule.priority == 1
    assert "pattern" in amount_rule.metadata
    
    # Test rule predicate functionality
    assert amount_rule.predicate("Payment: $100.00") == True, "Amount rule should match"
    assert amount_rule.predicate("No money here") == False, "Amount rule should not match"
    
    # Test second rule (phone detection)
    phone_rule = compiled_rules[1]
    assert phone_rule.name == "phone_detection"
    assert phone_rule.priority == 2
    
    assert phone_rule.predicate("Call 555-123-4567") == True, "Phone rule should match"
    assert phone_rule.predicate("No phone here") == False, "Phone rule should not match"


def test_v004_rule_extraction():
    """Test V-004: Rule extraction returns proper results."""
    sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
    
    from scripts.run_rule import compile_regex_rules, execute_rules_on_text, create_sample_regex_rule
    
    # Setup
    rules_config = create_sample_regex_rule()
    compiled_rules = compile_regex_rules(rules_config)
    
    # Test extraction on golden test data
    test_text = "Payment amount: $1,998.88 for services"
    results = execute_rules_on_text(compiled_rules, test_text)
    
    # Verify results structure
    assert "matches" in results
    assert "rules_matched" in results
    assert "total_rules" in results
    assert results["total_rules"] == 2
    assert results["rules_matched"] == 1
    
    # Verify match details
    match = results["matches"][0]
    assert match["rule_name"] == "amount_detection"
    assert "extracted_values" in match
    assert match["extracted_values"] == ["$1,998.88"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])