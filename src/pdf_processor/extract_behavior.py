import re
from pathlib import Path
import json
from src.pdf_processor.ir import make_behavior

# Naive patterns; real impl would use PDF spans
BEHAVIOR_PATTERNS = {
    "redirect": r"redirected to (WhatsApp|Telegram|Signal)",
    "spoof": r"spoof(ed|ing) caller ID",
    "urgency": r"(urgent|immediate action)",
    "payment": r"(gift cards?|wire transfers?|crypto(?:currency)?)"
}

def extract_behaviors(text: str, report_id="R1") -> list[dict]:
    """Extract literal behavioral phrases from text with zero inference."""
    results=[]
    for cat, pat in BEHAVIOR_PATTERNS.items():
        for m in re.finditer(pat, text, flags=re.IGNORECASE):
            span_id=f"{cat}_{m.start()}"
            results.append(make_behavior(m.group(0), cat, report_id, span_id))
    return results

if __name__=="__main__":
    sample="The scam redirected to WhatsApp and demanded gift cards. Caller ID was spoofed with urgency."
    behs=extract_behaviors(sample)
    print(json.dumps(behs, indent=2))