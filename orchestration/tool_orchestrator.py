"""
Tool Orchestrator for Safety Sigma 2.0

Manages sequential execution of tools with comprehensive audit logging.
Maintains compatibility with Safety Sigma 1.0 processing pipeline.
"""

import json
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Type
import os

from tools.base_tool import BaseTool, ToolResult
from tools.pdf_tool import PDFTool
from tools.extraction_tool import ExtractionTool


@dataclass
class OrchestrationStep:
    """
    Individual step in orchestration pipeline
    """
    step_name: str
    tool_class: Type[BaseTool]
    input_mapping: Dict[str, str]  # Map orchestrator inputs to tool inputs
    output_key: str  # Key to store output in orchestration context
    required: bool = True
    depends_on: List[str] = field(default_factory=list)  # Dependencies on previous steps


@dataclass
class OrchestrationResult:
    """
    Complete orchestration execution result
    """
    success: bool
    orchestration_id: str
    start_time: float
    end_time: float
    duration_ms: float
    steps_executed: int
    steps_successful: int  
    context: Dict[str, Any] = field(default_factory=dict)
    step_results: Dict[str, ToolResult] = field(default_factory=dict)
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class ToolOrchestrator:
    """
    Orchestrates sequential execution of tools with audit logging
    
    Provides:
    - Sequential tool execution with dependency management
    - Comprehensive audit trail across all tools
    - Context passing between tools
    - Error handling and recovery
    - Pipeline validation and compliance checking
    """
    
    def __init__(self, audit_dir: Optional[str] = None):
        """
        Initialize tool orchestrator
        
        Args:
            audit_dir: Directory for audit logs (default: from env)
        """
        self.audit_dir = Path(audit_dir or os.getenv('SS2_AUDIT_DIR', 'audit_logs'))
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        
        # Define Safety Sigma processing pipeline
        self.ss_pipeline = self._define_safety_sigma_pipeline()
    
    def _define_safety_sigma_pipeline(self) -> List[OrchestrationStep]:
        """
        Define the standard Safety Sigma processing pipeline
        
        Returns:
            List of orchestration steps matching SS1 behavior
        """
        return [
            OrchestrationStep(
                step_name="pdf_extraction",
                tool_class=PDFTool,
                input_mapping={"pdf_path": "pdf_file"},
                output_key="extracted_text",
                required=True,
            ),
            OrchestrationStep(
                step_name="ai_analysis", 
                tool_class=ExtractionTool,
                input_mapping={
                    "instructions": "instructions",
                    "text_content": "extracted_text"
                },
                output_key="analysis_result",
                required=True,
                depends_on=["pdf_extraction"],
            ),
        ]
    
    def execute_safety_sigma_pipeline(
        self, 
        pdf_file: str, 
        instructions: str,
        output_dir: Optional[str] = None,
        simulate: bool = False,
    ) -> OrchestrationResult:
        """
        Execute the complete Safety Sigma processing pipeline
        
        Args:
            pdf_file: Path to PDF file
            instructions: Processing instructions
            output_dir: Output directory for results
            simulate: Run in simulation mode
            
        Returns:
            OrchestrationResult with complete execution information
        """
        orchestration_context = {
            "pdf_file": pdf_file,
            "instructions": instructions,
            "output_dir": output_dir or ".",
            "simulate": simulate,
        }
        
        return self.execute_pipeline(self.ss_pipeline, orchestration_context)
    
    def execute_pipeline(
        self, 
        pipeline: List[OrchestrationStep], 
        context: Dict[str, Any]
    ) -> OrchestrationResult:
        """
        Execute a tool pipeline with full audit logging
        
        Args:
            pipeline: List of orchestration steps
            context: Initial execution context
            
        Returns:
            OrchestrationResult with execution details
        """
        orchestration_id = str(uuid.uuid4())
        start_time = time.time()
        
        result = OrchestrationResult(
            success=False,
            orchestration_id=orchestration_id,
            start_time=start_time,
            end_time=0,
            duration_ms=0,
            steps_executed=0,
            steps_successful=0,
            context=context.copy(),
        )
        
        try:
            self._log_orchestration_start(orchestration_id, pipeline, context)
            
            # Execute each step in sequence
            for step in pipeline:
                result.steps_executed += 1
                
                # Check dependencies
                if not self._check_step_dependencies(step, result.step_results):
                    error_msg = f"Step {step.step_name} dependencies not satisfied: {step.depends_on}"
                    result.error = error_msg
                    self._log_orchestration_error(orchestration_id, error_msg)
                    break
                
                # Execute step
                step_result = self._execute_step(step, result.context, orchestration_id)
                result.step_results[step.step_name] = step_result
                
                if step_result.success:
                    result.steps_successful += 1
                    # Update context with step output
                    result.context[step.output_key] = step_result.data
                    self._log_step_success(orchestration_id, step.step_name, step_result)
                else:
                    # Handle step failure
                    error_msg = f"Step {step.step_name} failed: {step_result.error}"
                    result.error = error_msg
                    self._log_step_failure(orchestration_id, step.step_name, step_result)
                    
                    if step.required:
                        break  # Stop pipeline on required step failure
            
            # Check overall success
            result.success = (result.steps_successful == len(pipeline))
            
        except Exception as e:
            result.error = f"Orchestration error: {str(e)}"
            self._log_orchestration_error(orchestration_id, result.error)
            
        finally:
            end_time = time.time()
            result.end_time = end_time
            result.duration_ms = (end_time - start_time) * 1000.0
            
            # Generate comprehensive metadata
            result.metadata = self._generate_orchestration_metadata(pipeline, result)
            
            # Write final orchestration audit record
            self._write_orchestration_audit(result)
        
        return result
    
    def _check_step_dependencies(
        self, 
        step: OrchestrationStep, 
        completed_steps: Dict[str, ToolResult]
    ) -> bool:
        """
        Check if step dependencies are satisfied
        
        Args:
            step: Step to check
            completed_steps: Results from completed steps
            
        Returns:
            True if dependencies satisfied
        """
        return all(
            dep in completed_steps and completed_steps[dep].success
            for dep in step.depends_on
        )
    
    def _execute_step(
        self, 
        step: OrchestrationStep, 
        context: Dict[str, Any],
        orchestration_id: str
    ) -> ToolResult:
        """
        Execute a single orchestration step
        
        Args:
            step: Step to execute
            context: Current orchestration context  
            orchestration_id: Orchestration run ID
            
        Returns:
            ToolResult from step execution
        """
        # Map inputs from context to tool parameters
        tool_inputs = {}
        for tool_param, context_key in step.input_mapping.items():
            if context_key in context:
                tool_inputs[tool_param] = context[context_key]
            else:
                raise ValueError(f"Required context key '{context_key}' not found for step {step.step_name}")
        
        # Add orchestration context
        tool_inputs['orchestration_id'] = orchestration_id
        tool_inputs['step_name'] = step.step_name
        
        # Add simulation mode if specified
        if context.get('simulate', False):
            tool_inputs['simulate'] = True
        
        # Initialize and execute tool
        tool = step.tool_class()
        result = tool.execute(**tool_inputs)
        
        # Add orchestration metadata to result
        result.metadata['orchestration'] = {
            'orchestration_id': orchestration_id,
            'step_name': step.step_name,
            'step_index': context.get('current_step_index', 0),
        }
        
        return result
    
    def save_results(self, result: OrchestrationResult, output_dir: str) -> str:
        """
        Save orchestration results to file (compatibility with SS1)
        
        Args:
            result: Orchestration result to save
            output_dir: Output directory
            
        Returns:
            Path to saved results file
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Generate timestamp for filename (SS1 compatibility)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"safety_sigma_results_{timestamp}.md"
        full_path = output_path / filename
        
        # Extract final analysis result
        analysis_result = result.context.get('analysis_result', 'No analysis result available')
        
        # Create SS1-compatible output format
        output_content = f"""# Safety Sigma Detection Rules Analysis
Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}

