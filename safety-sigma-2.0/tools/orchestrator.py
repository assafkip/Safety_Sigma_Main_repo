from dataclasses import dataclass
from .pdf_tool import PDFTool
from .extraction_tool import ExtractionTool

@dataclass
class PipelineResult:
    success: bool
    data: str = ""
    error: str = ""

class ToolOrchestrator:
    def __init__(self):
        self.pdf = PDFTool()
        self.extract = ExtractionTool()

    def execute_safety_sigma_pipeline(self, pdf_file: str, instructions: str, simulate: bool = False) -> PipelineResult:
        try:
            pdf_res = self.pdf.execute(pdf_path=pdf_file, simulate=simulate)
            text = pdf_res.data or ("Mock PDF extracted text" if simulate else "")
            x_res = self.extract.execute(instructions=instructions, text_content=text, simulate=simulate)
            return PipelineResult(success=x_res.success, data=x_res.data)
        except Exception as e:
            return PipelineResult(success=False, error=str(e))