"""
Test for V-005 compliance: Execution checklist validation.

Fails if any checkbox in docs/EXEC_CHECKLIST.md is unchecked, ensuring all
V-001..V-005 validation requirements are met before deployment.
"""
import re
from pathlib import Path


def test_v005_exec_checklist_all_boxes_checked():
    """
    Test V-005: All boxes in execution checklist must be checked.
    
    This test fails on PRs to main if any validation requirement is unchecked,
    enforcing contract-ready status per V-005.
    """
    # Path to execution checklist
    checklist_path = Path(__file__).parent.parent.parent / "docs" / "EXEC_CHECKLIST.md"
    
    # Verify checklist exists
    assert checklist_path.exists(), f"Execution checklist not found: {checklist_path}"
    
    # Read checklist content
    with open(checklist_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all checkboxes
    unchecked_boxes = re.findall(r'- \[ \].*', content)  # Unchecked: - [ ]
    checked_boxes_x = re.findall(r'- \[x\].*', content)  # Checked: - [x]
    checked_boxes_X = re.findall(r'- \[X\].*', content)  # Checked: - [X]
    
    total_checked = len(checked_boxes_x) + len(checked_boxes_X)
    total_unchecked = len(unchecked_boxes)
    total_boxes = total_checked + total_unchecked
    
    # Report findings
    print(f"\nV-005 Execution Checklist Validation:")
    print(f"  Total checkboxes: {total_boxes}")
    print(f"  Checked: {total_checked}")
    print(f"  Unchecked: {total_unchecked}")
    
    # Verify minimum expected V-001..V-005 items
    assert total_boxes >= 30, f"Expected at least 30 checklist items for V-001..V-005, found {total_boxes}"
    
    # Check for required validation sections
    required_sections = ["V-001", "V-002", "V-003", "V-004", "V-005"]
    for section in required_sections:
        assert section in content, f"Missing required section: {section}"
    
    # V-005 GATE: Fail if any boxes are unchecked
    if total_unchecked > 0:
        print(f"\nV-005 COMPLIANCE VIOLATION: {total_unchecked} unchecked items found:")
        for i, item in enumerate(unchecked_boxes, 1):
            print(f"  {i}. {item.strip()}")
        
        # FAIL THE TEST - this enforces V-005 gate
        assert False, (
            f"V-005 GATE FAILURE: {total_unchecked} validation requirements unchecked. "
            f"All {total_boxes} items must be verified before deployment. "
            f"This test fails on PRs to main until all compliance boxes are checked."
        )
    
    # SUCCESS: All validation requirements completed
    print(f"\n✓ V-005 COMPLIANCE: All {total_boxes} validation requirements verified")
    print("✓ Contract-ready: Repository meets all binding requirements V-001..V-005")


def test_v005_required_validation_content():
    """Test V-005: Checklist contains all required validation content."""
    checklist_path = Path(__file__).parent.parent.parent / "docs" / "EXEC_CHECKLIST.md"
    
    with open(checklist_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Required validation elements for contract compliance
    required_elements = [
        # Golden test references
        "G-001", "G-002", "G-003", "G-010",
        
        # IR compliance requirements
        "C-001", "C-002", "C-003", 
        "verbatim", "normalization", "span_ids",
        
        # Key file paths
        "src/pdf_processor/ingest.py", "src/pdf_processor/extract.py",
        "src/pdf_processor/ir.py", "src/pdf_processor/audit.py", 
        "scripts/run_rule.py",
        
        # Test files
        "tests/unit/test_pdf_processor_ir.py", "tests/unit/test_run_rule.py",
        
        # Core concepts
        "provenance", "page/character offsets", "append-only",
        "module_version", "doc_id", "spans", "decisions", "validation_scores",
        
        # Compliance gates
        "V-001", "V-002", "V-003", "V-004", "V-005"
    ]
    
    missing_elements = []
    for element in required_elements:
        if element not in content:
            missing_elements.append(element)
    
    if missing_elements:
        assert False, (
            f"V-005 validation: Checklist missing required elements: {missing_elements}. "
            f"All validation requirements must be documented for contract compliance."
        )


def test_v005_specific_gate_items():
    """Test V-005: Specific gate items are present and checked."""
    checklist_path = Path(__file__).parent.parent.parent / "docs" / "EXEC_CHECKLIST.md"
    
    with open(checklist_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Key gate requirements that must be checked
    gate_requirements = [
        "Golden tests G-001.*G-002.*G-003.*pass",
        "Golden test G-010.*pass",
        "C-001.*preserve verbatim",
        "C-002.*literal.*NO normalization",
        "C-003.*explicit span_ids",
        "module_version.*doc_id.*spans.*decisions.*validation_scores",
        "scripts/run_rule.py.*loads.*executes",
        "V-004 compliance"
    ]
    
    for requirement in gate_requirements:
        if not re.search(requirement, content, re.IGNORECASE):
            assert False, f"V-005: Missing gate requirement pattern: {requirement}"
    
    # Verify these are checked, not unchecked
    critical_unchecked = []
    for requirement in gate_requirements:
        # Look for this requirement in an unchecked line
        unchecked_lines = re.findall(r'- \[ \].*', content)
        for line in unchecked_lines:
            if re.search(requirement, line, re.IGNORECASE):
                critical_unchecked.append(line.strip())
    
    if critical_unchecked:
        assert False, (
            f"V-005: Critical gate requirements are unchecked: {critical_unchecked}. "
            f"These must be verified for contract compliance."
        )


if __name__ == "__main__":
    test_v005_exec_checklist_all_boxes_checked()
    test_v005_required_validation_content()
    test_v005_specific_gate_items()
    print("All V-005 exec checklist tests passed!")