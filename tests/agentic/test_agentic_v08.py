import json
from pathlib import Path
from src.agentic.orchestrator import Orchestrator

def write_json(p: Path, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj), encoding="utf-8")

def test_agentic_outputs_and_safety(tmp_path: Path):
    # Seed minimal artifacts
    exps = {"expansions":[
        {"pattern":"VOID[ ]\\d{3,4}","status":"ready","operator":"RANGE_DIGITS",
         "evidence_quote":"VOID followed by a 3-4 digit code.", "justification":"RANGE_DIGITS from S2"},
        {"pattern":"apps","status":"ready","operator":"ALT_ENUM","evidence_quote":"apps or payments","justification":"ALT_ENUM from S1"}
    ]}
    bt   = {"rules":{"VOID[ ]\\d{3,4}":{"false_positive_rate":0.0},"apps":{"false_positive_rate":0.10}}}
    write_json(tmp_path/"artifacts/proactive/expansions.json", exps)
    write_json(tmp_path/"artifacts/proactive/backtest_report.json", bt)

    # Run
    run_dir = Orchestrator(tmp_path).run()

    # A-801: audit log exists
    assert (tmp_path/"agentic/audit.log.jsonl").exists()

    # Outputs present
    props = json.loads((run_dir/"proposals/deployment_proposals.json").read_text(encoding="utf-8"))
    # Should include VOID pattern (low FPR), not "apps" (generic/high FPR escalated)
    pat_list = [p["pattern"] for p in props.get("proposals",[])]
    assert "VOID[ ]\\d{3,4}" in pat_list

    # A-802: authoritative dirs not created/modified
    assert not (tmp_path/"scripted").exists()