"""
Test for EXEC_CHECKLIST.md validation.

Fails if any checkbox in the execution checklist is unchecked,
ensuring all V-001..V-005 compliance requirements are verified before deployment.
"""
import re
from pathlib import Path
import pytest


def test_exec_checklist_all_boxes_checked():
    """
    Test that all boxes in docs/EXEC_CHECKLIST.md are checked.
    
    This test enforces that all V-001..V-005 validation requirements
    are completed before deployment by failing if any checkbox is unchecked.
    """
    # Path to the execution checklist
    checklist_path = Path(__file__).parent.parent / "docs" / "EXEC_CHECKLIST.md"
    
    # Verify checklist exists
    assert checklist_path.exists(), f"Execution checklist not found: {checklist_path}"
    
    # Read checklist content
    with open(checklist_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all checkbox patterns
    checkbox_patterns = [
        r'- \[ \]',  # Unchecked box: - [ ]
        r'- \[x\]',  # Checked box: - [x]  
        r'- \[X\]'   # Checked box: - [X]
    ]
    
    unchecked_boxes = re.findall(r'- \[ \].*', content)
    checked_boxes_x = re.findall(r'- \[x\].*', content)  
    checked_boxes_X = re.findall(r'- \[X\].*', content)
    
    total_checked = len(checked_boxes_x) + len(checked_boxes_X)
    total_unchecked = len(unchecked_boxes)
    total_boxes = total_checked + total_unchecked
    
    # Report findings
    print(f"\nExecution Checklist Validation:")
    print(f"  Total checkboxes: {total_boxes}")
    print(f"  Checked: {total_checked}")
    print(f"  Unchecked: {total_unchecked}")
    
    if unchecked_boxes:
        print(f"\nUnchecked items (compliance violations):")
        for i, item in enumerate(unchecked_boxes, 1):
            print(f"  {i}. {item.strip()}")
    
    # Verify minimum expected items are present
    assert total_boxes >= 20, f"Expected at least 20 checklist items, found {total_boxes}"
    
    # Check for key validation sections
    assert "V-001" in content, "Missing V-001 validation section"
    assert "V-002" in content, "Missing V-002 validation section"  
    assert "V-003" in content, "Missing V-003 validation section"
    assert "V-004" in content, "Missing V-004 validation section"
    assert "V-005" in content, "Missing V-005 validation section"
    
    # FAIL if any boxes are unchecked
    if total_unchecked > 0:
        pytest.fail(
            f"COMPLIANCE VIOLATION: {total_unchecked} unchecked items in execution checklist. "
            f"All {total_boxes} validation requirements must be completed before deployment. "
            f"Unchecked items represent unresolved compliance violations."
        )
    
    # SUCCESS: All boxes are checked
    print(f"\n✓ SUCCESS: All {total_boxes} checklist items verified - system ready for deployment")


def test_exec_checklist_contains_key_requirements():
    """Test that checklist contains all key validation requirements."""
    checklist_path = Path(__file__).parent.parent / "docs" / "EXEC_CHECKLIST.md"
    
    with open(checklist_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Required compliance elements
    required_elements = [
        # Golden tests
        "G-001", "G-002", "G-003", "G-010",
        
        # IR compliance
        "C-001", "C-002", "C-003",
        
        # File requirements  
        "pdf_to_text_with_offsets", "to_ir_objects", "append_jsonl", "run_rule.py",
        
        # Module paths
        "src/pdf_processor/ingest.py", "src/pdf_processor/extract.py", 
        "src/pdf_processor/ir.py", "src/pdf_processor/audit.py",
        "scripts/run_rule.py", "tests/unit/test_pdf_processor_ir.py",
        
        # Key concepts
        "provenance", "verbatim", "normalization", "audit", "regex",
        "module_version", "doc_id", "spans", "decisions", "validation_scores"
    ]
    
    missing_elements = []
    for element in required_elements:
        if element not in content:
            missing_elements.append(element)
    
    if missing_elements:
        pytest.fail(
            f"Execution checklist missing required elements: {missing_elements}. "
            f"Checklist must include all key validation requirements."
        )


def test_exec_checklist_structure_valid():
    """Test that checklist has proper markdown structure."""
    checklist_path = Path(__file__).parent.parent / "docs" / "EXEC_CHECKLIST.md"
    
    with open(checklist_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Must have proper markdown structure
    assert content.startswith("#"), "Checklist must start with markdown header"
    assert "V-001" in content, "Must include V-001 section"
    assert "V-002" in content, "Must include V-002 section" 
    assert "V-003" in content, "Must include V-003 section"
    assert "V-004" in content, "Must include V-004 section"
    assert "V-005" in content, "Must include V-005 section"
    
    # Must have deployment sign-off section
    assert "Deployment Sign-off" in content, "Must include deployment sign-off section"
    
    # Must have note about compliance violations
    assert "compliance violations" in content.lower(), "Must mention compliance violations"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])