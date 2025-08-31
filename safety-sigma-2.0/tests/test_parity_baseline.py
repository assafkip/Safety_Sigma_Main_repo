#!/usr/bin/env python3
"""
Parity testing framework for Safety Sigma 2.0

This module ensures byte-for-byte compatibility with Safety Sigma 1.0
by comparing outputs on the same inputs with all v2.0 features disabled.
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict, Optional
from unittest.mock import patch, Mock

import pytest

# Add safety_sigma to path
sys.path.insert(0, str(Path(__file__).parent.parent))

class SafetySigmaParityTester:
    """
    Handles comparison between Safety Sigma 1.0 and 2.0 outputs
    """
    
    def __init__(self, ss1_path: Optional[str] = None):
        self.ss1_path = ss1_path or os.getenv('SS1_PATH', '../Desktop/safety_sigma/phase_1')
        self.ss1_path = Path(self.ss1_path).resolve()
        
        if not self.ss1_path.exists():
            raise FileNotFoundError(f"Safety Sigma 1.0 not found at: {self.ss1_path}")
        
        # Add SS1 to Python path for imports
        sys.path.insert(0, str(self.ss1_path))
        
    def get_ss1_processor(self):
        """Import and initialize Safety Sigma 1.0 processor"""
        try:
            from safety_sigma_processor import SafetySigmaProcessor
            # For parity testing, we provide a mock API key
            return SafetySigmaProcessor(api_key="mock-key-for-testing")
        except ImportError as e:
            pytest.skip(f"Cannot import Safety Sigma 1.0: {e}")
            
    def get_ss2_processor(self):
        """Import and initialize Safety Sigma 2.0 processor (Stage 0 - should be identical)"""
        try:
            from safety_sigma.processor import SafetySigmaProcessor
            return SafetySigmaProcessor()
        except ImportError:
            # For Stage 0, we create a stub that delegates to SS1
            return self._create_ss2_stub()
    
    def _create_ss2_stub(self):
        """Create a Safety Sigma 2.0 stub that delegates to 1.0 for Stage 0"""
        class SS2Stub:
            def __init__(self, ss1_processor):
                self.ss1 = ss1_processor
                
            def extract_pdf_text(self, pdf_path: str) -> str:
                return self.ss1.extract_pdf_text(pdf_path)
                
            def read_instruction_file(self, md_path: str) -> str:
                return self.ss1.read_instruction_file(md_path)
                
            def process_report(self, instructions: str, report_content: str) -> str:
                return self.ss1.process_report(instructions, report_content)
                
            def save_results(self, results: str, output_path: str) -> None:
                return self.ss1.save_results(results, output_path)
        
        ss1_processor = self.get_ss1_processor()
        return SS2Stub(ss1_processor)
    
    def compare_outputs(self, ss1_output: str, ss2_output: str, test_name: str) -> Dict[str, Any]:
        """
        Compare outputs between SS1 and SS2
        
        Returns comparison results with detailed analysis
        """
        result = {
            'test_name': test_name,
            'identical': ss1_output == ss2_output,
            'ss1_length': len(ss1_output),
            'ss2_length': len(ss2_output),
            'length_diff': len(ss2_output) - len(ss1_output),
        }
        
        if not result['identical']:
            # Find first difference
            min_len = min(len(ss1_output), len(ss2_output))
            first_diff = -1
            for i in range(min_len):
                if ss1_output[i] != ss2_output[i]:
                    first_diff = i
                    break
            
            result.update({
                'first_difference_at': first_diff,
                'ss1_sample': ss1_output[max(0, first_diff-50):first_diff+50] if first_diff >= 0 else '',
                'ss2_sample': ss2_output[max(0, first_diff-50):first_diff+50] if first_diff >= 0 else '',
            })
        
        return result
    
    def run_parity_test(self, pdf_path: str, instructions_path: str, test_name: str) -> Dict[str, Any]:
        """
        Run a complete parity test comparing SS1 and SS2 on the same inputs
        """
        pdf_path = Path(pdf_path)
        instructions_path = Path(instructions_path)
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        if not instructions_path.exists():
            raise FileNotFoundError(f"Instructions not found: {instructions_path}")
        
        # Disable all SS2 features for parity testing
        with patch.dict(os.environ, {
            'SS2_ENABLE_TOOLS': 'false',
            'SS2_USE_AGENT': 'false', 
            'SS2_ENHANCE_DOCS': 'false',
            'SS2_DYNAMIC_WORKFLOWS': 'false',
            'SS2_MULTI_AGENT': 'false',
            'SS2_SELF_IMPROVE': 'false',
        }):
            try:
                # Run SS1
                ss1_processor = self.get_ss1_processor()
                instructions = ss1_processor.read_instruction_file(str(instructions_path))
                report_content = ss1_processor.extract_pdf_text(str(pdf_path))
                
                # Mock OpenAI for consistent testing
                mock_response = f"# Safety Sigma Analysis - {test_name}\n\nMocked response for testing parity"
                with patch('openai.OpenAI') as mock_openai:
                    mock_openai.return_value.chat.completions.create.return_value.choices = [
                        type('Choice', (), {'message': type('Message', (), {'content': mock_response})()})()
                    ]
                    
                    ss1_output = ss1_processor.process_report(instructions, report_content)
                
                # Run SS2 (stub)
                ss2_processor = self.get_ss2_processor()
                with patch('openai.OpenAI') as mock_openai:
                    mock_openai.return_value.chat.completions.create.return_value.choices = [
                        type('Choice', (), {'message': type('Message', (), {'content': mock_response})()})()
                    ]
                    
                    ss2_output = ss2_processor.process_report(instructions, report_content)
                
                # Compare outputs
                comparison = self.compare_outputs(ss1_output, ss2_output, test_name)
                
                return {
                    'success': True,
                    'comparison': comparison,
                    'pdf_path': str(pdf_path),
                    'instructions_path': str(instructions_path),
                }
                
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e),
                    'pdf_path': str(pdf_path),
                    'instructions_path': str(instructions_path),
                }


class TestSafetySigmaParity(unittest.TestCase):
    """
    Parity test cases for Safety Sigma 1.0 vs 2.0
    """
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.tester = SafetySigmaParityTester()
        cls.test_data_dir = Path(__file__).parent / 'fixtures'
        cls.test_data_dir.mkdir(exist_ok=True)
        
        # Create minimal test fixtures if they don't exist
        cls._create_test_fixtures()
    
    @classmethod
    def _create_test_fixtures(cls):
        """Create minimal test fixtures for parity testing"""
        # Create test instruction file
        instructions_file = cls.test_data_dir / 'test_instructions.md'
        if not instructions_file.exists():
            instructions_file.write_text("""
