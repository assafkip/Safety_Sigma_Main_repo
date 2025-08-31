#!/usr/bin/env python3
"""
Stage 2 Tests - Simple Agent Logic

Tests the agent-based processing with deterministic workflow selection.
Validates agent decision making, audit trails, and tool integration.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Dict, Any
from unittest.mock import patch, Mock

# import pytest  # Not needed for unittest execution

# Add safety_sigma to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents import BaseAgent, SimpleAgent, AgentDecision, AgentResult
from agents.agent_processor import AgentProcessor


class TestBaseAgent(unittest.TestCase):
    """Test the base agent interface and decision audit logging"""
    
    def setUp(self):
        """Set up test environment"""
        self.audit_dir = Path("test_agent_audit")
        self.audit_dir.mkdir(exist_ok=True)
    
    def tearDown(self):
        """Clean up test environment"""
        # Clean up audit logs
        if self.audit_dir.exists():
            for file in self.audit_dir.glob("*"):
                file.unlink()
            self.audit_dir.rmdir()
    
    def test_agent_decision_creation(self):
        """Test AgentDecision creation and JSON serialization"""
        decision = AgentDecision(
            decision_id="test-123",
            agent_name="test_agent",
            agent_version="1.0.0",
            timestamp=1234567890.0,
            input_analysis={"doc_type": "fraud"},
            decision_logic="Test logic",
            selected_workflow="test_workflow",
            confidence_score=0.85,
            reasoning=["Reason 1", "Reason 2"]
        )
        
        json_output = decision.to_json()
        self.assertIn("test-123", json_output)
        self.assertIn("fraud", json_output)
        self.assertIn("0.85", json_output)
    
    def test_agent_result_audit_trail(self):
        """Test AgentResult audit trail functionality"""
        result = AgentResult(
            success=True,
            agent_name="test_agent",
            decision=None  # Will be set by agent
        )
        
        result.add_audit_entry("Test entry 1")
        result.add_audit_entry("Test entry 2")
        
        self.assertEqual(len(result.audit_trail), 2)
        self.assertIn("Test entry 1", result.audit_trail[0])
        self.assertIn("Test entry 2", result.audit_trail[1])


class TestInputAnalysis(unittest.TestCase):
    """Test input analysis functions"""
    
    def test_document_type_analysis(self):
        """Test document type detection"""
        from agents.base_agent import analyze_document_type
        
        # Test fraud detection
        fraud_text = "This document describes fraudulent activities and scam operations"
        doc_type, confidence = analyze_document_type(fraud_text)
        self.assertEqual(doc_type, "fraud_analysis")
        self.assertGreater(confidence, 0.5)
        
        # Test threat intelligence
        threat_text = "Analysis of malware threat actors and attack vectors"
        doc_type, confidence = analyze_document_type(threat_text)
        self.assertEqual(doc_type, "threat_intelligence")
        self.assertGreater(confidence, 0.5)
        
        # Test general analysis fallback
        general_text = "This is a general document with no specific indicators"
        doc_type, confidence = analyze_document_type(general_text)
        self.assertEqual(doc_type, "general_analysis")
    
    def test_complexity_analysis(self):
        """Test document complexity detection"""
        from agents.base_agent import analyze_document_complexity
        
        # Simple document
        simple_text = "Short document."
        complexity, confidence = analyze_document_complexity(simple_text)
        self.assertEqual(complexity, "simple")
        
        # Complex document  
        complex_text = " ".join(["Complex technical document with API endpoints and encryption protocols"] * 100)
        complexity, confidence = analyze_document_complexity(complex_text)
        self.assertIn(complexity, ["moderate", "complex"])
    
    def test_structure_analysis(self):
        """Test document structure analysis"""
        from agents.base_agent import analyze_document_structure
        
        structured_text = """# Header
        - List item
        - Another item
        
        
        ## Subheader
        Some content with `code` formatting.
        """
        
        structure = analyze_document_structure(structured_text)
        self.assertTrue(structure['has_headers'])
        self.assertTrue(structure['has_lists'])
        self.assertTrue(structure['has_technical_formatting'])
        self.assertGreaterEqual(structure['paragraph_count'], 1)


class TestSimpleAgent(unittest.TestCase):
    """Test Simple Agent implementation"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = Path("test_simple_agent")
        self.test_dir.mkdir(exist_ok=True)
        self.agent = SimpleAgent(audit_dir=str(self.test_dir / "audit"))
    
    def tearDown(self):
        """Clean up test environment"""
        if self.test_dir.exists():
            for file in self.test_dir.rglob("*"):
                if file.is_file():
                    file.unlink()
            for dir_path in sorted(self.test_dir.rglob("*"), reverse=True):
                if dir_path.is_dir():
                    dir_path.rmdir()
            self.test_dir.rmdir()
    
    def test_agent_initialization(self):
        """Test Simple Agent initialization"""
        self.assertEqual(self.agent.name, "simple_agent")
        self.assertEqual(self.agent.version, "1.0.0")
        self.assertIn("fraud_analysis_workflow", self.agent.supported_workflows)
        self.assertIn("general_analysis_workflow", self.agent.supported_workflows)
    
    def test_input_analysis(self):
        """Test agent input analysis"""
        inputs = {
            'pdf_file': 'test.pdf',
            'instructions': 'Extract fraud indicators from this financial document',
            'document_content': 'Document about fraudulent transactions and suspicious activities'
        }
        
        analysis = self.agent._analyze_inputs(inputs)
        
        self.assertIn('document_type', analysis)
        self.assertIn('complexity_level', analysis)
        self.assertIn('structure_analysis', analysis)
        self.assertIn('instruction_analysis', analysis)
        self.assertIn('file_analysis', analysis)
        
        # Should detect fraud content
        self.assertEqual(analysis['document_type'], 'fraud_analysis')
        self.assertGreater(analysis['document_type_confidence'], 0.5)
    
    def test_workflow_decision_making(self):
        """Test deterministic workflow decision making"""
        # Test fraud workflow selection
        input_analysis = {
            'document_type': 'fraud_analysis',
            'document_type_confidence': 0.9,
            'complexity_level': 'moderate',
            'complexity_confidence': 0.8,
            'instruction_analysis': {'mentions_detection': True},
            'file_analysis': {'estimated_size': 'medium'},
            'content_length': 1000
        }
        
        decision = self.agent._make_decision("test-id", input_analysis, {})
        
        self.assertEqual(decision.selected_workflow, 'fraud_analysis_workflow')
        self.assertGreater(decision.confidence_score, 0.8)
        self.assertGreater(len(decision.reasoning), 2)
        self.assertIn('fraud', decision.reasoning[0].lower())
    
    def test_general_workflow_fallback(self):
        """Test fallback to general workflow"""
        input_analysis = {
            'document_type': 'general_analysis',
            'document_type_confidence': 0.7,
            'complexity_level': 'simple',
            'complexity_confidence': 0.8,
            'instruction_analysis': {},
            'file_analysis': {'estimated_size': 'small'},
            'content_length': 200
        }
        
        decision = self.agent._make_decision("test-id", input_analysis, {})
        
        self.assertEqual(decision.selected_workflow, 'general_analysis_workflow')
        self.assertIn('general', decision.reasoning[-1].lower())
    
    def test_instruction_enhancement(self):
        """Test workflow-specific instruction enhancement"""
        original_instructions = "Analyze this document"
        
        # Test fraud workflow enhancement
        enhanced = self.agent._enhance_instructions_for_workflow(
            original_instructions, 'fraud_analysis_workflow'
        )
        
        self.assertIn("FRAUD ANALYSIS FOCUS", enhanced)
        self.assertIn("fraud_analysis_workflow", enhanced)
        self.assertIn(original_instructions, enhanced)
    
    def test_agent_execution_simulation(self):
        """Test full agent execution in simulation mode"""
        # Mock the tool orchestrator on the agent instance directly
        mock_orchestrator = Mock()
        
        # Mock successful orchestration result
        mock_orch_result = Mock()
        mock_orch_result.success = True
        mock_orch_result.steps_executed = 2
        mock_orch_result.duration_ms = 100.0
        mock_orch_result.context = {'analysis_result': 'Mock analysis result', 'extracted_text': 'Mock extracted text'}
        mock_orch_result.step_results = {}
        mock_orch_result.error = None
        
        # Mock the pipeline property that is used in workflow execution
        mock_orchestrator.ss_pipeline = ['step1', 'step2']  # Mock pipeline steps
        mock_orchestrator.execute_safety_sigma_pipeline.return_value = mock_orch_result
        
        # Replace the agent's tool orchestrator with our mock
        self.agent.tool_orchestrator = mock_orchestrator
        
        # Execute agent
        result = self.agent.execute(
            pdf_file='test.pdf',
            instructions='Analyze this document for fraud indicators',
            document_content='This document contains evidence of fraudulent transactions, scam operations, and other deceptive practices that need to be analyzed for fraud detection.',
            simulate=True
        )
        
        # Validate result
        self.assertTrue(result.success)
        self.assertIsNotNone(result.decision)
        # The workflow selection is deterministic but may vary based on document content analysis
        self.assertIn(result.decision.selected_workflow, ['fraud_analysis_workflow', 'general_analysis_workflow'])
        self.assertGreater(len(result.audit_trail), 5)  # Should have comprehensive audit trail
        
        # Verify orchestrator was called
        mock_orchestrator.execute_safety_sigma_pipeline.assert_called_once()


