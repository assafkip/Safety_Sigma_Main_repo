from __future__ import annotations
import json, time
from pathlib import Path
from src.agentic.audit import AuditLog
from src.agentic.policy import DEFAULT_POLICY
from src.agentic.actions import load_proactive_expansions, load_backtest_metrics, choose_ready_deploy, plan_adapters

class Orchestrator:
    """Advisory orchestrator: reads artifacts, proposes next actions, never edits authoritative outputs."""
    def __init__(self, repo_root: Path):
        self.root = repo_root
        self.art = repo_root / "artifacts"
        self.out = repo_root / "agentic"
        self.out.mkdir(parents=True, exist_ok=True)
        self.audit = AuditLog(repo_root)

    def run(self) -> Path:
        run_dir = self.out / f"run_{int(time.time())}"
        run_dir.mkdir(parents=True, exist_ok=True)
        self.audit.append("orchestrator.start", {"run_dir": str(run_dir)})

        # Load advisory artifacts
        exps = load_proactive_expansions(self.art)
        self.audit.append("load.expansions", {"count": len(exps.get("expansions", []))})
        bt = load_backtest_metrics(self.art)
        self.audit.append("load.backtest", {"rule_count": len(bt.get("rules", {}))})

        # Decide candidates for deployment
        cand = choose_ready_deploy(exps, bt, DEFAULT_POLICY)
        self.audit.append("decide.ready_deploy", {"count": len(cand)})

        # Assign adapters (advisory)
        proposals = plan_adapters(cand, DEFAULT_POLICY)
        self.audit.append("decide.adapter_targets", {"count": len(proposals)})

        # Write proposals (safe write zone)
        prop_dir = run_dir / "proposals"
        prop_dir.mkdir(parents=True, exist_ok=True)
        (prop_dir / "deployment_proposals.json").write_text(json.dumps({"proposals": proposals}, indent=2), encoding="utf-8")
        self.audit.append("write.proposals", {"path": str(prop_dir / "deployment_proposals.json")})

        # Summarize decisions
        (run_dir / "plan.json").write_text(json.dumps({"candidates": cand}, indent=2), encoding="utf-8")
        self.audit.append("orchestrator.end", {"status": "ok"})
        return run_dir