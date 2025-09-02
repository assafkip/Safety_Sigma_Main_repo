from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple

@dataclass
class Evidence:
    sent_id: str
    text: str
    spans: List[str]  # span_ids present in the sentence

@dataclass
class Expansion:
    pattern: str
    kind: str
    parent_spans: List[str]
    operator: str        # ALT_ENUM | RANGE_DIGITS | LITERAL_SET
    evidence_sent_id: str
    evidence_quote: str
    status: str          # "ready" | "advisory"

EDAP_THRESHOLD = {"repeat_min": 2}

def extract_evidence(sentences: List[Evidence]) -> List[Expansion]:
    """Extract expansions from narrative sentences using EDAP criteria"""
    exps: List[Expansion] = []
    for s in sentences:
        t = s.text

        # ALT_ENUM: "WhatsApp or Telegram" / "such as A, B"
        if (" or " in t.lower()) or ("such as" in t.lower()) or ("including" in t.lower()):
            alts = _extract_alternatives(t)
            for alt in alts:
                # compile literal set expansion for platforms/domains named explicitly
                pat = _literal_to_pattern(alt)
                exps.append(Expansion(pattern=pat, kind="behavior_or_platform",
                                      parent_spans=s.spans, operator="ALT_ENUM",
                                      evidence_sent_id=s.sent_id, evidence_quote=t, status="advisory"))

        # RANGE_DIGITS: "3-4 digit code", "6+ digits"
        rng = _extract_digit_range(t)
        if rng:
            lo, hi = rng
            # example: VOID <digits> where VOID is in parent spans
            if any("VOID" in s.text for s in sentences):
                pat = r"VOID[ ]\\d{" + (f"{lo},{hi}" if hi else f"{lo},") + "}"
                exps.append(Expansion(pattern=pat, kind="text",
                                      parent_spans=s.spans, operator="RANGE_DIGITS",
                                      evidence_sent_id=s.sent_id, evidence_quote=t, status="advisory"))

        # LITERAL_SET: explicitly named variants
        literals = _extract_literal_set(t)
        for lit in literals:
            pat = _literal_to_pattern(lit)
            exps.append(Expansion(pattern=pat, kind="domain_or_url",
                                  parent_spans=s.spans, operator="LITERAL_SET", 
                                  evidence_sent_id=s.sent_id, evidence_quote=t, status="advisory"))

    # EDAP: auto-promote if E1/E2/E3 holds
    return _apply_edap(exps, sentences)

def _apply_edap(exps: List[Expansion], sentences: List[Evidence]) -> List[Expansion]:
    """Apply Evidence-Driven Auto-Promotion criteria"""
    # E1: ALT_ENUM present -> ready
    # E2: RANGE_DIGITS present -> ready
    for e in exps:
        if e.operator in ("ALT_ENUM", "RANGE_DIGITS"):
            e.status = "ready"
    
    # E3: LITERAL_SET with explicit enumeration -> ready
    for e in exps:
        if e.operator == "LITERAL_SET":
            # Check if multiple variants explicitly listed
            if "," in e.evidence_quote and len(_extract_literal_set(e.evidence_quote)) > 1:
                e.status = "ready"
    
    # E3 repeat mention: naive boost
    counts: Dict[str,int] = {}
    for s in sentences:
        for tok in _candidate_terms(s.text):
            counts[tok] = counts.get(tok, 0) + 1
    
    for e in exps:
        base_pattern = e.pattern.replace("\\", "").replace("(", "").replace(")", "")
        if counts.get(base_pattern.lower(), 0) >= EDAP_THRESHOLD["repeat_min"]:
            e.status = "ready"
    
    return exps

def _extract_alternatives(text: str) -> List[str]:
    """Extract alternatives from enumeration patterns"""
    import re
    lowers = text.lower()
    alternatives = []
    
    if "such as" in lowers:
        # Extract after "such as"
        seg = text[lowers.index("such as") + 8:]
        alternatives.extend([a.strip().strip(".,;:()") for a in seg.split(",") if a.strip()])
    
    if " or " in lowers:
        # Extract from "A or B" patterns
        parts = [p.strip() for p in re.split(r'\s+or\s+', text, flags=re.IGNORECASE)]
        # Take last word of each part as the alternative
        alternatives.extend([p.split()[-1].strip(".,;:()") for p in parts if p.strip()])
    
    if "including" in lowers:
        # Extract after "including"
        seg = text[lowers.index("including") + 9:]
        alternatives.extend([a.strip().strip(".,;:()") for a in seg.split(",") if a.strip()])
    
    return [alt for alt in alternatives if alt and len(alt) > 1]

def _extract_digit_range(text: str) -> Tuple[int,int] | None:
    """Extract digit range specifications"""
    import re
    
    # Look for patterns like "3-4 digit", "6+ digit", "between 4 and 8"
    patterns = [
        r"(\d+)[-–](\d+)\s*digit",
        r"(\d+)\+\s*digit",
        r"between\s+(\d+)\s+and\s+(\d+)",
        r"(\d+)\s+to\s+(\d+)\s*digit"
    ]
    
    for pattern in patterns:
        m = re.search(pattern, text.lower())
        if m:
            if m.lastindex == 2:
                return int(m.group(1)), int(m.group(2))
            else:
                return int(m.group(1)), None
    
    return None

def _extract_literal_set(text: str) -> List[str]:
    """Extract explicitly named literal variants"""
    import re
    literals = []
    
    # Look for domain-like patterns in lists
    domains = re.findall(r'\b[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b', text)
    if len(domains) > 1:
        literals.extend(domains)
    
    # Look for explicit variant listings
    if "," in text and any(char in text for char in [".", "@", "/"]):
        # Split on commas and extract items that look like URLs/domains/identifiers
        parts = [p.strip().strip(".,;:()") for p in text.split(",")]
        variants = [p for p in parts if any(char in p for char in [".", "@", "/"]) and len(p) > 3]
        if len(variants) > 1:
            literals.extend(variants)
    
    return literals

def _literal_to_pattern(s: str) -> str:
    """Convert literal string to regex pattern"""
    import re
    return re.escape(s)

def _candidate_terms(text: str) -> List[str]:
    """Extract candidate terms for frequency analysis"""
    import re
    # Extract words and domain-like strings
    words = re.findall(r'\b\w+\b', text.lower())
    domains = re.findall(r'\b[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b', text.lower())
    return words + domains