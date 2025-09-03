"""
Test for audit logging V-003 compliance.

Tests append-only audit logging with required fields:
module_version, doc_id, spans, decisions, validation_scores, timestamp
"""
import os
import json
import tempfile
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from pdf_processor.audit import append_jsonl


def test_audit_log_append_only():
    """Test that audit log is append-only with required V-003 fields."""
    
    # Create temporary log file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as tmp:
        log_path = tmp.name
    
    try:
        # First record
        record1 = {
            'action': 'pdf_extraction',
            'module_version': 'pdf_processor_v1.0.0',
            'doc_id': 'test_doc_001', 
            'spans': [
                {'text': '$1,998.88', 'start': 16, 'end': 25, 'page': 1},
                {'text': 'VOID 2000', 'start': 32, 'end': 41, 'page': 1}
            ],
            'decisions': [
                {
                    'decision_point': 'amount_extraction', 
                    'reasoning': 'Found currency pattern $X,XXX.XX',
                    'outcome': 'extracted'
                },
                {
                    'decision_point': 'memo_extraction',
                    'reasoning': 'Found VOID pattern in memo field', 
                    'outcome': 'extracted'
                }
            ],
            'validation_scores': {
                'amount_confidence': 0.95,
                'memo_confidence': 0.88,
                'overall_quality': 0.91
            }
        }
        
        # Append first record
        append_jsonl(record1, log_path)
        
        # Verify first record was written
        with open(log_path, 'r') as f:
            lines = f.readlines()
        
        assert len(lines) == 1, "First record should create one line"
        
        first_record = json.loads(lines[0])
        assert first_record['module_version'] == 'pdf_processor_v1.0.0'
        assert first_record['doc_id'] == 'test_doc_001'
        assert len(first_record['spans']) == 2
        assert len(first_record['decisions']) == 2
        assert 'timestamp' in first_record
        
        # Second record
        record2 = {
            'action': 'link_extraction',
            'module_version': 'pdf_processor_v1.0.0',
            'doc_id': 'test_doc_002',
            'spans': [
                {'text': 'wa.me/123456789', 'start': 9, 'end': 24, 'page': 1}
            ],
            'decisions': [
                {
                    'decision_point': 'link_extraction',
                    'reasoning': 'Found wa.me pattern matching regex',
                    'outcome': 'extracted'
                }
            ],
            'validation_scores': {
                'link_confidence': 0.99,
                'pattern_match_quality': 1.0
            }
        }
        
        # Append second record
        append_jsonl(record2, log_path)
        
        # Verify both records exist (append-only)
        with open(log_path, 'r') as f:
            lines = f.readlines()
        
        assert len(lines) == 2, "Second record should append, creating two lines total"
        
        # Verify first record unchanged
        first_record_check = json.loads(lines[0])
        assert first_record_check['doc_id'] == 'test_doc_001'
        
        # Verify second record appended
        second_record = json.loads(lines[1])
        assert second_record['doc_id'] == 'test_doc_002'
        assert second_record['spans'][0]['text'] == 'wa.me/123456789'
        
    finally:
        # Cleanup
        if os.path.exists(log_path):
            os.unlink(log_path)


def test_audit_log_required_keys():
    """Test that audit log requires all V-003 keys."""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as tmp:
        log_path = tmp.name
    
    try:
        # Test missing module_version
        invalid_record = {
            'action': 'test',
            'doc_id': 'test',
            'spans': [{'text': 'test', 'start': 0, 'end': 4, 'page': 1}],
            'decisions': [{'decision_point': 'test', 'reasoning': 'test', 'outcome': 'test'}],
            'validation_scores': {'confidence': 0.95}
        }
        
        try:
            append_jsonl(invalid_record, log_path)
            assert False, "Should have raised ValueError for missing module_version"
        except ValueError as e:
            assert "module_version" in str(e), f"Error should mention module_version: {e}"
        
        # Test missing doc_id
        invalid_record = {
            'action': 'test',
            'module_version': 'v1.0.0',
            'spans': [{'text': 'test', 'start': 0, 'end': 4, 'page': 1}],
            'decisions': [{'decision_point': 'test', 'reasoning': 'test', 'outcome': 'test'}],
            'validation_scores': {'confidence': 0.95}
        }
        
        try:
            append_jsonl(invalid_record, log_path)
            assert False, "Should have raised ValueError for missing doc_id"
        except ValueError as e:
            assert "doc_id" in str(e), f"Error should mention doc_id: {e}"
        
        # Test missing spans
        invalid_record = {
            'action': 'test',
            'module_version': 'v1.0.0',
            'doc_id': 'test',
            'decisions': [{'decision_point': 'test', 'reasoning': 'test', 'outcome': 'test'}],
            'validation_scores': {'confidence': 0.95}
        }
        
        try:
            append_jsonl(invalid_record, log_path)
            assert False, "Should have raised ValueError for missing spans"
        except ValueError as e:
            assert "spans" in str(e), f"Error should mention spans: {e}"
            
    finally:
        if os.path.exists(log_path):
            os.unlink(log_path)


def test_audit_log_span_validation():
    """Test that spans are validated for required provenance fields."""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as tmp:
        log_path = tmp.name
    
    try:
        # Test span missing 'text' field
        invalid_record = {
            'action': 'test',
            'module_version': 'v1.0.0',
            'doc_id': 'test',
            'spans': [{'start': 0, 'end': 4, 'page': 1}],  # Missing 'text'
            'decisions': [{'decision_point': 'test', 'reasoning': 'test', 'outcome': 'test'}],
            'validation_scores': {'confidence': 0.95}
        }
        
        try:
            append_jsonl(invalid_record, log_path)
            assert False, "Should have raised ValueError for span missing text"
        except ValueError as e:
            assert "text" in str(e), f"Error should mention missing text: {e}"
        
        # Test span missing page field  
        invalid_record = {
            'action': 'test',
            'module_version': 'v1.0.0',
            'doc_id': 'test',
            'spans': [{'text': 'test', 'start': 0, 'end': 4}],  # Missing 'page'
            'decisions': [{'decision_point': 'test', 'reasoning': 'test', 'outcome': 'test'}],
            'validation_scores': {'confidence': 0.95}
        }
        
        try:
            append_jsonl(invalid_record, log_path)
            assert False, "Should have raised ValueError for span missing page"
        except ValueError as e:
            assert "page" in str(e), f"Error should mention missing page: {e}"
            
    finally:
        if os.path.exists(log_path):
            os.unlink(log_path)


def test_audit_log_decision_validation():
    """Test that decisions are validated for required fields."""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as tmp:
        log_path = tmp.name
    
    try:
        # Test decision missing 'reasoning' field
        invalid_record = {
            'action': 'test',
            'module_version': 'v1.0.0', 
            'doc_id': 'test',
            'spans': [{'text': 'test', 'start': 0, 'end': 4, 'page': 1}],
            'decisions': [{'decision_point': 'test', 'outcome': 'test'}],  # Missing 'reasoning'
            'validation_scores': {'confidence': 0.95}
        }
        
        try:
            append_jsonl(invalid_record, log_path)
            assert False, "Should have raised ValueError for decision missing reasoning"
        except ValueError as e:
            assert "reasoning" in str(e), f"Error should mention missing reasoning: {e}"
            
    finally:
        if os.path.exists(log_path):
            os.unlink(log_path)


if __name__ == "__main__":
    test_audit_log_append_only()
    test_audit_log_required_keys() 
    test_audit_log_span_validation()
    test_audit_log_decision_validation()
    print("All audit logging tests passed!")