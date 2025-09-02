import json
from pathlib import Path
from src.proactive.backtest import backtest

def test_backtest_computes_rates(tmp_path):
    # minimal rules with one trivial regex
    rules = {"regex":[{"pattern":"VOID[ ]\\d{3,4}"}]}
    rpath = tmp_path/"rules.json"; rpath.write_text(json.dumps(rules), encoding="utf-8")
    clean = tmp_path/"clean.csv"; clean.write_text("text\nno matches here\nanother benign line\n", encoding="utf-8")
    labeled = tmp_path/"lab.csv"; labeled.write_text("text,label\nVOID 1234,pos\nhello,neg\n", encoding="utf-8")
    res = backtest(rpath, clean, labeled)
    assert "rules" in res and "VOID[ ]\\d{3,4}" in res["rules"]
    entry = res["rules"]["VOID[ ]\\d{3,4}"]
    assert entry["samples_tested"] >= 3
    assert "false_positive_rate" in entry and "true_positive_rate" in entry