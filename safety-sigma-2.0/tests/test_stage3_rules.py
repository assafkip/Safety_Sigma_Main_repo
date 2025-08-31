#!/usr/bin/env python3
"""
Stage 3 Tests - Advanced Decision Trees with Rule Engines

Tests the rule engine system with YAML-based configuration, conditional logic,
and enhanced agent integration. Validates rule evaluation, workflow selection,
and comprehensive decision audit trails.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Dict, Any
from unittest.mock import patch, Mock

# Add safety_sigma to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rules import BaseRuleEngine, RuleCondition, RuleNode, RuleSet, DocumentClassifierEngine
from agents import EnhancedAgent, AgentDecision, AgentResult
from agents.agent_processor import AgentProcessor


class TestRuleEngine(unittest.TestCase):
    """Test the base rule engine functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = Path("test_rule_engine")
        self.test_dir.mkdir(exist_ok=True)
        self.rules_dir = self.test_dir / "rules"
        self.rules_dir.mkdir(exist_ok=True)
        
        # Create simple test rule configuration
        test_rule = {
            'name': 'test_rules',
            'version': '1.0.0',
            'description': 'Test rules for validation',
            'default_workflow': 'general_analysis_workflow',
            'rules': [
                {
                    'id': 'test_node_1',
                    'name': 'Test Node 1',
                    'operator': 'AND',
                    'workflow': 'fraud_analysis_workflow',
                    'confidence_boost': 0.2,
                    'conditions': [
                        {
                            'field': 'test_field',
                            'operator': 'gt',
                            'value': 10,
                            'weight': 1.0
                        }
                    ],
                    'actions': [
                        {
                            'type': 'log',
                            'message': 'Test rule matched'
                        }
                    ]
                }
            ]
        }
        
        # Write test rule file
        import yaml
        with open(self.rules_dir / "test_rules.yaml", 'w') as f:
            yaml.dump(test_rule, f)
    
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
    
    def test_rule_condition_evaluation(self):
        """Test individual rule condition evaluation"""
        # Test greater than condition
        condition = RuleCondition(field='value', operator='gt', value=5)
        self.assertTrue(condition.evaluate({'value': 10}))
        self.assertFalse(condition.evaluate({'value': 3}))
        
        # Test equality condition
        condition = RuleCondition(field='type', operator='eq', value='fraud')
        self.assertTrue(condition.evaluate({'type': 'fraud'}))
        self.assertFalse(condition.evaluate({'type': 'general'}))
        
        # Test contains condition
        condition = RuleCondition(field='text', operator='contains', value='test')
        self.assertTrue(condition.evaluate({'text': 'This is a test'}))
        self.assertFalse(condition.evaluate({'text': 'No match here'}))
        
        # Test in condition
        condition = RuleCondition(field='category', operator='in', value=['a', 'b', 'c'])
        self.assertTrue(condition.evaluate({'category': 'b'}))
        self.assertFalse(condition.evaluate({'category': 'd'}))
    
    def test_rule_node_evaluation(self):
        """Test rule node evaluation with conditions"""
        # Create test node with AND conditions
        node = RuleNode(
            node_id='test_node',
            name='Test Node',
            operator='AND',
            workflow='test_workflow',
            confidence_boost=0.1
        )
        
        node.conditions = [
            RuleCondition(field='value1', operator='gt', value=5),
            RuleCondition(field='value2', operator='eq', value='test')
        ]
        
        # Test matching context
        context = {'value1': 10, 'value2': 'test'}
        result = node.evaluate(context)
        self.assertTrue(result['matched'])
        self.assertEqual(result['confidence_boost'], 0.1)
        self.assertEqual(result['workflow'], 'test_workflow')
        
        # Test non-matching context
        context = {'value1': 3, 'value2': 'test'}
        result = node.evaluate(context)
        self.assertFalse(result['matched'])
        self.assertEqual(result['confidence_boost'], 0.0)
    
    def test_rule_set_evaluation(self):
        """Test complete rule set evaluation"""
        # Create rule set with multiple nodes
        ruleset = RuleSet(
            name='test_ruleset',
            version='1.0.0',
            description='Test ruleset'
        )
        
        # Add root nodes
        fraud_node = RuleNode(
            node_id='fraud_detection',
            name='Fraud Detection',
            workflow='fraud_analysis_workflow',
            confidence_boost=0.3
        )
        fraud_node.conditions = [
            RuleCondition(field='fraud_score', operator='gt', value=0.8)
        ]
        
        general_node = RuleNode(
            node_id='general_analysis',
            name='General Analysis',
            workflow='general_analysis_workflow',
            confidence_boost=0.1
        )
        general_node.conditions = [
            RuleCondition(field='document_length', operator='gt', value=100)
        ]
        
        ruleset.root_nodes = [fraud_node, general_node]
        
        # Test evaluation with fraud context
        context = {'fraud_score': 0.9, 'document_length': 500}
        result = ruleset.evaluate(context)
        
        self.assertEqual(result['ruleset_name'], 'test_ruleset')
        self.assertIn('fraud_analysis_workflow', result['matched_workflows'])
        self.assertIn('general_analysis_workflow', result['matched_workflows'])
        self.assertGreater(result['total_confidence_boost'], 0.3)


