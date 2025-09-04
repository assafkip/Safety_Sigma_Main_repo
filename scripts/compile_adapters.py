#!/usr/bin/env python3
import json, argparse, sys, os
ap = argparse.ArgumentParser()
ap.add_argument("--rules", required=True)
ap.add_argument("--out", required=True)
args = ap.parse_args()
with open(args.rules) as f: rules = json.load(f)
os.makedirs(args.out, exist_ok=True)
errors = 0
sf = []
sift = []
u21 = []
for r in rules.get("rules", []):
    body = r.get("body","")
    # Snowflake SQL stub
    sf.append(f"-- rule:{r.get('id','')}\n{body};")
    # Sift/Unit21 JSON stubs
    sift.append({"id": r.get("id"), "type": "rule", "expr": body})
    u21.append({"id": r.get("id"), "type": "rule", "expr": body})
with open(os.path.join(args.out,"snowflake.sql"),"w") as f: f.write("\n\n".join(sf))
with open(os.path.join(args.out,"sift.json"),"w") as f: json.dump(sift,f,indent=2)
with open(os.path.join(args.out,"unit21.json"),"w") as f: json.dump(u21,f,indent=2)
print("[adapters] compiled=0 errors=0")
sys.exit(errors)