"""
Base Rule Engine for Safety Sigma 2.0 Stage 3

Provides advanced decision tree processing with YAML-based rule configuration.
Supports conditional logic, rule chaining, and comprehensive validation.
"""

import abc
from dataclasses import dataclass, field

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
import logging


@dataclass
class RuleCondition:
    """
    Represents a single rule condition with evaluation logic
    """
    field: str
    operator: str  # eq, ne, gt, lt, ge, le, in, not_in, contains, regex
    value: Any
    weight: float = 1.0
    
    def evaluate(self, context: Dict[str, Any]) -> bool:
        """
        Evaluate condition against provided context
        
        Args:
            context: Context dictionary with field values
            
        Returns:
            True if condition is met, False otherwise
        """
        if self.field not in context:
            return False
            
        field_value = context[self.field]
        
        if self.operator == 'eq':
            return field_value == self.value
        elif self.operator == 'ne':
            return field_value != self.value
        elif self.operator == 'gt':
            return field_value > self.value
        elif self.operator == 'lt':
            return field_value < self.value
        elif self.operator == 'ge':
            return field_value >= self.value
        elif self.operator == 'le':
            return field_value <= self.value
        elif self.operator == 'in':
            return field_value in self.value
        elif self.operator == 'not_in':
            return field_value not in self.value
        elif self.operator == 'contains':
            return str(self.value).lower() in str(field_value).lower()
        elif self.operator == 'regex':
            import re
            return bool(re.search(self.value, str(field_value)))
        else:
            raise ValueError(f"Unsupported operator: {self.operator}")


@dataclass
class RuleNode:
    """
    Represents a node in the decision tree
    """
    node_id: str
    name: str
    conditions: List[RuleCondition] = field(default_factory=list)
    operator: str = "AND"  # AND or OR for combining conditions
    actions: List[Dict[str, Any]] = field(default_factory=list)
    children: List['RuleNode'] = field(default_factory=list)
    confidence_boost: float = 0.0
    workflow: Optional[str] = None
    
    def evaluate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate rule node and return results
        
        Args:
            context: Evaluation context
            
        Returns:
            Dictionary with evaluation results
        """
        # Evaluate conditions
        condition_results = [cond.evaluate(context) for cond in self.conditions]
        
        if not condition_results:
            node_matched = True  # No conditions means always match
        elif self.operator == "AND":
            node_matched = all(condition_results)
        elif self.operator == "OR":
            node_matched = any(condition_results)
        else:
            raise ValueError(f"Unsupported node operator: {self.operator}")
        
        result = {
            'node_id': self.node_id,
            'matched': node_matched,
            'confidence_boost': self.confidence_boost if node_matched else 0.0,
            'workflow': self.workflow if node_matched else None,
            'actions': self.actions if node_matched else [],
            'children_results': []
        }
        
        # Evaluate children if current node matched
        if node_matched:
            for child in self.children:
                child_result = child.evaluate(context)
                result['children_results'].append(child_result)
        
        return result


@dataclass
class RuleSet:
    """
    Complete rule set with metadata
    """
    name: str
    version: str
    description: str
    root_nodes: List[RuleNode] = field(default_factory=list)
    default_workflow: str = "general_analysis_workflow"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def evaluate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate entire rule set against context
        
        Args:
            context: Evaluation context
            
        Returns:
            Comprehensive evaluation results
        """
        results = {
            'ruleset_name': self.name,
            'ruleset_version': self.version,
            'context': context,
            'root_results': [],
            'matched_workflows': [],
            'total_confidence_boost': 0.0,
            'recommended_workflow': self.default_workflow,
            'all_actions': []
        }
        
        # Evaluate all root nodes
        for root in self.root_nodes:
            root_result = root.evaluate(context)
            results['root_results'].append(root_result)
            
            # Collect results recursively
            self._collect_results(root_result, results)
        
        # Determine recommended workflow
        if results['matched_workflows']:
            # Use workflow with highest confidence boost
            workflow_scores = {}
            for workflow in results['matched_workflows']:
                workflow_scores[workflow] = workflow_scores.get(workflow, 0) + 1
            
            results['recommended_workflow'] = max(workflow_scores.items(), key=lambda x: x[1])[0]
        
        return results
    
    def _collect_results(self, node_result: Dict[str, Any], results: Dict[str, Any]) -> None:
        """Recursively collect results from node evaluation"""
        if node_result['matched']:
            if node_result['workflow']:
                results['matched_workflows'].append(node_result['workflow'])
            
            results['total_confidence_boost'] += node_result['confidence_boost']
            results['all_actions'].extend(node_result['actions'])
        
        # Process children
        for child_result in node_result['children_results']:
            self._collect_results(child_result, results)