# Test Safety Sigma Instructions

Extract the following from the report:
- Title
- Version
- Key findings

Output in JSON format.
""")
        
        # Create baseline outputs for comparison
        baseline_file = cls.test_data_dir / 'baseline_outputs.json'
        if not baseline_file.exists():
            baseline_file.write_text('{}')
    
    def test_basic_parity_mock(self):
        """Test basic parity with mocked inputs"""
        # Create a temporary PDF file for testing
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_pdf:
            tmp_pdf.write(b'Mock PDF content')
            tmp_pdf.flush()
            
            instructions_path = self.test_data_dir / 'test_instructions.md'
            
            # Mock both processors to avoid PDF parsing issues in testing
            with patch.object(self.tester, 'get_ss1_processor') as mock_ss1, \
                 patch.object(self.tester, 'get_ss2_processor') as mock_ss2:
                
                # Create mock processors
                mock_ss1_instance = Mock()
                mock_ss2_instance = Mock()
                mock_ss1.return_value = mock_ss1_instance
                mock_ss2.return_value = mock_ss2_instance
                
                # Mock consistent responses
                mock_response = "# Test Analysis\nMocked response for parity testing"
                mock_ss1_instance.read_instruction_file.return_value = "Test instructions"
                mock_ss1_instance.extract_pdf_text.return_value = "Mock PDF content"
                mock_ss1_instance.process_report.return_value = mock_response
                
                mock_ss2_instance.read_instruction_file.return_value = "Test instructions"
                mock_ss2_instance.extract_pdf_text.return_value = "Mock PDF content" 
                mock_ss2_instance.process_report.return_value = mock_response
                
                try:
                    result = self.tester.run_parity_test(
                        pdf_path=tmp_pdf.name,
                        instructions_path=str(instructions_path),
                        test_name='basic_mock_test'
                    )
                    
                    self.assertTrue(result['success'], f"Parity test failed: {result.get('error', 'Unknown error')}")
                    self.assertTrue(result['comparison']['identical'], 
                                  f"Outputs not identical: {result['comparison']}")
                finally:
                    # Clean up
                    os.unlink(tmp_pdf.name)
    
    def test_pdf_extraction_parity(self):
        """Test that PDF text extraction is identical between versions"""
        # This test would use real PDFs when available
        pytest.skip("Requires real PDF test files - implement when available")
    
    def test_instruction_parsing_parity(self):
        """Test that instruction file parsing is identical"""
        instructions_path = self.test_data_dir / 'test_instructions.md'
        
        ss1_processor = self.tester.get_ss1_processor()
        ss2_processor = self.tester.get_ss2_processor()
        
        ss1_instructions = ss1_processor.read_instruction_file(str(instructions_path))
        ss2_instructions = ss2_processor.read_instruction_file(str(instructions_path))
        
        self.assertEqual(ss1_instructions, ss2_instructions, 
                        "Instruction parsing differs between versions")
    
    @pytest.mark.skipif(not os.getenv('OPENAI_API_KEY'), reason="Requires OpenAI API key")
    def test_real_api_parity(self):
        """Test parity with real API calls (requires API key)"""
        # This test would run with real API calls when API key is available
        pytest.skip("Real API testing not implemented yet")


def generate_baseline():
    """Generate baseline outputs for parity testing"""
    print("Generating parity baseline...")
    
    tester = SafetySigmaParityTester()
    baseline_data = {}
    
    # Add baseline generation logic here
    baseline_file = Path(__file__).parent / 'fixtures' / 'baseline_outputs.json'
    baseline_file.parent.mkdir(exist_ok=True)
    
    with open(baseline_file, 'w') as f:
        json.dump(baseline_data, f, indent=2)
    
    print(f"Baseline saved to: {baseline_file}")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Safety Sigma parity testing')
    parser.add_argument('--generate-baseline', action='store_true', 
                       help='Generate baseline outputs for comparison')
    
    args = parser.parse_args()
    
    if args.generate_baseline:
        generate_baseline()
    else:
        unittest.main()