class TestDocumentClassifier(unittest.TestCase):
    """Test the document classification rule engine"""
    
    def setUp(self):
        """Set up test environment"""
        # Initialize with default rules directory
        self.classifier = DocumentClassifierEngine()
    
    def test_keyword_counting(self):
        """Test keyword counting functionality"""
        text = "This document contains fraud and scam activities with phishing attempts"
        fraud_keywords = self.classifier._get_fraud_keywords()
        count = self.classifier._count_keywords(text, fraud_keywords)
        self.assertGreaterEqual(count, 3)  # Should find fraud, scam, phishing
    
    def test_document_structure_detection(self):
        """Test document structure detection"""
        structured_text = """# Header
        - List item 1
        - List item 2
        
        Some text with email@example.com and phone 555-1234
        """
        
        self.assertTrue(self.classifier._has_headers(structured_text))
        self.assertTrue(self.classifier._has_lists(structured_text))
        self.assertTrue(self.classifier._has_emails(structured_text))
        self.assertTrue(self.classifier._has_phone_numbers(structured_text))
    
    def test_document_context_analysis(self):
        """Test comprehensive document context analysis"""
        document_content = """
        This document describes fraudulent activities and scam operations.
        The investigation reveals deceptive practices targeting victims.
        Contact: fraud@example.com, Phone: 555-0123
        """
        instructions = "Analyze this document for fraud indicators"
        
        context = self.classifier.analyze_document_context(
            document_content, instructions, pdf_file="test.pdf"
        )
        
        # Check basic characteristics
        self.assertIn('document_length', context)
        self.assertIn('word_count', context)
        self.assertTrue(context['has_pdf_file'])
        
        # Check keyword analysis
        self.assertGreater(context['fraud_keyword_count'], 0)
        self.assertGreater(context['fraud_keyword_density'], 0)
        
        # Check instruction analysis
        self.assertTrue(context['instructions_mention_fraud'])
        
        # Check structure detection
        self.assertTrue(context['has_emails'])
        self.assertTrue(context['has_phone_numbers'])


