from typing import List

class Span:
    def __init__(self, text: str, start: int, end: int):
        self.text = text
        self.start = start
        self.end = end

class IR:
    def __init__(self, span: Span):
        self.span = span

def to_ir_objects(spans: List[Span]) -> List[IR]:
    return [IR(span) for span in spans]