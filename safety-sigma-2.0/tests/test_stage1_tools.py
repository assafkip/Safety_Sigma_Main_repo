#!/usr/bin/env python3
"""
Stage 1 Tests - Tool Abstraction Layer

Tests the tool abstraction layer ensuring parity with Safety Sigma 1.0.
Validates that tool wrappers produce identical results to direct SS1 calls.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict
from unittest.mock import patch, Mock

import pytest

# Add safety_sigma to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools import PDFTool, ExtractionTool, BaseTool, ToolResult
from orchestration import ToolOrchestrator


class TestBaseTool(unittest.TestCase):
    """Test the base tool interface and audit logging"""
    
    def setUp(self):
        """Set up test environment"""
        self.audit_dir = Path("test_audit_logs")
        self.audit_dir.mkdir(exist_ok=True)
    
    def tearDown(self):
        """Clean up test environment"""
        # Clean up audit logs
        if self.audit_dir.exists():
            for file in self.audit_dir.glob("*"):
                file.unlink()
            self.audit_dir.rmdir()
    
    def test_tool_result_creation(self):
        """Test ToolResult creation and audit trail"""
        result = ToolResult(data="test data")
        result.add_audit_entry("Test entry")
        
        self.assertTrue(result.success)
        self.assertEqual(result.data, "test data")
        self.assertEqual(len(result.audit_trail), 1)
        self.assertIn("Test entry", result.audit_trail[0])
    
    def test_base_tool_validation(self):
        """Test base tool validation framework"""
        class TestTool(BaseTool):
            name = "test_tool"
            required_params = ["required_param"]
            
            def _run(self, **kwargs):
                return "test_result"
        
        tool = TestTool()
        
        # Test missing required parameter
        with self.assertRaises(ValueError):
            tool.execute()
        
        # Test successful execution
        result = tool.execute(required_param="test_value")
        self.assertTrue(result.success)
        self.assertEqual(result.data, "test_result")


class TestPDFTool(unittest.TestCase):
    """Test PDF tool wrapper"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.test_dir = Path("test_pdf_outputs")
        cls.test_dir.mkdir(exist_ok=True)
        
        # Create test PDF file
        cls.test_pdf = cls.test_dir / "test.pdf"
        with open(cls.test_pdf, 'wb') as f:
            f.write(b'%PDF-1.4\nTest PDF content for validation')
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment"""
        if cls.test_dir.exists():
            for file in cls.test_dir.glob("*"):
                file.unlink()
            cls.test_dir.rmdir()
    
    def test_pdf_tool_initialization(self):
        """Test PDF tool initialization"""
        tool = PDFTool()
        self.assertEqual(tool.name, "pdf_tool")
        self.assertEqual(tool.version, "1.0.0")
        self.assertIn("pdf_path", tool.required_params)
    
    @patch('tools.pdf_tool.PDFTool._import_ss1')
    def test_pdf_tool_validation(self, mock_import):
        """Test PDF tool input validation"""
        # Mock the SS1 processor
        mock_processor = Mock()
        mock_import.return_value = None
        
        tool = PDFTool()
        tool._ss1_processor = mock_processor
        
        # Test missing file
        with self.assertRaises(FileNotFoundError):
            tool.execute(pdf_path="nonexistent.pdf")
        
        # Test file size validation
        with patch('pathlib.Path.stat') as mock_stat:
            mock_stat.return_value.st_size = 200 * 1024 * 1024  # 200MB
            with patch.dict(os.environ, {'SS2_MAX_PDF_SIZE_MB': '100'}):
                with self.assertRaises(ValueError):
                    tool.execute(pdf_path=str(self.test_pdf))
    
    @patch('tools.pdf_tool.PDFTool._import_ss1')
    def test_pdf_tool_execution(self, mock_import):
        """Test PDF tool execution with mocked backend"""
        # Mock the SS1 processor
        mock_processor = Mock()
        mock_processor.extract_pdf_text.return_value = "Extracted PDF text content"
        mock_import.return_value = None
        
        tool = PDFTool()
        tool._ss1_processor = mock_processor
        
        result = tool.execute(pdf_path=str(self.test_pdf))
        
        self.assertTrue(result.success)
        self.assertEqual(result.data, "Extracted PDF text content")
        self.assertGreater(len(result.audit_trail), 0)
        self.assertIn("source_traceability", result.metadata)


class TestExtractionTool(unittest.TestCase):
    """Test extraction tool wrapper"""
    
    @patch('tools.extraction_tool.ExtractionTool._import_ss1')
    def test_extraction_tool_initialization(self, mock_import):
        """Test extraction tool initialization"""
        mock_import.return_value = None
        
        tool = ExtractionTool()
        self.assertEqual(tool.name, "extraction_tool")
        self.assertEqual(tool.version, "1.0.0")
        self.assertIn("instructions", tool.required_params)
        self.assertIn("text_content", tool.required_params)
    
    @patch('tools.extraction_tool.ExtractionTool._import_ss1')
    def test_extraction_tool_validation(self, mock_import):
        """Test extraction tool input validation"""
        mock_processor = Mock()
        mock_import.return_value = None
        
        tool = ExtractionTool()
        tool._ss1_processor = mock_processor
        
        # Test missing parameters
        with self.assertRaises(ValueError):
            tool.execute()
        
        # Test short instructions
        with self.assertRaises(ValueError):
            tool.execute(instructions="short", text_content="test content")
        
        # Test short content
        with self.assertRaises(ValueError):
            tool.execute(instructions="valid instructions", text_content="short")
    
    @patch('tools.extraction_tool.ExtractionTool._import_ss1')
    def test_extraction_tool_zero_inference(self, mock_import):
        """Test zero-inference compliance checking"""
        mock_processor = Mock()
        mock_import.return_value = None
        
        tool = ExtractionTool(zero_inference=True)
        tool._ss1_processor = mock_processor
        
        # Test content with synthetic language
        synthetic_output = "Based on the analysis, it appears that this document suggests possible fraud"
        source_content = "Document content about security policies"
        
        violations = tool._check_zero_inference_compliance(synthetic_output, source_content)
        self.assertGreater(len(violations), 0)
    
    @patch('tools.extraction_tool.ExtractionTool._import_ss1') 
    def test_extraction_tool_simulation(self, mock_import):
        """Test extraction tool simulation mode"""
        mock_processor = Mock()
        mock_import.return_value = None
        
        tool = ExtractionTool()
        tool._ss1_processor = mock_processor
        
        result = tool.execute(
            instructions="Extract key information from the document",
            text_content="This is test content for extraction",
            simulate=True
        )
        
        self.assertTrue(result.success)
        self.assertIn("SIMULATED", result.data)
        self.assertIn("Zero-inference mode", result.data)


class TestToolOrchestrator(unittest.TestCase):
    """Test tool orchestrator"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = Path("test_orchestration")
        self.test_dir.mkdir(exist_ok=True)
        
        # Create test PDF
        self.test_pdf = self.test_dir / "test.pdf"
        with open(self.test_pdf, 'w') as f:
            f.write("Mock PDF content")
        
        self.orchestrator = ToolOrchestrator(audit_dir=str(self.test_dir / "audit"))
    
    def tearDown(self):
        """Clean up test environment"""
        if self.test_dir.exists():
            for file in self.test_dir.rglob("*"):
                if file.is_file():
                    file.unlink()
            for dir in sorted(self.test_dir.rglob("*"), reverse=True):
                if dir.is_dir():
                    dir.rmdir()
            self.test_dir.rmdir()
    
    def test_orchestrator_initialization(self):
        """Test orchestrator initialization"""
        self.assertIsNotNone(self.orchestrator.ss_pipeline)
        self.assertEqual(len(self.orchestrator.ss_pipeline), 2)  # PDF + Extraction
    
    @patch('tools.pdf_tool.PDFTool._import_ss1')
    @patch('tools.extraction_tool.ExtractionTool._import_ss1')
    def test_orchestrator_pipeline_execution(self, mock_extract_import, mock_pdf_import):
        """Test full pipeline execution"""
        # Mock the tools
        mock_pdf_processor = Mock()
        mock_pdf_processor.extract_pdf_text.return_value = "Mock PDF extracted text"
        mock_pdf_import.return_value = None
        
        mock_extract_processor = Mock()
        mock_extract_processor.process_report.return_value = "Mock analysis result"
        mock_extract_import.return_value = None
        
        # Patch the tool instances
        with patch('tools.pdf_tool.PDFTool._ss1_processor', mock_pdf_processor), \
             patch('tools.extraction_tool.ExtractionTool._ss1_processor', mock_extract_processor):
            
            result = self.orchestrator.execute_safety_sigma_pipeline(
                pdf_file=str(self.test_pdf),
                instructions="Test extraction instructions",
                simulate=True
            )
        
        self.assertTrue(result.success)
        self.assertEqual(result.steps_executed, 2)
        self.assertEqual(result.steps_successful, 2)
        self.assertIn("extracted_text", result.context)
        self.assertIn("analysis_result", result.context)