class TestEnhancedAgent(unittest.TestCase):
    """Test Enhanced Agent implementation"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = Path("test_enhanced_agent")
        self.test_dir.mkdir(exist_ok=True)
        
        # Create rules directory with test configuration
        rules_dir = self.test_dir / "rules"
        rules_dir.mkdir(exist_ok=True)
        
        # Create minimal test rule configuration
        test_config = {
            'name': 'document_classification',
            'version': '1.0.0',
            'description': 'Test classification rules',
            'default_workflow': 'general_analysis_workflow',
            'rules': [
                {
                    'id': 'fraud_test',
                    'name': 'Fraud Test Rule',
                    'operator': 'AND',
                    'workflow': 'fraud_analysis_workflow',
                    'confidence_boost': 0.3,
                    'conditions': [
                        {'field': 'fraud_keyword_count', 'operator': 'ge', 'value': 2}
                    ]
                }
            ]
        }
        
        import yaml
        with open(rules_dir / "document_classification.yaml", 'w') as f:
            yaml.dump(test_config, f)
        
        # Initialize agent with test rules
        self.agent = EnhancedAgent(
            audit_dir=str(self.test_dir / "audit"),
            rules_dir=str(rules_dir)
        )
    
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
        """Test Enhanced Agent initialization"""
        self.assertEqual(self.agent.name, "enhanced_agent")
        self.assertEqual(self.agent.version, "1.0.0")
        self.assertIn("fraud_analysis_workflow", self.agent.supported_workflows)
        self.assertIn("technical_analysis_workflow", self.agent.supported_workflows)
        
        # Check rule engine initialization
        self.assertIsNotNone(self.agent.rule_engine)
        self.assertIn('document_classification', self.agent.rule_engine.rulesets)
    
    def test_enhanced_input_analysis(self):
        """Test enhanced input analysis with rule engine"""
        inputs = {
            'pdf_file': 'test.pdf',
            'instructions': 'Extract fraud indicators from this financial document',
            'document_content': '''This document contains evidence of fraudulent transactions, 
                                  scam operations, and deceptive practices used to target victims.
                                  The investigation reveals systematic fraud patterns.'''
        }
        
        analysis = self.agent._analyze_inputs(inputs)
        
        # Check rule engine results are included
        self.assertIn('rule_classification', analysis)
        self.assertIn('rule_recommended_workflow', analysis)
        self.assertIn('rule_confidence_score', analysis)
        self.assertIn('rule_matched_rules', analysis)
        
        # Check backward compatibility fields
        self.assertIn('document_type', analysis)
        self.assertIn('complexity_level', analysis)
        
        # Check enhanced analysis fields
        self.assertIn('keyword_analysis', analysis)
        self.assertIn('structure_analysis', analysis)
        self.assertIn('instruction_analysis', analysis)
        
        # Should detect fraud content
        self.assertGreater(analysis['rule_confidence_score'], 0.5)
    
    def test_rule_based_decision_making(self):
        """Test rule-based workflow decision making"""
        input_analysis = {
            'rule_classification': {'total_confidence_boost': 0.3},
            'rule_recommended_workflow': 'fraud_analysis_workflow',
            'rule_confidence_score': 0.85,
            'rule_matched_rules': ['fraud_test'],
            'rule_decision_factors': {
                'keyword_analysis': {'fraud_density': 0.05},
                'structure_analysis': {'has_financial_data': True},
                'instruction_analysis': {'mentions_fraud': True}
            }
        }
        
        decision = self.agent._make_decision("test-id", input_analysis, {})
        
        self.assertEqual(decision.selected_workflow, 'fraud_analysis_workflow')
        self.assertEqual(decision.confidence_score, 0.85)
        self.assertIn('fraud_test', decision.metadata['matched_rules'])
        self.assertGreater(len(decision.reasoning), 3)
        self.assertIn('Rule engine analysis completed', decision.reasoning[0])
    
    def test_rule_enhancement_application(self):
        """Test rule-based instruction enhancements"""
        instructions = "Analyze this document"
        rule_actions = [
            {'type': 'enhance_instructions', 'enhancement': 'fraud_detection_focus'}
        ]
        workflow_name = 'fraud_analysis_workflow'
        
        enhanced = self.agent._apply_rule_enhancements(instructions, rule_actions, workflow_name)
        
        self.assertIn("SPECIAL FOCUS", enhanced)
        self.assertIn("fraud indicators", enhanced)
        self.assertIn("STAGE 3 RULE-BASED FRAUD ANALYSIS", enhanced)
        self.assertIn(instructions, enhanced)  # Original instructions preserved
    
    def test_agent_execution_with_mocked_orchestrator(self):
        """Test full agent execution with rule engine"""
        # Mock the tool orchestrator
        mock_orchestrator = Mock()
        
        # Mock successful orchestration result
        mock_orch_result = Mock()
        mock_orch_result.success = True
        mock_orch_result.steps_executed = 2
        mock_orch_result.context = {'analysis_result': 'Mock rule-enhanced analysis'}
        mock_orch_result.step_results = {}
        mock_orch_result.error = None
        
        mock_orchestrator.ss_pipeline = ['step1', 'step2']
        mock_orchestrator.execute_safety_sigma_pipeline.return_value = mock_orch_result
        
        # Replace agent's orchestrator
        self.agent.tool_orchestrator = mock_orchestrator
        
        # Execute agent with fraud content
        result = self.agent.execute(
            pdf_file='test.pdf',
            instructions='Analyze for fraud patterns',
            document_content='This document contains multiple fraud indicators including scam operations and deceptive practices.',
            simulate=True
        )
        
        # Validate results
        self.assertTrue(result.success)
        self.assertIsNotNone(result.decision)
        self.assertEqual(result.decision.selected_workflow, 'fraud_analysis_workflow')
        self.assertGreater(len(result.audit_trail), 5)
        
        # Check enhanced result structure
        workflow_result = result.workflow_result
        self.assertIn('enhanced_by_stage3', workflow_result)
        self.assertTrue(workflow_result['enhanced_by_stage3'])
        self.assertGreater(workflow_result['rule_matched_count'], 0)
    
    def test_rule_engine_info(self):
        """Test rule engine information retrieval"""
        info = self.agent.get_rule_engine_info()
        
        self.assertEqual(info['engine_type'], 'DocumentClassifierEngine')
        self.assertIn('document_classification', info['loaded_rulesets'])
        self.assertIn('document_classification', info['supported_rulesets'])


class TestAgentProcessorStage3(unittest.TestCase):
    """Test Agent Processor with Stage 3 integration"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = Path("test_agent_processor_stage3")
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
    
    def test_enhanced_agent_processor_initialization(self):
        """Test agent processor initialization with enhanced agent"""
        processor = AgentProcessor(agent_type="enhanced", audit_dir=str(self.test_dir))
        
        self.assertEqual(processor.agent_type, "enhanced")
        self.assertIsInstance(processor.agent, EnhancedAgent)
        self.assertIn("Stage 3", processor._stage)
    
    def test_enhanced_agent_stage_info(self):
        """Test enhanced agent processor stage information"""
        processor = AgentProcessor(agent_type="enhanced")
        
        stage_info = processor.get_stage_info()
        
        self.assertIn("Stage 3", stage_info['stage'])
        self.assertEqual(stage_info['agent_type'], 'enhanced')
        self.assertTrue(stage_info['tools_enabled'])
        self.assertTrue(stage_info['agent_enabled'])
        self.assertIn('technical_analysis_workflow', stage_info['supported_workflows'])
        self.assertIn('compliance_audit_workflow', stage_info['supported_workflows'])


