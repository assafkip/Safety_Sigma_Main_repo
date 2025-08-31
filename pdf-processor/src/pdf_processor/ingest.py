from typing import List, Tuple

class Span:
    def __init__(self, text: str, start: int, end: int):
        self.text = text
        self.start = start
        self.end = end

def pdf_to_text_with_offsets(path: str) -> List[Span]:
    # Placeholder for PDF processing logic
    # This function should read a PDF file and extract text along with its offsets.
    # For now, returning an empty list.
    return []