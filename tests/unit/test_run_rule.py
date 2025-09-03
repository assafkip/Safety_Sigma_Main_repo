"""
Test for V-004 compliance: Rule execution harness functionality.

Tests that scripts/run_rule.py loads IR samples, generates rules, and executes successfully.
"""
import subprocess
import sys
from pathlib import Path


def test_run_rule_script_executes():
    """Test V-004: Rule execution script runs successfully with exit code 0."""
    
    # Path to the rule execution script
    script_path = Path(__file__).parent.parent.parent / "scripts" / "run_rule.py"
    
    # Verify script exists
    assert script_path.exists(), f"Rule execution script not found: {script_path}"
    
    # Run the script using subprocess
    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        cwd=script_path.parent.parent  # Run from repo root
    )
    
    # V-004 requirement: exit non-zero if no match or runtime error
    assert result.returncode == 0, f"V-004 failure: Script exited with code {result.returncode}. Stderr: {result.stderr}"
    
    # Verify expected output content
    output = result.stdout
    assert "V-004 COMPLIANCE" in output, "Missing V-004 compliance marker"
    assert "Rule execution completed successfully" in output, "Missing success message"
    assert "Loaded IR sample" in output, "Missing IR loading message"
    assert "Generated" in output and "rules from IR objects" in output, "Missing rule generation"
    assert "Compiled" in output and "rules successfully" in output, "Missing rule compilation"
    assert "SUCCESS:" in output, "Missing match success indicator"
    
    # Verify no errors
    assert "ERROR:" not in output, f"Script reported errors: {output}"


def test_run_rule_matches_golden_indicators():
    """Test V-004: Rule execution finds golden test indicators."""
    
    script_path = Path(__file__).parent.parent.parent / "scripts" / "run_rule.py"
    
    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        cwd=script_path.parent.parent
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    
    output = result.stdout
    
    # Verify golden test indicators are matched
    assert "$1,998.88" in output, "Must match golden test amount"
    assert "wa.me/123456789" in output, "Must match golden test link" 
    assert "finance" in output, "Must match golden test category"
    
    # Verify matches were found
    assert "MATCHED:" in output, "Must show rule matches"
    assert "3/3 rules matched" in output or "rules matched" in output, "Must show match statistics"


def test_run_rule_ir_integration():
    """Test V-004: Rule execution integrates with IR objects correctly."""
    
    script_path = Path(__file__).parent.parent.parent / "scripts" / "run_rule.py"
    
    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        cwd=script_path.parent.parent
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    
    output = result.stdout
    
    # Verify IR-to-rule pipeline works
    assert "Loaded IR sample with 3 objects" in output, "Must load IR sample"
    assert "Generated 3 rules from IR objects" in output, "Must generate rules from IR"
    assert "Compiled 3 IR-derived rules successfully" in output, "Must compile IR-derived rules"
    
    # Verify different IR types are handled
    assert "amount_match_" in output, "Must generate amount rules from IR"
    assert "link_match_" in output, "Must generate link rules from IR"
    assert "category_match_" in output, "Must generate category rules from IR"


if __name__ == "__main__":
    test_run_rule_script_executes()
    test_run_rule_matches_golden_indicators() 
    test_run_rule_ir_integration()
    print("All run_rule tests passed!")