class TestStage3Integration(unittest.TestCase):
    """Test Stage 3 integration with existing architecture"""
    
    @patch.dict(os.environ, {'SS2_ENABLE_TOOLS': 'true', 'SS2_ENHANCE_DOCS': 'true'})
    def test_stage3_feature_detection(self):
        """Test that Stage 3 features are properly detected"""
        # Force reload of feature toggles
        import safety_sigma
        import importlib
        importlib.reload(safety_sigma)
        
        version_info = safety_sigma.get_version_info()
        self.assertIn("Stage 3", version_info['active_stage'])
    
    def test_stage3_processor_routing(self):
        """Test that processor correctly routes to Stage 3"""
        # Mock feature toggles
        with patch('safety_sigma.processor.FEATURE_TOGGLES', {
            'SS2_ENABLE_TOOLS': True,
            'SS2_ENHANCE_DOCS': True,
            'SS2_USE_AGENT': False  # Should be overridden by SS2_ENHANCE_DOCS
        }):
            from safety_sigma.processor import SafetySigmaProcessor
            
            processor = SafetySigmaProcessor()
            stage_info = processor.get_stage_info()
            
            self.assertIn("Stage 3", stage_info['stage'])


if __name__ == '__main__':
    # Set up test environment
    os.environ['SS2_ENABLE_TOOLS'] = 'true'
    os.environ['SS2_ENHANCE_DOCS'] = 'true'
    os.environ['OPENAI_API_KEY'] = 'mock-key-for-testing'
    
    unittest.main()