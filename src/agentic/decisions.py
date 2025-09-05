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
    """Assign deployment targets with governance gates."""
    proposals = []
    for c in candidates:
        # Governance gates: require confidence & tier even for ready-deploy
        if c.get("decision") != "ready-deploy":
            continue
            
        # v1.0 Governance: mandatory confidence scoring
        confidence = c.get("confidence_score")
        if confidence is None:
            # Escalate: missing confidence score
            c["decision"] = "escalate-missing-confidence"
            c["escalation_reason"] = "Advisory item lacks required confidence score"
            continue
            
        # Risk tier validation
        risk_tier = c.get("risk_tier")
        if not risk_tier:
            c["decision"] = "escalate-missing-tier"
            c["escalation_reason"] = "Advisory item lacks required risk tier assignment"
            continue
            
        # Metadata validation
        required_metadata = {"severity_label", "rule_owner", "detection_type", "sla"}
        missing_metadata = []
        for field in required_metadata:
            if not c.get(field):
                missing_metadata.append(field)
                
        if missing_metadata:
            c["decision"] = "escalate-missing-metadata"
            c["escalation_reason"] = f"Missing required metadata: {', '.join(missing_metadata)}"
            continue
            
        # Governance passed: create deployment proposals
        for tgt in policy.allowed_targets:
            proposal = {**c, "target_system": tgt}
            # Add governance attestation
            from datetime import datetime, timezone
            proposal["governance_status"] = "approved"
            proposal["governance_timestamp"] = datetime.now(timezone.utc).isoformat()
            proposals.append(proposal)
    
    return proposals