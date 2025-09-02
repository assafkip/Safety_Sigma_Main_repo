"""
Safety Sigma 2.0 Processor

Main processing class that routes between Safety Sigma 1.0 (Stage 0) 
and tool abstraction layer (Stage 1+) based on feature toggles.
"""

import os
import sys
from pathlib import Path
from typing import Optional

from safety_sigma import FEATURE_TOGGLES


class SafetySigmaProcessor:
    """
    Main processor class that provides unified interface across all stages
    
    Routes between:
    - Stage 0: Direct Safety Sigma 1.0 delegation (parity mode)
    - Stage 1+: Tool abstraction layer with orchestration
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize processor with appropriate backend
        
        Args:
            api_key: API key for AI services
        """
        self.api_key = api_key
        
        # Initialize appropriate backend based on feature toggles
        if FEATURE_TOGGLES['SS2_ENABLE_TOOLS']:
            self._init_stage1_processor()
        else:
            self._init_stage0_processor()
    
    def _init_stage0_processor(self) -> None:
        """Initialize Stage 0 processor (Safety Sigma 1.0 delegation)"""
        try:
            ss1_path = os.getenv('SS1_PATH', '../Desktop/safety_sigma/phase_1')
            ss1_path = str(Path(ss1_path).resolve())
            
            if ss1_path not in sys.path:
                sys.path.insert(0, ss1_path)
            
            from safety_sigma_processor import SafetySigmaProcessor as SS1Processor
            
            api_key = self.api_key or os.getenv('OPENAI_API_KEY', 'mock-key-for-testing')
            self._backend = SS1Processor(api_key=api_key)
            self._stage = "Stage 0: v1.0 Parity Mode"
            
        except ImportError as e:
            raise ImportError(f"Cannot import Safety Sigma 1.0 for Stage 0: {e}")
    
    def _init_stage1_processor(self) -> None:
        """Initialize Stage 1+ processor (tool abstraction or agent-based)"""
        try:
            # Check if advanced features are enabled (Stage 3+)
            if FEATURE_TOGGLES['SS2_ENHANCE_DOCS']:
                from agents.agent_processor import AgentProcessor
                
                self._backend = AgentProcessor(agent_type="enhanced")
                self._stage = "Stage 3: Advanced Decision Trees"
            # Check if basic agent processing is enabled (Stage 2+)
            elif FEATURE_TOGGLES['SS2_USE_AGENT']:
                from agents.agent_processor import AgentProcessor
                
                self._backend = AgentProcessor(agent_type="simple")
                self._stage = "Stage 2: Simple Agent Logic"
            else:
                # Stage 1: Tool abstraction only
                from orchestration import ToolOrchestrator
                
                self._backend = ToolOrchestrator()
                self._stage = "Stage 1: Tool Abstraction"
            
        except ImportError as e:
            raise ImportError(f"Cannot import Stage 1+ components: {e}")
    
    def extract_pdf_text(self, pdf_path: str) -> str:
        """
        Extract text from PDF file
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extracted text content
        """
        if FEATURE_TOGGLES['SS2_ENABLE_TOOLS']:
            # Stage 1+: Use tool abstraction
            from tools import PDFTool
            
            pdf_tool = PDFTool()
            result = pdf_tool.execute(pdf_path=pdf_path)
            
            if not result.success:
                raise RuntimeError(f"PDF extraction failed: {result.error}")
            
            return result.data
        else:
            # Stage 0: Direct SS1 delegation
            return self._backend.extract_pdf_text(pdf_path)
    
    def read_instruction_file(self, md_path: str) -> str:
        """
        Read instruction file
        
        Args:
            md_path: Path to markdown instruction file
            
        Returns:
            Instruction content
        """
        if FEATURE_TOGGLES['SS2_ENABLE_TOOLS']:
            # Stage 1+: Enhanced file reading (could add validation)
            try:
                with open(md_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Basic validation
                if len(content.strip()) < 10:
                    raise ValueError(f"Instruction file too short: {len(content)} characters")
                
                return content
                
            except Exception as e:
                raise Exception(f"Error reading instruction file: {str(e)}")
        else:
            # Stage 0: Direct SS1 delegation  
            return self._backend.read_instruction_file(md_path)
    
    def process_report(self, instructions: str, report_content: str) -> str:
        """
        Process report with AI analysis
        
        Args:
            instructions: Processing instructions
            report_content: Source content to analyze
            
        Returns:
            Analysis result
        """
        if FEATURE_TOGGLES['SS2_ENABLE_TOOLS']:
            # Stage 1+: Use tool abstraction
            from tools import ExtractionTool
            
            extraction_tool = ExtractionTool()
            result = extraction_tool.execute(
                instructions=instructions,
                text_content=report_content
            )
            
            if not result.success:
                raise RuntimeError(f"Report processing failed: {result.error}")
            
            return result.data
        else:
            # Stage 0: Direct SS1 delegation
            return self._backend.process_report(instructions, report_content)
    
    def save_results(self, results: str, output_path: str) -> None:
        """
        Save results to file
        
        Args:
            results: Analysis results to save
            output_path: Output directory path
        """
        if FEATURE_TOGGLES['SS2_ENABLE_TOOLS']:
            # Stage 1+: Use backend's save_results (handles both orchestrator and agent)
            return self._backend.save_results(results, output_path)
        else:
            # Stage 0: Direct SS1 delegation
            return self._backend.save_results(results, output_path)
    
    def get_stage_info(self) -> dict:
        """
        Get information about current processing stage
        
        Returns:
            Dictionary with stage information
        """
        return {
            "stage": self._stage,
            "backend_type": type(self._backend).__name__,
            "feature_toggles": FEATURE_TOGGLES,
            "tools_enabled": FEATURE_TOGGLES['SS2_ENABLE_TOOLS'],
        }