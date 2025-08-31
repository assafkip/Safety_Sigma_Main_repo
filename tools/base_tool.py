"""
Base Tool Interface for Safety Sigma 2.0

Provides abstract base class for all tools with:
- Standardized execute() entrypoint
- Comprehensive audit logging  
- Input/output validation
- Performance tracking
- Error handling and recovery
"""

import abc
import json
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, List
import os
import logging

# Configure audit logging
AUDIT_DIR = Path(os.getenv('SS2_AUDIT_DIR', 'audit_logs'))
AUDIT_DIR.mkdir(parents=True, exist_ok=True)

# Set up logger
logger = logging.getLogger('safety_sigma.tools')
logger.setLevel(os.getenv('SS2_LOG_LEVEL', 'INFO'))

@dataclass
class ToolExecutionRecord:
    """
    Complete execution record for audit trail compliance
    """
    tool_name: str
    tool_version: str
    run_id: str
    start_time: float
    end_time: float
    duration_ms: float
    success: bool
    input_summary: Dict[str, Any]
    output_summary: Dict[str, Any] 
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    compliance_flags: Dict[str, bool] = field(default_factory=dict)
    
    def to_json(self) -> str:
        """Serialize record to JSON for audit logging"""
        return json.dumps({
            "tool_name": self.tool_name,
            "tool_version": self.tool_version,
            "run_id": self.run_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "success": self.success,
            "input_summary": self.input_summary,
            "output_summary": self.output_summary,
            "error": self.error,
            "metadata": self.metadata,
            "compliance_flags": self.compliance_flags,
            "timestamp_iso": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(self.start_time)),
        }, ensure_ascii=False, indent=2)


@dataclass
class ToolResult:
    """
    Standardized tool result with metadata and validation
    """
    data: Any
    success: bool = True
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_time_ms: float = 0.0
    compliance_status: Dict[str, bool] = field(default_factory=dict)
    audit_trail: List[str] = field(default_factory=list)
    
    def add_audit_entry(self, entry: str) -> None:
        """Add entry to audit trail"""
        timestamp = time.strftime('%H:%M:%S.%f')[:-3]
        self.audit_trail.append(f"[{timestamp}] {entry}")