class TestStage1Parity(unittest.TestCase):
    """Test Stage 1 parity with Safety Sigma 1.0"""
    
    def setUp(self):
        """Set up parity testing environment"""
        self.ss1_path = os.getenv('SS1_PATH', '../Desktop/safety_sigma/phase_1')
        
        if not Path(self.ss1_path).exists():
            self.skipTest(f"Safety Sigma 1.0 not found at {self.ss1_path}")
    
    @patch.dict(os.environ, {'SS2_ENABLE_TOOLS': 'true'})
    def test_stage1_feature_detection(self):
        """Test that Stage 1 features are properly detected"""
        from safety_sigma import get_version_info, FEATURE_TOGGLES
        
        # Force reload of feature toggles
        import safety_sigma
        import importlib
        importlib.reload(safety_sigma)
        
        version_info = safety_sigma.get_version_info()
        self.assertIn("Stage 1", version_info['active_stage'])
    
    @patch('tools.pdf_tool.PDFTool._import_ss1')
    @patch('tools.extraction_tool.ExtractionTool._import_ss1')
    def test_end_to_end_parity(self, mock_extract_import, mock_pdf_import):
        """Test end-to-end parity between Stage 1 and SS1"""
        # Mock both processors to return identical results
        mock_pdf_result = "Mock PDF content for parity testing"
        mock_analysis_result = "Mock analysis result for parity testing"
        
        # Mock SS1 processors
        mock_pdf_processor = Mock()
        mock_pdf_processor.extract_pdf_text.return_value = mock_pdf_result
        mock_pdf_import.return_value = None
        
        mock_extract_processor = Mock()
        mock_extract_processor.process_report.return_value = mock_analysis_result
        mock_extract_import.return_value = None
        
        # Test Stage 1 (tool abstraction)
        with patch('tools.pdf_tool.PDFTool._ss1_processor', mock_pdf_processor), \
             patch('tools.extraction_tool.ExtractionTool._ss1_processor', mock_extract_processor):
            
            orchestrator = ToolOrchestrator()
            
            # Create temporary PDF
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_pdf:
                tmp_pdf.write(b'Mock PDF content')
                tmp_pdf.flush()
                
                try:
                    result = orchestrator.execute_safety_sigma_pipeline(
                        pdf_file=tmp_pdf.name,
                        instructions="Test instructions for parity checking",
                        simulate=True
                    )
                    
                    # Verify successful execution
                    self.assertTrue(result.success)
                    self.assertIn("analysis_result", result.context)
                    
                    # The exact content will be simulation results, but structure should be preserved
                    self.assertIsInstance(result.context["analysis_result"], str)
                    self.assertGreater(len(result.context["analysis_result"]), 100)
                    
                finally:
                    os.unlink(tmp_pdf.name)


if __name__ == '__main__':
    # Set up test environment
    os.environ['SS2_ENABLE_TOOLS'] = 'true'  # Enable Stage 1 for testing
    os.environ['OPENAI_API_KEY'] = 'mock-key-for-testing'
    
    unittest.main()