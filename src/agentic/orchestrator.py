from __future__ import annotations
import json, time
from pathlib import Path
from src.agentic.audit import AuditLog
from src.agentic.policy import DEFAULT_POLICY
from src.agentic.decisions import pick_candidates, assign_targets
from src.memory.reuse_index import build_or_update_index

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

        # Load artifacts and update memory index
        exps = _read_json(self.art / "proactive" / "expansions.json") or {"expansions":[]}
        bt   = _read_json(self.art / "proactive" / "backtest_report.json") or {"rules":{}}
        self.audit.append("load.artifacts", {"expansions": len(exps["expansions"]), "bt_rules": len(bt["rules"])})

        # Build/update reuse index and load for related case analysis
        idx_path = build_or_update_index(self.root)
        idx = json.loads(Path(idx_path).read_text(encoding="utf-8"))
        self.audit.append("memory.reuse_index", {"index_path": str(idx_path), "total_patterns": len(idx.get("items", {}))})

        def prior_cases_for_pattern(pat: str) -> int:
            """Get count of prior cases that used this pattern."""
            key = f"pattern::{pat}"
            rec = idx.get("items",{}).get(key) or {}
            return len(rec.get("cases", []))

        # Enrich candidates with prior case counts
        cand = pick_candidates(exps, bt, DEFAULT_POLICY)
        for c in cand:
            if "pattern" in c:
                c["prior_case_count"] = prior_cases_for_pattern(c["pattern"])
        self.audit.append("decide.candidates", {"count": len(cand)})

        props = assign_targets(cand, DEFAULT_POLICY)
        self.audit.append("decide.proposals", {"count": len(props)})

        # Governance analysis and escalation tracking
        gov_stats = self._analyze_governance(cand)
        self.audit.append("governance.analysis", gov_stats)

        # Write outputs (advisory-only safe zone)
        (self.out / "plan.json").write_text(json.dumps({"candidates": cand}, indent=2), encoding="utf-8")
        (self.out / "decisions.json").write_text(json.dumps({"proposals": props}, indent=2), encoding="utf-8")
        prop_dir = self.out / "proposals"; prop_dir.mkdir(exist_ok=True)
        (prop_dir / "deployment_proposals.json").write_text(json.dumps({"proposals": props}, indent=2), encoding="utf-8")
        
        # Write governance report for analyst feedback loop
        gov_report = {
            "governance_summary": gov_stats,
            "escalations": [c for c in cand if c.get("decision", "").startswith("escalate")],
            "ready_for_review": [c for c in cand if c.get("decision") == "ready-review"],
            "approved_for_deployment": [c for c in cand if c.get("decision") == "ready-deploy"],
            "decision_tree_reference": "../docs/governance_decision_tree.md"
        }
        (self.out / "governance_report.json").write_text(json.dumps(gov_report, indent=2), encoding="utf-8")
        
        self.audit.append("write.outputs", {
            "plan": "plan.json", 
            "decisions": "decisions.json", 
            "proposals": "proposals/deployment_proposals.json",
            "governance": "governance_report.json"
        })

        self.audit.append("orchestrator.end", {"status":"ok"})
        return self.out

    def _analyze_governance(self, candidates):
        """Analyze governance gate results for feedback loop."""
        stats = {
            "total_candidates": len(candidates),
            "ready_deploy": 0,
            "ready_review": 0,
            "escalate_missing_confidence": 0,
            "escalate_missing_tier": 0,
            "escalate_missing_metadata": 0,
            "governance_pass_rate": 0.0
        }
        
        for c in candidates:
            decision = c.get("decision", "")
            if decision == "ready-deploy":
                stats["ready_deploy"] += 1
            elif decision == "ready-review":
                stats["ready_review"] += 1
            elif decision == "escalate-missing-confidence":
                stats["escalate_missing_confidence"] += 1
            elif decision == "escalate-missing-tier":
                stats["escalate_missing_tier"] += 1
            elif decision == "escalate-missing-metadata":
                stats["escalate_missing_metadata"] += 1
        
        # Calculate governance pass rate (ready-deploy + ready-review vs escalations)
        non_escalated = stats["ready_deploy"] + stats["ready_review"]
        if stats["total_candidates"] > 0:
            stats["governance_pass_rate"] = round(non_escalated / stats["total_candidates"], 3)
        
        return stats