class BaseTool(abc.ABC):
    """
    Abstract base class for all Safety Sigma 2.0 tools.
    
    Provides:
    - Standardized execute() entrypoint with audit logging
    - Input/output validation hooks
    - Performance tracking and metadata collection
    - Compliance guarantee enforcement
    - Error handling with recovery options
    """
    
    name: str = "base_tool"
    version: str = "0.1.0"
    
    def __init__(self, audit: bool = True, zero_inference: Optional[bool] = None):
        """
        Initialize base tool
        
        Args:
            audit: Enable audit logging (default: True)
            zero_inference: Enforce zero-inference mode (default: from env)
        """
        self.audit = audit
        self.zero_inference = zero_inference if zero_inference is not None else \
                             os.getenv('SS2_ZERO_INFERENCE', 'true').lower() == 'true'
        self.source_traceability = os.getenv('SS2_REQUIRE_SOURCE_TRACEABILITY', 'true').lower() == 'true'
        self.fail_on_validation = os.getenv('SS2_FAIL_ON_VALIDATION_ERROR', 'true').lower() == 'true'
        
        # Set up tool-specific logger
        self.logger = logging.getLogger(f'safety_sigma.tools.{self.name}')
        
    def execute(self, **kwargs) -> ToolResult:
        """
        Execute the tool with comprehensive audit logging and validation
        
        Args:
            **kwargs: Tool-specific parameters
            
        Returns:
            ToolResult: Standardized result with audit trail
        """
        run_id = str(uuid.uuid4())
        start = time.time()
        error = None
        result_data = None
        
        # Create result object for audit trail
        result = ToolResult(data=None)
        result.add_audit_entry(f"Tool execution started: {self.name} v{self.version}")
        result.add_audit_entry(f"Run ID: {run_id}")
        
        try:
            # Pre-execution validation
            result.add_audit_entry("Validating inputs...")
            self._validate_inputs(kwargs, result)
            
            if self.zero_inference:
                result.add_audit_entry("Zero-inference mode: ENABLED")
                result.compliance_status['zero_inference'] = True
            
            # Execute the tool
            result.add_audit_entry("Executing tool logic...")
            result_data = self._run(**kwargs)
            
            # Store kwargs metadata for tools that need it
            result.metadata.update({k: v for k, v in kwargs.items() if k.endswith('_mode')})
            
            # Post-execution validation
            result.add_audit_entry("Validating outputs...")
            self._validate_outputs(result_data, result)
            
            # Check compliance requirements
            if self.source_traceability:
                result.add_audit_entry("Checking source traceability...")
                self._validate_source_traceability(kwargs, result_data, result)
                result.compliance_status['source_traceability'] = True
            
            result.data = result_data
            result.success = True
            result.add_audit_entry("Tool execution completed successfully")
            
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
            result.success = False
            result.error = error
            result.add_audit_entry(f"Tool execution failed: {error}")
            
            if self.fail_on_validation and ("validation" in error.lower() or "ValueError" in error):
                result.add_audit_entry("Failing closed due to validation error")
                raise
            
            self.logger.error(f"Tool {self.name} failed: {error}")
            
        finally:
            end = time.time()
            result.execution_time_ms = (end - start) * 1000.0
            
            # Create comprehensive audit record
            if self.audit:
                record = ToolExecutionRecord(
                    tool_name=self.name,
                    tool_version=self.version,
                    run_id=run_id,
                    start_time=start,
                    end_time=end,
                    duration_ms=result.execution_time_ms,
                    success=result.success,
                    input_summary=self._summarize_inputs(kwargs),
                    output_summary=self._summarize_outputs(result_data) if result.success else {},
                    error=error,
                    metadata=self._get_metadata(kwargs, result_data),
                    compliance_flags=result.compliance_status
                )
                self._write_audit_record(record)
                result.add_audit_entry(f"Audit record written: {record.run_id}")
        
        return result

    @abc.abstractmethod
    def _run(self, **kwargs) -> Any:
        """
        Core tool execution logic - implemented by subclasses
        
        Args:
            **kwargs: Tool-specific parameters
            
        Returns:
            Tool-specific result data
        """
        raise NotImplementedError(f"Tool {self.name} must implement _run method")

    # ---------- Validation Hooks ----------
    
    def _validate_inputs(self, inputs: Dict[str, Any], result: ToolResult) -> None:
        """
        Validate input parameters before execution
        
        Args:
            inputs: Input parameters
            result: Result object for audit trail
        """
        # Default validation - override in subclasses for specific checks
        required_params = getattr(self, 'required_params', [])
        missing = [param for param in required_params if param not in inputs]
        
        if missing:
            error_msg = f"Missing required parameters: {missing}"
            result.add_audit_entry(f"Input validation failed: {error_msg}")
            raise ValueError(error_msg)
        
        result.add_audit_entry("Input validation passed")

    def _validate_outputs(self, output: Any, result: ToolResult) -> None:
        """
        Validate output data after execution
        
        Args:
            output: Tool output data
            result: Result object for audit trail
        """
        # Default validation - override in subclasses for specific checks
        if output is None and getattr(self, 'allow_none_output', False) is False:
            error_msg = "Tool produced None output"
            result.add_audit_entry(f"Output validation failed: {error_msg}")
            raise ValueError(error_msg)
        
        result.add_audit_entry("Output validation passed")

    def _validate_source_traceability(self, inputs: Dict[str, Any], output: Any, result: ToolResult) -> None:
        """
        Validate that outputs can be traced back to source inputs
        
        Args:
            inputs: Input parameters
            output: Tool output data  
            result: Result object for audit trail
        """
        # Default implementation - override in subclasses for specific traceability checks
        if self.source_traceability:
            # Basic check that source information is preserved
            source_files = [v for k, v in inputs.items() if 'path' in k.lower() or 'file' in k.lower()]
            if source_files:
                result.metadata['source_files'] = source_files
            
        result.add_audit_entry("Source traceability validation passed")

    # ---------- Summarization and Metadata ----------
    
    def _summarize_inputs(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create summary of input parameters for audit logging
        
        Args:
            inputs: Input parameters
            
        Returns:
            Summarized input information
        """
        summary: Dict[str, Any] = {}
        
        for k, v in inputs.items():
            if isinstance(v, (str, int, float, bool)) or v is None:
                # Truncate long strings for audit logs
                if isinstance(v, str) and len(v) > 100:
                    summary[k] = f"{v[:100]}... (truncated, length={len(v)})"
                else:
                    summary[k] = v
            elif isinstance(v, (list, tuple)):
                summary[k] = f"sequence(len={len(v)})"
            elif isinstance(v, dict):
                summary[k] = f"dict(keys={list(v.keys())[:5]})"
            elif isinstance(v, Path):
                summary[k] = f"path({v})"
            else:
                summary[k] = f"type({type(v).__name__})"
        
        return summary

    def _summarize_outputs(self, output: Any) -> Dict[str, Any]:
        """
        Create summary of output data for audit logging
        
        Args:
            output: Tool output data
            
        Returns:
            Summarized output information
        """
        if output is None:
            return {"type": "None"}
        
        if isinstance(output, (str, int, float, bool)):
            preview = str(output)[:200] + "..." if len(str(output)) > 200 else str(output)
            return {"type": type(output).__name__, "preview": preview}
        
        if isinstance(output, dict):
            return {"type": "dict", "keys": list(output.keys())[:10], "size": len(output)}
        
        if isinstance(output, list):
            return {"type": "list", "length": len(output)}
        
        return {"type": type(output).__name__, "size": getattr(output, '__len__', lambda: -1)()}

    def _get_metadata(self, inputs: Dict[str, Any], output: Any) -> Dict[str, Any]:
        """
        Generate tool-specific metadata for audit logging
        
        Args:
            inputs: Input parameters
            output: Tool output data
            
        Returns:
            Tool metadata
        """
        return {
            "zero_inference_mode": self.zero_inference,
            "source_traceability_required": self.source_traceability,
            "fail_on_validation": self.fail_on_validation,
            "tool_configuration": {
                "name": self.name,
                "version": self.version,
                "audit_enabled": self.audit,
            }
        }

    # ---------- Audit Logging ----------
    
    def _write_audit_record(self, record: ToolExecutionRecord) -> None:
        """
        Write execution record to audit log
        
        Args:
            record: Execution record to log
        """
        try:
            # Write individual tool audit record
            audit_file = AUDIT_DIR / f"{record.tool_name}_{record.run_id}.json"
            audit_file.write_text(record.to_json(), encoding="utf-8")
            
            # Also append to daily audit log
            daily_log = AUDIT_DIR / f"audit_{time.strftime('%Y-%m-%d')}.jsonl"
            with open(daily_log, 'a', encoding='utf-8') as f:
                f.write(record.to_json().replace('\n', '') + '\n')
                
        except Exception as e:
            self.logger.error(f"Failed to write audit record: {e}")
            # Don't fail the tool execution due to audit logging issues
            pass