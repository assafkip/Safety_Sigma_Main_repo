#!/usr/bin/env python3
import os, sys, json, argparse, hashlib, time, random
# Minimal stub: pretend to execute compiled SQL against sampled data
# Replace with real Snowflake execution via snowflake-connector-python in your environment.
ap = argparse.ArgumentParser()
ap.add_argument("--cfg", required=True)
ap.add_argument("--rules", required=True)
ap.add_argument("--out", required=True)
args = ap.parse_args()
with open(args.rules) as f: rules = json.load(f)
h = hashlib.sha256((args.cfg+args.rules).encode()).hexdigest()[:12]
metrics = {"dataset_hash": h, "generated_at": int(time.time()), "rules": {}}
random.seed(7)
for r in rules.get("rules", []):
    sample = max(1000, random.randint(1000,5000))
    tp = random.randint(0, max(1, sample//200))
    fp = random.randint(0, max(1, sample//400))
    fpr = fp/max(1,sample)
    tpr = tp/max(1,tp+random.randint(1,50))
    comp = max(0.0, 1.0 - 0.8*fpr + 0.2*tpr)
    metrics["rules"][r.get("id","<unknown>")] = {"sample_size": sample, "tp": tp, "fp": fp, "fpr": fpr, "tpr": tpr, "composite": comp}
with open(args.out,"w") as f: json.dump(metrics, f, indent=2)
print(f"[backtest] wrote metrics for {len(metrics['rules'])} rules to {args.out}")