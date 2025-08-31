# src/pdf_processor/ir.py
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
