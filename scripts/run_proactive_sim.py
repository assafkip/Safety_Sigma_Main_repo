#!/usr/bin/env python3
"""
Safety Sigma Proactive Simulation v0.4
Narrative-aware expansion with EDAP (Evidence-Driven Auto-Promotion)
"""
import json
import argparse
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.proactive.narrative_expander import extract_evidence, Evidence

def extract_sentences_from_text(text: str) -> List[Evidence]:
    """Extract sentences with IDs for evidence analysis"""
    import re
    
    # Simple sentence splitting
    sentences = re.split(r'[.!?]+', text)
    evidence_list = []
    
    for i, sent in enumerate(sentences):
        sent = sent.strip()
        if len(sent) > 10:  # Skip very short fragments
            # Generate simple span IDs for content that might be indicators
            spans = []
            if any(pattern in sent.lower() for pattern in ['$', 'whatsapp', 'telegram', 'void', '.com']):
                spans.append(f"span_{i:03d}")
            
            evidence_list.append(Evidence(
                sent_id=f"S{i:03d}",
                text=sent,
                spans=spans
            ))
    
    return evidence_list

def load_sentences_from_json(json_path: Path) -> List[Evidence]:
    """Load sentences from JSON file"""
    data = json.loads(json_path.read_text(encoding="utf-8"))
    return [Evidence(**d) for d in data]

def main():
    parser = argparse.ArgumentParser(description="Run proactive narrative expansion simulation")
    parser.add_argument("--sentences", help="JSON list of {sent_id,text,spans}")
    parser.add_argument("--text", help="Plain text file to analyze")
    parser.add_argument("--out", default="artifacts/proactive/expansions.json", help="Output JSON file")
    
    args = parser.parse_args()
    
    # Load evidence sentences
    if args.sentences and Path(args.sentences).exists():
        print(f"Loading sentences from {args.sentences}")
        sentences = load_sentences_from_json(Path(args.sentences))
    elif args.text and Path(args.text).exists():
        print(f"Extracting sentences from {args.text}")
        text_content = Path(args.text).read_text(encoding="utf-8")
        sentences = extract_sentences_from_text(text_content)
    else:
        # Create sample sentences for demonstration
        print("Using sample narrative sentences for demonstration")
        sentences = [
            Evidence(
                sent_id="S001",
                text="Victims are redirected to WhatsApp or Telegram messaging apps.",
                spans=["span_redirect"]
            ),
            Evidence(
                sent_id="S002", 
                text="The scammer requests a VOID check with a 3-4 digit code written in the memo.",
                spans=["span_void", "span_memo"]
            ),
            Evidence(
                sent_id="S003",
                text="Fraudulent domains include paypaI.com, paypai.com, and paypa1.com to mimic PayPal.",
                spans=["span_domains"]
            ),
            Evidence(
                sent_id="S004",
                text="The scheme involves such as gift cards, wire transfers, or cryptocurrency payments.",
                spans=["span_payments"]
            )
        ]
    
    print(f"Analyzing {len(sentences)} sentences for evidence patterns...")
    
    # Extract expansions using EDAP
    expansions = extract_evidence(sentences)
    
    print(f"Found {len(expansions)} potential expansions:")
    for exp in expansions:
        status_icon = "✅" if exp.status == "ready" else "⚠️"
        print(f"  {status_icon} {exp.operator}: {exp.pattern} ({exp.status})")
    
    # Save results
    output_path = Path(args.out)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert to serializable format
    expansion_data = []
    for exp in expansions:
        expansion_data.append({
            "pattern": exp.pattern,
            "kind": exp.kind,
            "parent_spans": exp.parent_spans,
            "operator": exp.operator,
            "evidence_sent_id": exp.evidence_sent_id,
            "evidence_quote": exp.evidence_quote,
            "status": exp.status
        })
    
    output_json = {
        "schema_version": "v0.4",
        "processing_mode": "proactive_edap",
        "total_sentences": len(sentences),
        "total_expansions": len(expansions),
        "ready_expansions": len([e for e in expansions if e.status == "ready"]),
        "expansions": expansion_data,
        "edap_criteria": {
            "E1_ALT_ENUM": len([e for e in expansions if e.operator == "ALT_ENUM"]),
            "E2_RANGE_DIGITS": len([e for e in expansions if e.operator == "RANGE_DIGITS"]),
            "E3_LITERAL_SET": len([e for e in expansions if e.operator == "LITERAL_SET"])
        }
    }
    
    output_path.write_text(json.dumps(output_json, indent=2, ensure_ascii=False))
    print(f"✅ Wrote {args.out} with {len(expansions)} expansions")
    
    # Summary
    ready_count = len([e for e in expansions if e.status == "ready"])
    advisory_count = len([e for e in expansions if e.status == "advisory"])
    print(f"📊 Summary: {ready_count} ready, {advisory_count} advisory")

if __name__ == "__main__":
    main()