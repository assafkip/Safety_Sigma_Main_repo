from __future__ import annotations
import json
from pathlib import Path
from typing import Any

def read_json(p: Path) -> Any:
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None

def load_proactive_expansions(art_dir: Path):
    return read_json(art_dir / "proactive" / "expansions.json") or {"expansions":[]}

def load_backtest_metrics(art_dir: Path):
    return read_json(art_dir / "proactive" / "backtest_report.json") or {"rules":{}}

def choose_ready_deploy(expansions, backtest, policy) -> list[dict]:
    """Select expansions with strong evidence and acceptable FP rate."""
    ready = []
    fpr_map = backtest.get("rules", {})
    for e in expansions.get("expansions", []):
        pat = e.get("pattern","")
        status = e.get("status","advisory")
        if status not in ("ready","ready-deploy"): 
            continue
        fpr = fpr_map.get(pat, {}).get("false_positive_rate", 1.0)
        if fpr <= policy.max_fpr:
            e = {**e, "deployment_candidate": True, "fpr": fpr}
            ready.append(e)
    return ready

def plan_adapters(candidates: list[dict], policy) -> list[dict]:
    """Assign target systems for proposals; advisory only."""
    out = []
    for e in candidates:
        for tgt in policy.allowed_targets:
            out.append({**e, "target_system": tgt})
    return out