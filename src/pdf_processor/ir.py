# src/pdf_processor/ir.py
from typing import Any, Dict, Iterable

BEHAVIORAL_KEYS = ("velocity_event_count","ip_reputation","account_age_days")
CASE_KEYS = ("case_id","report_id")
BEHAVIOR_KEYS = ("behavior","category","provenance")

def to_ir_objects(spans):
    """Convert normalized spans into IR with value|norm|provenance (C-001..C-003)."""
    ir = []
    for s in spans:
        obj = {
            "type": s["type"],
            "value": s["value"],          # verbatim
            "provenance": s["provenance"] # {"page","start","end"}
        }
        if s["type"] == "amount":
            obj["norm"] = {"currency": s.get("currency","USD"), "amount": s["amount_float"]}  # C-001
        if s["type"] == "link":
            # C-002: literal only, no normalization
            pass
        if s["type"] == "category":
            # C-003: category must include source span id(s)
            obj.setdefault("span_ids", s.get("span_ids", []))
        ir.append(obj)
    return ir

def normalize_indicator(i: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize indicator with behavioral and case field validation."""
    out = dict(i)
    # Validate behavioral fields if present
    if out.get("ip_reputation") not in (None,"low","med","high"):
        out.pop("ip_reputation", None)
    # Ensure case/report fields are strings if present
    for k in CASE_KEYS:
        if k in out and not isinstance(out[k], str):
            out.pop(k, None)
    return out

def indicators_with_ids(indicators: Iterable[Dict[str,Any]], report_id: str|None=None, case_id: str|None=None):
    """Enrich indicators with case/report IDs while preserving existing values."""
    for i in indicators:
        ii = normalize_indicator(i)
        if report_id and "report_id" not in ii:
            ii["report_id"] = report_id
        if case_id and "case_id" not in ii:
            ii["case_id"] = case_id
        yield ii

def make_behavior(verbatim: str, category: str|None, report_id: str, span_id: str) -> dict:
    """Create a behavior indicator with verbatim text and provenance."""
    return {
        "type":"behavior",
        "value": verbatim,
        "category": category,
        "report_id": report_id,
        "span_id": span_id
    }
