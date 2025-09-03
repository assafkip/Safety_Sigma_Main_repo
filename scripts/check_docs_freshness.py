#!/usr/bin/env python3
"""
Safety Sigma docs freshness checker.

Validates that documentation stays synchronized with code changes:
- Golden test IDs (G-001, G-002, G-003, G-010) are referenced in docs
- IR invariants (C-001, C-002, C-003) are documented 
- EXEC_CHECKLIST.md exists and has required validation items

Exits 0 if all checks pass, non-zero with error details if validation fails.
"""
import re
import sys
from pathlib import Path
from typing import List, Tuple, Dict


def find_golden_test_ids() -> List[str]:
    """Find all golden test IDs (G-XXX) in test files."""
    golden_ids = set()
    
    test_dirs = [
        Path("tests/golden_cases"),
        Path("tests/unit")
    ]
    
    for test_dir in test_dirs:
        if not test_dir.exists():
            continue
            
        for test_file in test_dir.glob("*.py"):
            try:
                content = test_file.read_text(encoding='utf-8')
                # Find G-XXX patterns in comments and function names
                matches = re.findall(r'\bG-\d{3}\b', content)
                golden_ids.update(matches)
            except Exception as e:
                print(f"Warning: Could not read {test_file}: {e}")
    
    return sorted(golden_ids)


def find_ir_invariant_ids() -> List[str]:
    """Find all IR invariant IDs (C-XXX) in code and tests."""
    ir_ids = set()
    
    # Check IR implementation and tests
    ir_files = [
        Path("src/pdf_processor/ir.py"),
        Path("tests/unit/test_pdf_processor_ir.py")
    ]
    
    for ir_file in ir_files:
        if not ir_file.exists():
            continue
            
        try:
            content = ir_file.read_text(encoding='utf-8')
            # Find C-XXX patterns in comments and function names
            matches = re.findall(r'\bC-\d{3}\b', content)
            ir_ids.update(matches)
        except Exception as e:
            print(f"Warning: Could not read {ir_file}: {e}")
    
    return sorted(ir_ids)


def check_docs_references(doc_path: Path, required_ids: List[str]) -> Tuple[List[str], List[str]]:
    """Check if documentation references all required IDs."""
    if not doc_path.exists():
        return [], required_ids
    
    try:
        content = doc_path.read_text(encoding='utf-8')
        
        found_ids = []
        missing_ids = []
        
        for required_id in required_ids:
            if required_id in content:
                found_ids.append(required_id)
            else:
                missing_ids.append(required_id)
        
        return found_ids, missing_ids
        
    except Exception as e:
        print(f"Warning: Could not read {doc_path}: {e}")
        return [], required_ids


def check_exec_checklist() -> Tuple[bool, List[str]]:
    """Check EXEC_CHECKLIST.md exists and has required validation items."""
    checklist_path = Path("docs/EXEC_CHECKLIST.md")
    
    if not checklist_path.exists():
        return False, ["EXEC_CHECKLIST.md does not exist"]
    
    try:
        content = checklist_path.read_text(encoding='utf-8')
        
        required_sections = ["V-001", "V-002", "V-003", "V-004", "V-005"]
        required_elements = [
            "G-001", "G-002", "G-003", "G-010",  # Golden tests
            "C-001", "C-002", "C-003",           # IR invariants
            "pdf_processor/ingest.py",
            "pdf_processor/extract.py", 
            "pdf_processor/ir.py",
            "pdf_processor/audit.py",
            "scripts/run_rule.py"
        ]
        
        issues = []
        
        # Check validation sections
        for section in required_sections:
            if section not in content:
                issues.append(f"Missing validation section: {section}")
        
        # Check required elements
        for element in required_elements:
            if element not in content:
                issues.append(f"Missing required element: {element}")
        
        # Check for minimum number of checkboxes
        checkboxes = re.findall(r'- \[[xX ]\]', content)
        if len(checkboxes) < 30:
            issues.append(f"Expected at least 30 checklist items, found {len(checkboxes)}")
        
        return len(issues) == 0, issues
        
    except Exception as e:
        return False, [f"Could not read EXEC_CHECKLIST.md: {e}"]


def check_docs_freshness() -> int:
    """Main freshness checker function. Returns 0 if fresh, non-zero if stale."""
    print("=== Safety Sigma Docs Freshness Check ===")
    print()
    
    total_issues = 0
    
    # 1. Check golden test documentation sync
    print("1. Checking golden test ID documentation...")
    golden_ids = find_golden_test_ids()
    
    if golden_ids:
        print(f"   Found golden test IDs: {', '.join(golden_ids)}")
        
        # Check docs reference these IDs
        docs_to_check = [
            Path("docs/TESTING.md"),
            Path("docs/specs/pdf_processor_PRD_v0.1.md"),
            Path("Safety-Sigma-Docs/tests/golden_cases.md")
        ]
        
        for doc_path in docs_to_check:
            if doc_path.exists():
                found, missing = check_docs_references(doc_path, golden_ids)
                if missing:
                    print(f"   ❌ {doc_path}: Missing golden IDs {missing}")
                    total_issues += len(missing)
                else:
                    print(f"   ✅ {doc_path}: All golden IDs referenced")
    else:
        print("   ⚠️  No golden test IDs found in test files")
    
    print()
    
    # 2. Check IR invariant documentation sync  
    print("2. Checking IR invariant documentation...")
    ir_ids = find_ir_invariant_ids()
    
    if ir_ids:
        print(f"   Found IR invariant IDs: {', '.join(ir_ids)}")
        
        ir_docs = [
            Path("docs/IR_SCHEMA.md"),
            Path("Safety-Sigma-Docs/ir/schema.md")
        ]
        
        for doc_path in ir_docs:
            if doc_path.exists():
                found, missing = check_docs_references(doc_path, ir_ids)
                if missing:
                    print(f"   ❌ {doc_path}: Missing IR invariant IDs {missing}")
                    total_issues += len(missing)
                else:
                    print(f"   ✅ {doc_path}: All IR invariant IDs referenced")
    else:
        print("   ⚠️  No IR invariant IDs found in code files")
    
    print()
    
    # 3. Check execution checklist completeness
    print("3. Checking execution checklist...")
    checklist_ok, checklist_issues = check_exec_checklist()
    
    if checklist_ok:
        print("   ✅ EXEC_CHECKLIST.md: Complete and valid")
    else:
        print("   ❌ EXEC_CHECKLIST.md: Issues found:")
        for issue in checklist_issues:
            print(f"      - {issue}")
        total_issues += len(checklist_issues)
    
    print()
    
    # Summary
    if total_issues == 0:
        print("✅ DOCS FRESHNESS: All documentation is synchronized")
        return 0
    else:
        print(f"❌ DOCS FRESHNESS: {total_issues} synchronization issues found")
        print()
        print("Fix required:")
        print("- Update documentation files to reference missing IDs")
        print("- Ensure EXEC_CHECKLIST.md contains all validation requirements") 
        print("- Verify Safety-Sigma-Docs submodule is up to date")
        return 1


if __name__ == "__main__":
    exit_code = check_docs_freshness()
    sys.exit(exit_code)