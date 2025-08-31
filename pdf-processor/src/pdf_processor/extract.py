def extract_amounts(text: str) -> List[Span]:
    import re
    from typing import List

    # Regular expression to find amounts (e.g., $100, €200.50)
    amount_pattern = r'(\$[0-9,]+(\.[0-9]{2})?|\€[0-9,]+(\.[0-9]{2})?)'
    matches = re.finditer(amount_pattern, text)

    spans = []
    for match in matches:
        start, end = match.span()
        spans.append(Span(text=match.group(), start=start, end=end))

    return spans