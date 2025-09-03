from __future__ import annotations
import json, time
from pathlib import Path
from src.agentic.audit import AuditLog
from src.agentic.policy import DEFAULT_POLICY
from src.agentic.decisions import pick_candidates, assign_targets

def _read_json(p: Path):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None

class Orchestrator:
    """Advisory-only orchestrator. Reads artifacts, proposes next actions, never mutates authoritative outputs."""
    def __init__(self, repo_root: Path):
        self.root = repo_root
        self.art = repo_root / "artifacts"
        self.out = repo_root / "agentic" / f"run_{int(time.time())}"
        self.out.mkdir(parents=True, exist_ok=True)
        self.audit = AuditLog(repo_root)

    def run(self) -> Path:
        self.audit.append("orchestrator.start", {"run_dir": str(self.out)})

        exps = _read_json(self.art / "proactive" / "expansions.json") or {"expansions":[]}
        bt   = _read_json(self.art / "proactive" / "backtest_report.json") or {"rules":{}}
        self.audit.append("load.artifacts", {"expansions": len(exps["expansions"]), "bt_rules": len(bt["rules"])})

        cand = pick_candidates(exps, bt, DEFAULT_POLICY)
        self.audit.append("decide.candidates", {"count": len(cand)})

        props = assign_targets(cand, DEFAULT_POLICY)
        self.audit.append("decide.proposals", {"count": len(props)})

        # Write outputs (advisory-only safe zone)
        (self.out / "plan.json").write_text(json.dumps({"candidates": cand}, indent=2), encoding="utf-8")
        (self.out / "decisions.json").write_text(json.dumps({"proposals": props}, indent=2), encoding="utf-8")
        prop_dir = self.out / "proposals"; prop_dir.mkdir(exist_ok=True)
        (prop_dir / "deployment_proposals.json").write_text(json.dumps({"proposals": props}, indent=2), encoding="utf-8")
        self.audit.append("write.outputs", {"plan": "plan.json", "decisions": "decisions.json", "proposals": "proposals/deployment_proposals.json"})

        self.audit.append("orchestrator.end", {"status":"ok"})
        return self.out