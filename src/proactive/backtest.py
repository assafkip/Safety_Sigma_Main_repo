from __future__ import annotations
import re, json, csv
from pathlib import Path
from typing import Dict, List, Tuple

def load_regexes(artifacts_json: Path) -> List[Tuple[str, re.Pattern]]:
    data = json.loads(artifacts_json.read_text(encoding="utf-8"))
    regs = []
    for r in data.get("regex", []):
        pat = r.get("pattern")
        if isinstance(pat, str):
            try:
                regs.append((pat, re.compile(pat)))
            except re.error:
                pass
    return regs

def _iter_csv_rows(csv_path: Path) -> Tuple[str, str]:
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield row.get("text", ""), (row.get("label") or "").lower()

def backtest(rules_json: Path, clean_corpus: Path, labeled_corpus: Path|None=None) -> Dict:
    regs = load_regexes(rules_json)
    summary: Dict[str, Dict[str, float|int]] = {pat: {"matches":0, "samples_tested":0, "tp":0, "fp":0} for pat,_ in regs}
    # Clean corpus: count FPs
    if clean_corpus and clean_corpus.exists():
        for txt,_ in _iter_csv_rows(clean_corpus):
            for pat, rx in regs:
                summary[pat]["samples_tested"] += 1
                if rx.search(txt or ""):
                    summary[pat]["matches"] += 1
                    summary[pat]["fp"] += 1
    # Labeled corpus: count TPs
    if labeled_corpus and labeled_corpus.exists():
        for txt, lab in _iter_csv_rows(labeled_corpus):
            for pat, rx in regs:
                summary[pat]["samples_tested"] += 1
                hit = bool(rx.search(txt or ""))
                if hit:
                    summary[pat]["matches"] += 1
                if lab == "pos":
                    summary[pat]["tp"] += 1 if hit else 0
    # rates
    for pat in summary:
        s = summary[pat]
        s["false_positive_rate"] = round((s["fp"]/s["samples_tested"]), 6) if s["samples_tested"] else 0.0
        s["true_positive_rate"]  = round((s["tp"]/s["samples_tested"]), 6) if s["samples_tested"] else 0.0
    return {"rules": summary}