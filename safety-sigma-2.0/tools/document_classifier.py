import re

EMAIL_RX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PHONE_RX = re.compile(
    r"(?:(?<!\d)\d{3}[-.\s]\d{4}(?!\d))|(?:\+?\d{1,2}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]\d{4})"
)

class DocumentClassifier:
    def __init__(self):
        pass
    
    def _has_emails(self, text: str) -> bool:
        return EMAIL_RX.search(text or "") is not None

    def _has_phone_numbers(self, text: str) -> bool:
        return PHONE_RX.search(text or "") is not None
    
    def _has_headers(self, text: str) -> bool:
        """Check if document has header structures"""
        return bool(re.search(r'#+\s+|^[A-Z][^\n]*:$', text or "", re.MULTILINE))
    
    def _has_lists(self, text: str) -> bool:
        """Check if document has list structures"""
        return bool(re.search(r'^\s*[-*+]\s+|^\s*\d+\.\s+', text or "", re.MULTILINE))
    
    def analyze_document_context(self, document_content: str, instructions: str = "", pdf_file: str = "", **kwargs):
        """Create analysis context from document inputs for rule evaluation"""
        context = {
            # Basic document characteristics
            'document_length': len(document_content),
            'word_count': len(document_content.split()),
            'has_pdf_file': bool(pdf_file),
            
            # Structure indicators
            'has_headers': self._has_headers(document_content),
            'has_lists': self._has_lists(document_content),
            'has_emails': self._has_emails(document_content),
            'has_phone_numbers': self._has_phone_numbers(document_content),
            
            # Keyword analysis placeholders
            'fraud_keyword_count': 0,
            'fraud_keyword_density': 0.0,
            
            # Instruction analysis
            'instructions_mention_fraud': 'fraud' in instructions.lower() if instructions else False,
        }
        
        return context