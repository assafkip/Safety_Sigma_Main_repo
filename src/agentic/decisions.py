from __future__ import annotations
from typing import Any, Dict, List

def _has_strong_justification(e: Dict[str, Any]) -> bool:
    just = (e.get("justification") or "").strip()
    quote = (e.get("evidence_quote") or "").strip()
    op = (e.get("operator") or "").strip()
    return bool(just and quote and op)

def pick_candidates(expansions: Dict[str, Any], backtest: Dict[str, Any], policy) -> List[Dict[str, Any]]:
    fpr_map = backtest.get("rules", {})
    out = []
    for e in expansions.get("expansions", []):
        status = e.get("status", "advisory")
        pat = e.get("pattern", "")
        # Only consider EDAP-ready items
        if status not in ("ready", "ready-deploy"):
            continue
        fpr = fpr_map.get(pat, {}).get("false_positive_rate", 1.0)
        strong = _has_strong_justification(e) if policy.require_justification else True
        if fpr <= policy.max_fpr and strong:
            out.append({**e, "deployment_candidate": True, "fpr": fpr, "decision": "ready-deploy"})
        else:
            out.append({**e, "deployment_candidate": False, "fpr": fpr, "decision": "ready-review"})
    return out

def assign_targets(candidates: List[Dict[str, Any]], policy) -> List[Dict[str, Any]]:
    proposals = []
    for c in candidates:
        if c.get("decision") != "ready-deploy":
            continue
        for tgt in policy.allowed_targets:
            proposals.append({**c, "target_system": tgt})
    return proposals