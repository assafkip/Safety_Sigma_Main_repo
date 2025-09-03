from __future__ import annotations
import json, time
from pathlib import Path
from typing import Dict, List

def _key_of(ind: Dict) -> str:
    """Generate consistent key for indicator patterns."""
    # Prefer explicit value (verbatim/literal), else regex pattern name if present
    v = ind.get("verbatim") or ind.get("literal") or ind.get("pattern") or ind.get("value")
    kind = ind.get("kind") or ind.get("type") or "unknown"
    return f"{kind}::{v}".strip()

def build_or_update_index(repo_root: Path, case_id: str|None=None) -> Path:
    """
    Scan artifacts for rules/indicators and update a cumulative index file:
    artifacts/memory/reuse_index.json
    Tracks: first_seen, last_seen, cases, count, kinds
    """
    art = repo_root/"artifacts"
    outdir = art/"memory"; outdir.mkdir(parents=True, exist_ok=True)
    idx_path = outdir/"reuse_index.json"
    idx = json.loads(idx_path.read_text(encoding="utf-8")) if idx_path.exists() else {"items": {}}
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    # Collect indicators from scripted demo_rules.json, proactive expansions (patterns), etc.
    sources: List[Dict] = []
    
    # Load from demo_rules.json (authoritative scripted indicators)
    dr = art/"demo_rules.json"
    if dr.exists():
        data = json.loads(dr.read_text(encoding="utf-8"))
        for i in data.get("indicators", []) or data.get("json", {}).get("indicators", []):
            i = dict(i)
            i["source"] = "scripted"
            sources.append(i)
    
    # Load from proactive expansions
    exps = art/"proactive"/"expansions.json"
    if exps.exists():
        ed = json.loads(exps.read_text(encoding="utf-8"))
        for e in ed.get("expansions", []):
            i = {"kind": e.get("kind","pattern"), "pattern": e.get("pattern"),
                 "evidence_quote": e.get("evidence_quote"), "source":"proactive",
                 "report_id": e.get("report_id"), "case_id": e.get("case_id")}
            sources.append(i)
    
    # Load behavioral indicators if available
    behaviors = art/"behaviors"/"extracted_behaviors.json"
    if behaviors.exists():
        bd = json.loads(behaviors.read_text(encoding="utf-8"))
        for b in bd.get("behaviors", []):
            i = {"type": b.get("type","behavior"), "value": b.get("value"),
                 "category": b.get("category"), "source":"behavioral",
                 "report_id": b.get("report_id"), "case_id": b.get("case_id")}
            sources.append(i)

    # Process each source indicator
    for s in sources:
        k = _key_of(s)
        if not k: 
            continue
        rec = idx["items"].get(k) or {"kinds": set(), "cases": set()}
        
        # Update sets (converting to/from sets for deduplication)
        kinds = set(rec.get("kinds") or [])
        cases = set(rec.get("cases") or [])
        categories = set(rec.get("categories") or [])
        
        if s.get("kind"): kinds.add(s["kind"])
        if s.get("type"): kinds.add(s["type"])
        if case_id: cases.add(case_id)
        if s.get("case_id"): cases.add(s["case_id"])
        if s.get("category"): categories.add(s["category"])
        
        # Convert sets back to sorted lists for JSON serialization
        rec["kinds"] = sorted(kinds)
        rec["cases"] = sorted(cases)
        rec["categories"] = sorted(categories) if categories else []
        
        # Update timestamps & counts
        rec["count"] = int(rec.get("count", 0)) + 1
        rec["first_seen"] = rec.get("first_seen") or now
        rec["last_seen"] = now
        
        idx["items"][k] = rec

    # Final normalization for JSON compatibility
    for k, rec in list(idx["items"].items()):
        if isinstance(rec.get("kinds"), set):   
            rec["kinds"] = sorted(list(rec["kinds"]))
        if isinstance(rec.get("cases"), set):   
            rec["cases"] = sorted(list(rec["cases"]))
        if isinstance(rec.get("categories"), set):   
            rec["categories"] = sorted(list(rec["categories"]))

    # Write updated index
    idx_path.write_text(json.dumps(idx, indent=2), encoding="utf-8")
    return idx_path