{analysis_result}

---
## Orchestration Metadata (Safety Sigma 2.0)
- Orchestration ID: {result.orchestration_id}
- Processing time: {result.duration_ms:.1f}ms
- Steps executed: {result.steps_executed}/{len(self.ss_pipeline)}
- Tool abstraction: ENABLED
"""
        
        # Write results file
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(output_content)
        
        return str(full_path)
    
    def _generate_orchestration_metadata(
        self, 
        pipeline: List[OrchestrationStep],
        result: OrchestrationResult
    ) -> Dict[str, Any]:
        """Generate comprehensive orchestration metadata"""
        return {
            "pipeline_definition": [
                {
                    "step_name": step.step_name,
                    "tool_class": step.tool_class.__name__,
                    "required": step.required,
                    "depends_on": step.depends_on,
                }
                for step in pipeline
            ],
            "execution_summary": {
                "total_steps": len(pipeline),
                "steps_executed": result.steps_executed,
                "steps_successful": result.steps_successful,
                "success_rate": result.steps_successful / max(1, result.steps_executed),
            },
            "performance": {
                "total_duration_ms": result.duration_ms,
                "average_step_duration_ms": result.duration_ms / max(1, result.steps_executed),
            },
            "compliance": {
                "audit_logging": True,
                "tool_abstraction": True,
                "ss1_compatibility": True,
            }
        }
    
    # ---------- Audit Logging Methods ----------
    
    def _log_orchestration_start(
        self, 
        orchestration_id: str, 
        pipeline: List[OrchestrationStep],
        context: Dict[str, Any]
    ) -> None:
        """Log orchestration start"""
        log_entry = {
            "event": "orchestration_start",
            "orchestration_id": orchestration_id,
            "timestamp": time.time(),
            "pipeline_steps": len(pipeline),
            "context_keys": list(context.keys()),
        }
        self._write_audit_log(log_entry)
    
    def _log_step_success(
        self, 
        orchestration_id: str, 
        step_name: str, 
        result: ToolResult
    ) -> None:
        """Log successful step execution"""
        log_entry = {
            "event": "step_success",
            "orchestration_id": orchestration_id,
            "step_name": step_name,
            "timestamp": time.time(),
            "execution_time_ms": result.execution_time_ms,
        }
        self._write_audit_log(log_entry)
    
    def _log_step_failure(
        self, 
        orchestration_id: str, 
        step_name: str, 
        result: ToolResult
    ) -> None:
        """Log failed step execution"""
        log_entry = {
            "event": "step_failure",
            "orchestration_id": orchestration_id,
            "step_name": step_name,
            "timestamp": time.time(),
            "error": result.error,
        }
        self._write_audit_log(log_entry)
    
    def _log_orchestration_error(self, orchestration_id: str, error: str) -> None:
        """Log orchestration-level error"""
        log_entry = {
            "event": "orchestration_error",
            "orchestration_id": orchestration_id,
            "timestamp": time.time(),
            "error": error,
        }
        self._write_audit_log(log_entry)
    
    def _write_audit_log(self, log_entry: Dict[str, Any]) -> None:
        """Write audit log entry"""
        try:
            # Write to daily orchestration log
            daily_log = self.audit_dir / f"orchestration_{time.strftime('%Y-%m-%d')}.jsonl"
            with open(daily_log, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
        except Exception:
            pass  # Don't fail orchestration due to audit logging issues
    
    def _write_orchestration_audit(self, result: OrchestrationResult) -> None:
        """Write comprehensive orchestration audit record"""
        try:
            audit_record = {
                "orchestration_id": result.orchestration_id,
                "start_time": result.start_time,
                "end_time": result.end_time, 
                "duration_ms": result.duration_ms,
                "success": result.success,
                "steps_executed": result.steps_executed,
                "steps_successful": result.steps_successful,
                "error": result.error,
                "metadata": result.metadata,
                "timestamp_iso": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(result.start_time)),
            }
            
            # Write individual orchestration record
            audit_file = self.audit_dir / f"orchestration_{result.orchestration_id}.json"
            audit_file.write_text(json.dumps(audit_record, indent=2, ensure_ascii=False), encoding='utf-8')
            
        except Exception:
            pass  # Don't fail orchestration due to audit logging issues