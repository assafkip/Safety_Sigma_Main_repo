#!/usr/bin/env python3
import argparse, json
from pathlib import Path
from src.proactive.backtest import backtest

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rules", required=True, help="Compiled artifacts JSON with 'regex' list")
    ap.add_argument("--clean", required=False, help="CSV with 'text' column (benign)")
    ap.add_argument("--labeled", required=False, help="CSV with 'text','label' columns (label in {pos,neg})")
    ap.add_argument("--out", default="artifacts/proactive/backtest_report.json")
    args = ap.parse_args()

    rules = Path(args.rules)
    clean = Path(args.clean) if args.clean else None
    labeled = Path(args.labeled) if args.labeled else None

    result = backtest(rules, clean, labeled)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Wrote {out}")

if __name__ == "__main__":
    main()