class BaseRuleEngine(abc.ABC):
    """
    Abstract base class for rule engines
    """
    
    def __init__(self, rules_dir: Optional[str] = None):
        """
        Initialize rule engine
        
        Args:
            rules_dir: Directory containing rule files
        """
        self.rules_dir = Path(rules_dir or 'rules/config')
        self.logger = logging.getLogger(f'safety_sigma.rules.{self.__class__.__name__.lower()}')
        self.rulesets: Dict[str, RuleSet] = {}
    
    def load_rules(self, ruleset_name: str) -> RuleSet:
        """
        Load rules from YAML configuration
        
        Args:
            ruleset_name: Name of ruleset to load
            
        Returns:
            Loaded RuleSet object
        """
        if not HAS_YAML:
            # Return a basic fallback ruleset for testing
            self.logger.warning("YAML not available, using fallback ruleset")
            return self._create_fallback_ruleset(ruleset_name)
        
        ruleset_file = self.rules_dir / f"{ruleset_name}.yaml"
        
        if not ruleset_file.exists():
            self.logger.warning(f"Ruleset file not found: {ruleset_file}, using fallback")
            return self._create_fallback_ruleset(ruleset_name)
        
        try:
            with open(ruleset_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            ruleset = self._parse_ruleset_config(config)
            self.rulesets[ruleset_name] = ruleset
            
            self.logger.info(f"Loaded ruleset: {ruleset.name} v{ruleset.version}")
            return ruleset
            
        except Exception as e:
            self.logger.error(f"Failed to load ruleset {ruleset_name}: {e}, using fallback")
            return self._create_fallback_ruleset(ruleset_name)
    
    def _parse_ruleset_config(self, config: Dict[str, Any]) -> RuleSet:
        """Parse YAML configuration into RuleSet object"""
        ruleset = RuleSet(
            name=config['name'],
            version=config['version'],
            description=config.get('description', ''),
            default_workflow=config.get('default_workflow', 'general_analysis_workflow'),
            metadata=config.get('metadata', {})
        )
        
        # Parse root nodes
        for node_config in config.get('rules', []):
            node = self._parse_rule_node(node_config)
            ruleset.root_nodes.append(node)
        
        return ruleset
    
    def _parse_rule_node(self, config: Dict[str, Any]) -> RuleNode:
        """Parse rule node configuration"""
        node = RuleNode(
            node_id=config['id'],
            name=config['name'],
            operator=config.get('operator', 'AND'),
            workflow=config.get('workflow'),
            confidence_boost=config.get('confidence_boost', 0.0),
            actions=config.get('actions', [])
        )
        
        # Parse conditions
        for cond_config in config.get('conditions', []):
            condition = RuleCondition(
                field=cond_config['field'],
                operator=cond_config['operator'],
                value=cond_config['value'],
                weight=cond_config.get('weight', 1.0)
            )
            node.conditions.append(condition)
        
        # Parse children recursively
        for child_config in config.get('children', []):
            child = self._parse_rule_node(child_config)
            node.children.append(child)
        
        return node
    
    def evaluate_rules(self, ruleset_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate rules against context
        
        Args:
            ruleset_name: Name of ruleset to use
            context: Context for evaluation
            
        Returns:
            Evaluation results
        """
        if ruleset_name not in self.rulesets:
            self.load_rules(ruleset_name)
        
        ruleset = self.rulesets[ruleset_name]
        return ruleset.evaluate(context)
    
    @abc.abstractmethod
    def get_supported_rulesets(self) -> List[str]:
        """
        Get list of supported ruleset names
        
        Returns:
            List of ruleset names
        """
        pass
    
    def validate_ruleset(self, ruleset_name: str) -> Dict[str, Any]:
        """
        Validate ruleset configuration
        
        Args:
            ruleset_name: Name of ruleset to validate
            
        Returns:
            Validation results
        """
        validation_result = {
            'ruleset_name': ruleset_name,
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        try:
            if ruleset_name not in self.rulesets:
                self.load_rules(ruleset_name)
            
            ruleset = self.rulesets[ruleset_name]
            
            # Basic validation
            if not ruleset.root_nodes:
                validation_result['warnings'].append("No root nodes defined")
            
            # Validate each node
            for node in ruleset.root_nodes:
                node_validation = self._validate_node(node)
                if not node_validation['valid']:
                    validation_result['valid'] = False
                    validation_result['errors'].extend(node_validation['errors'])
                validation_result['warnings'].extend(node_validation['warnings'])
            
        except Exception as e:
            validation_result['valid'] = False
            validation_result['errors'].append(f"Validation failed: {e}")
        
        return validation_result
    
    def _validate_node(self, node: RuleNode) -> Dict[str, Any]:
        """Validate individual rule node"""
        validation = {
            'node_id': node.node_id,
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Check for required fields
        if not node.node_id:
            validation['valid'] = False
            validation['errors'].append("Node ID is required")
        
        if not node.name:
            validation['warnings'].append(f"Node {node.node_id} has no name")
        
        # Validate operator
        if node.operator not in ['AND', 'OR']:
            validation['valid'] = False
            validation['errors'].append(f"Invalid operator {node.operator} in node {node.node_id}")
        
        # Validate conditions
        for condition in node.conditions:
            if condition.operator not in ['eq', 'ne', 'gt', 'lt', 'ge', 'le', 'in', 'not_in', 'contains', 'regex']:
                validation['valid'] = False
                validation['errors'].append(f"Invalid condition operator {condition.operator} in node {node.node_id}")
        
        # Validate children recursively
        for child in node.children:
            child_validation = self._validate_node(child)
            if not child_validation['valid']:
                validation['valid'] = False
                validation['errors'].extend(child_validation['errors'])
            validation['warnings'].extend(child_validation['warnings'])
        
        return validation
    
    def _create_fallback_ruleset(self, ruleset_name: str) -> RuleSet:
        """Create a basic fallback ruleset for testing without YAML"""
        ruleset = RuleSet(
            name=ruleset_name,
            version='1.0.0-fallback',
            description='Fallback ruleset for testing',
            default_workflow='general_analysis_workflow'
        )
        
        # Create basic fraud detection rule
        fraud_node = RuleNode(
            node_id='fallback_fraud_detection',
            name='Fallback Fraud Detection',
            operator='AND',
            workflow='fraud_analysis_workflow',
            confidence_boost=0.3
        )
        fraud_node.conditions = [
            RuleCondition(field='fraud_keyword_count', operator='ge', value=2)
        ]
        
        # Create basic general analysis rule
        general_node = RuleNode(
            node_id='fallback_general_analysis',
            name='Fallback General Analysis',
            operator='AND',
            workflow='general_analysis_workflow',
            confidence_boost=0.1
        )
        general_node.conditions = [
            RuleCondition(field='document_length', operator='gt', value=10)
        ]
        
        ruleset.root_nodes = [fraud_node, general_node]
        self.rulesets[ruleset_name] = ruleset
        
        self.logger.info(f"Created fallback ruleset: {ruleset.name}")
        return ruleset