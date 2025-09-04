#!/usr/bin/env python3
import json, sys, argparse
REQ = {"severity_label","rule_owner","detection_type","SLA","staleness_days","log_field_targets"}
ap = argparse.ArgumentParser()
ap.add_argument("--rules", required=True)
ap.add_argument("--out", required=True)
args = ap.parse_args()
with open(args.rules) as f: rules = json.load(f)
missing = {}
for r in rules.get("rules", []):
    miss = sorted([k for k in REQ if not r.get("metadata",{}).get(k)])
    if miss:
        missing[r.get("id","<unknown>")] = miss
ok = (len(missing)==0)
with open(args.out,"w") as f: json.dump({"missing":missing,"ok":ok}, f, indent=2)
print(f"[metadata] ok={ok} missing={len(missing)}")
if not ok: sys.exit(1)