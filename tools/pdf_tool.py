"""
PDF Processing Tool for Safety Sigma 2.0

Wraps Safety Sigma 1.0 PDF extraction functionality with tool interface.
Maintains byte-for-byte compatibility while adding audit logging and validation.
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from .base_tool import BaseTool, ToolResult


class PDFTool(BaseTool):
    """
    PDF text extraction tool with Safety Sigma 1.0 compatibility
    
    Wraps the original PDF extraction functionality while providing:
    - Standardized tool interface
    - Comprehensive audit logging  
    - Source traceability tracking
    - File validation and error handling
    """
    
    name = "pdf_tool"
    version = "1.0.0"
    required_params = ["pdf_path"]
    allow_none_output = False
    
    def __init__(self, ss1_path: Optional[str] = None, **kwargs):
        """
        Initialize PDF tool with Safety Sigma 1.0 backend
        
        Args:
            ss1_path: Path to Safety Sigma 1.0 installation
            **kwargs: Additional base tool arguments
        """
        super().__init__(**kwargs)
        
        self.ss1_path = ss1_path or os.getenv('SS1_PATH', '../Desktop/safety_sigma/phase_1')
        self.ss1_path = Path(self.ss1_path).resolve()
        
        # Import Safety Sigma 1.0 processor
        self._ss1_processor = None
        self._import_ss1()
    
    def _import_ss1(self) -> None:
        """Import Safety Sigma 1.0 processor with error handling"""
        try:
            if str(self.ss1_path) not in sys.path:
                sys.path.insert(0, str(self.ss1_path))
            
            from safety_sigma_processor import SafetySigmaProcessor
            # Use mock API key since we only need PDF extraction
            self._ss1_processor = SafetySigmaProcessor(api_key="mock-key-for-pdf-only")
            
        except ImportError as e:
            raise ImportError(f"Cannot import Safety Sigma 1.0 from {self.ss1_path}: {e}")
    
    def _validate_inputs(self, inputs: Dict[str, Any], result: ToolResult) -> None:
        """
        Validate PDF file input parameters
        
        Args:
            inputs: Input parameters including pdf_path
            result: Result object for audit trail
        """
        super()._validate_inputs(inputs, result)
        
        pdf_path = Path(inputs['pdf_path'])
        
        # Check file exists
        if not pdf_path.exists():
            error_msg = f"PDF file not found: {pdf_path}"
            result.add_audit_entry(f"File validation failed: {error_msg}")
            raise FileNotFoundError(error_msg)
        
        # Check file extension
        if not pdf_path.suffix.lower() == '.pdf':
            result.add_audit_entry(f"Warning: File does not have .pdf extension: {pdf_path.suffix}")
        
        # Check file size (reasonable limits)
        file_size = pdf_path.stat().st_size
        max_size = int(os.getenv('SS2_MAX_PDF_SIZE_MB', '100')) * 1024 * 1024
        
        if file_size > max_size:
            error_msg = f"PDF file too large: {file_size / (1024*1024):.1f}MB > {max_size / (1024*1024)}MB"
            result.add_audit_entry(f"Size validation failed: {error_msg}")
            raise ValueError(error_msg)
        
        result.add_audit_entry(f"PDF validation passed: {pdf_path} ({file_size / 1024:.1f}KB)")
        
        # Store file metadata for audit trail
        result.metadata.update({
            'pdf_file_size': file_size,
            'pdf_file_path': str(pdf_path.resolve()),
            'pdf_file_name': pdf_path.name,
            'pdf_modified_time': pdf_path.stat().st_mtime,
        })

    def _validate_outputs(self, output: Any, result: ToolResult) -> None:
        """
        Validate extracted PDF text
        
        Args:
            output: Extracted text content
            result: Result object for audit trail
        """
        super()._validate_outputs(output, result)
        
        if not isinstance(output, str):
            error_msg = f"Expected string output, got {type(output)}"
            result.add_audit_entry(f"Output type validation failed: {error_msg}")
            raise ValueError(error_msg)
        
        # Check for minimum content
        if len(output.strip()) < 10:
            result.add_audit_entry(f"Warning: Very short text extracted ({len(output)} chars)")
        
        # Check for extraction issues
        if "Error" in output or "Exception" in output:
            result.add_audit_entry(f"Warning: Possible extraction errors in content")
        
        result.add_audit_entry(f"Text extraction validation passed: {len(output)} characters")
        
        # Store extraction metadata
        result.metadata.update({
            'extracted_text_length': len(output),
            'extracted_lines': output.count('\n') + 1,
            'extraction_quality_indicators': {
                'has_structured_content': bool('\n\n' in output),
                'has_page_breaks': bool('\f' in output),
                'character_diversity': len(set(output.lower())) / max(1, len(output)),
            }
        })

    def _validate_source_traceability(self, inputs: Dict[str, Any], output: Any, result: ToolResult) -> None:
        """
        Ensure extracted content can be traced back to source PDF
        
        Args:
            inputs: Input parameters 
            output: Extracted text
            result: Result object for audit trail
        """
        super()._validate_source_traceability(inputs, output, result)
        
        pdf_path = Path(inputs['pdf_path'])
        
        # Store comprehensive source traceability information
        result.metadata['source_traceability'] = {
            'source_file': str(pdf_path.resolve()),
            'source_file_hash': self._calculate_file_hash(pdf_path),
            'extraction_timestamp': result.metadata.get('extraction_timestamp'),
            'extraction_tool': f"{self.name} v{self.version}",
            'backend_processor': "safety_sigma_processor v1.0",
            'zero_inference_mode': self.zero_inference,
        }
        
        result.add_audit_entry("Source traceability information recorded")

    def _calculate_file_hash(self, file_path: Path) -> str:
        """
        Calculate hash of source file for integrity verification
        
        Args:
            file_path: Path to file
            
        Returns:
            File hash string
        """
        import hashlib
        
        try:
            hasher = hashlib.sha256()
            with open(file_path, 'rb') as f:
                # Read in chunks to handle large files
                for chunk in iter(lambda: f.read(8192), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()[:16]  # Truncate for audit logs
        except Exception:
            return "hash_unavailable"

    def _run(self, pdf_path: str, **kwargs) -> str:
        """
        Extract text from PDF using Safety Sigma 1.0 backend
        
        Args:
            pdf_path: Path to PDF file
            **kwargs: Additional parameters (ignored for compatibility)
            
        Returns:
            Extracted text content
        """
        if not self._ss1_processor:
            raise RuntimeError("Safety Sigma 1.0 processor not initialized")
        
        # Convert to string path for SS1 compatibility
        pdf_path_str = str(Path(pdf_path).resolve())
        
        # Use SS1 extraction method directly
        extracted_text = self._ss1_processor.extract_pdf_text(pdf_path_str)
        
        return extracted_text

    def _get_metadata(self, inputs: Dict[str, Any], output: Any) -> Dict[str, Any]:
        """
        Generate PDF-specific metadata for audit logging
        
        Args:
            inputs: Input parameters
            output: Extracted text
            
        Returns:
            Tool metadata with PDF-specific information
        """
        metadata = super()._get_metadata(inputs, output)
        
        metadata.update({
            "tool_specific": {
                "backend": "safety_sigma_processor",
                "pdf_processing": {
                    "file_path": inputs.get('pdf_path', 'unknown'),
                    "extraction_method": "PyPDF2",
                },
                "compatibility": {
                    "ss1_version": "1.0",
                    "maintains_byte_parity": True,
                }
            }
        })
        
        return metadata


class PDFToolError(Exception):
    """PDF tool specific exceptions"""
    pass