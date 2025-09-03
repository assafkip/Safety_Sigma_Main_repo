import json
from pathlib import Path
from src.agentic.orchestrator import Orchestrator

def write(p: Path, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj), encoding="utf-8")

def test_orchestrator_produces_proposals(tmp_path: Path):
    # Seed minimal artifacts
    art = tmp_path / "artifacts"
    exps = {"expansions":[{"pattern":"VOID[ ]\\d{3,4}","status":"ready"}]}
    bt = {"rules":{"VOID[ ]\\d{3,4}":{"false_positive_rate":0.0}}}
    write(art / "proactive" / "expansions.json", exps)
    write(art / "proactive" / "backtest_report.json", bt)

    # Run orchestrator
    (tmp_path / "src/agentic").mkdir(parents=True, exist_ok=True)  # for relative imports if needed
    o = Orchestrator(tmp_path)
    run_dir = o.run()

    # A-801: logs exist
    assert (tmp_path / "agentic" / "audit.log.jsonl").exists()

    # A-802: proposals written under proposals/, not authoritative directories
    prop = run_dir / "proposals" / "deployment_proposals.json"
    assert prop.exists()
    obj = json.loads(prop.read_text(encoding="utf-8"))
    assert "proposals" in obj and len(obj["proposals"]) >= 1

def test_no_authoritative_mutation(tmp_path: Path):
    # Ensure orchestrator does not create/modify scripted authoritative files
    o = Orchestrator(tmp_path)
    o.run()
    assert not (tmp_path / "scripted").exists()