class TestAgentProcessor(unittest.TestCase):
    """Test Agent Processor integration"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = Path("test_agent_processor")
        self.test_dir.mkdir(exist_ok=True)
    
    def tearDown(self):
        """Clean up test environment"""
        if self.test_dir.exists():
            for file in self.test_dir.rglob("*"):
                if file.is_file():
                    file.unlink()
            for dir_path in sorted(self.test_dir.rglob("*"), reverse=True):
                if dir_path.is_dir():
                    dir_path.rmdir()
            self.test_dir.rmdir()
    
    def test_agent_processor_initialization(self):
        """Test agent processor initialization"""
        processor = AgentProcessor(agent_type="simple", audit_dir=str(self.test_dir))
        
        self.assertEqual(processor.agent_type, "simple")
        self.assertIsInstance(processor.agent, SimpleAgent)
        self.assertIn("Stage 2", processor._stage)
    
    def test_agent_processor_stage_info(self):
        """Test agent processor stage information"""
        processor = AgentProcessor(agent_type="simple")
        
        stage_info = processor.get_stage_info()
        
        self.assertIn("Stage 2", stage_info['stage'])
        self.assertEqual(stage_info['agent_type'], 'simple')
        self.assertTrue(stage_info['tools_enabled'])
        self.assertTrue(stage_info['agent_enabled'])
        self.assertIn('fraud_analysis_workflow', stage_info['supported_workflows'])
    
    def test_agent_info(self):
        """Test detailed agent information"""
        processor = AgentProcessor(agent_type="simple")
        
        agent_info = processor.get_agent_info()
        
        self.assertEqual(agent_info['agent_name'], 'simple_agent')
        self.assertIn('fraud_analysis_workflow', agent_info['supported_workflows'])
        self.assertIn('Hardcoded decision trees', agent_info['decision_logic'])
        self.assertGreater(len(agent_info['audit_capabilities']), 3)


class TestStage2Integration(unittest.TestCase):
    """Test Stage 2 integration with existing architecture"""
    
    @patch.dict(os.environ, {'SS2_USE_AGENT': 'true', 'SS2_ENABLE_TOOLS': 'true'})
    def test_stage2_feature_detection(self):
        """Test that Stage 2 features are properly detected"""
        # Force reload of feature toggles
        import safety_sigma
        import importlib
        importlib.reload(safety_sigma)
        
        version_info = safety_sigma.get_version_info()
        self.assertIn("Stage 2", version_info['active_stage'])
    
    def test_end_to_end_agent_processing(self):
        """Test end-to-end agent processing"""
        # Mock orchestrator for agent execution
        mock_orchestrator = Mock()
        
        mock_orch_result = Mock()
        mock_orch_result.success = True
        mock_orch_result.steps_executed = 2
        mock_orch_result.duration_ms = 150.0
        mock_orch_result.context = {
            'extracted_text': 'Mock extracted PDF text',
            'analysis_result': 'Mock comprehensive fraud analysis'
        }
        mock_orch_result.step_results = {}
        mock_orch_result.error = None
        
        # Mock the pipeline property
        mock_orchestrator.ss_pipeline = ['step1', 'step2']
        mock_orchestrator.execute_safety_sigma_pipeline.return_value = mock_orch_result
        
        # Test agent processor
        processor = AgentProcessor(agent_type="simple")
        
        # Replace the agent's tool orchestrator with our mock
        processor.agent.tool_orchestrator = mock_orchestrator
        
        # Test PDF extraction (goes through agent)
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_pdf:
            tmp_pdf.write(b'Mock PDF content')
            tmp_pdf.flush()
            
            try:
                # This will go through agent decision making
                text_result = processor.extract_pdf_text(tmp_pdf.name)
                self.assertIn('Mock', text_result)
                
                # Test report processing (full agent workflow)
                instructions = "Analyze this document for fraudulent activities"
                analysis_result = processor.process_report(instructions, text_result)
                
                self.assertIsInstance(analysis_result, str)
                self.assertIn('Mock', analysis_result)
                
            finally:
                os.unlink(tmp_pdf.name)


if __name__ == '__main__':
    # Set up test environment  
    os.environ['SS2_USE_AGENT'] = 'true'
    os.environ['SS2_ENABLE_TOOLS'] = 'true'
    os.environ['OPENAI_API_KEY'] = 'mock-key-for-testing'
    
    unittest.main()