#!/usr/bin/env python3
"""
Generate NON-AUTHORITATIVE advisory narrative from existing IR/rules.
Default: offline/template mode (no model calls).
Optional: LLM mode if ADVISORY_LLM=on and API key present (adds 'Advisory Augmentations' section).
"""
import argparse, json, os
from pathlib import Path

DISCLAIMER = (
  "**ADVISORY / NON-AUTHORITATIVE** — This narrative is for analyst convenience. "
  "It is derived from quoted spans already present in the IR/rules bundle. "
  "Do not treat this document as a source of truth. The authoritative artifacts remain: "
  "`ir/ir.json`, `rules/rules.json`, test results, and the validation manifest."
)

def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def extract_literals(ir, rules):
    inds = (rules or {}).get("json", {}).get("indicators", [])
    # Fallback to IR if rules.json doesn't include indicators in JSON section
    if not inds and ir:
        inds = ir.get("indicators", [])
    out = {
        "amounts": [i for i in inds if i.get("kind")=="amount"],
        "accounts": [i for i in inds if i.get("kind")=="account"],
        "domains": [i for i in inds if i.get("kind")=="domain"],
        "phones":  [i for i in inds if i.get("kind")=="phone"],
        "emails":  [i for i in inds if i.get("kind")=="email"],
        "behaviors":[i for i in inds if i.get("kind")=="behavior"],
        "texts":   [i for i in inds if i.get("kind") in ("text","memo")],
    }
    return out

def mk_quote(item):
    val = item.get("verbatim") or item.get("literal") or ""
    span = f"{item.get('category_id','')}/{item.get('span_id','')}"
    return f'• "{val}"  _(span: {span})_'

def render_markdown(lits, augmentations=None):
    lines = []
    lines.append("# Advisory Narrative v0.1 — NON-AUTHORITATIVE\n")
    lines.append(DISCLAIMER + "\n")
    # Threat Themes
    if lits["behaviors"]:
        lines.append("## Threat Themes (literal)\n")
        for b in lits["behaviors"]:
            lines.append(f"- {b.get('verbatim','') or b.get('literal','')}")
        lines.append("")
    # Financial Indicators
    if lits["amounts"] or lits["accounts"]:
        lines.append("## Financial Indicators (literal)\n")
        for a in lits["amounts"]:
            val = a.get("verbatim","")
            span = f"{a.get('category_id','')}/{a.get('span_id','')}"
            lines.append(f"- Amount: **{val}** _(span: {span})_")
        for acc in lits["accounts"]:
            val = acc.get("verbatim","")
            span = f"{acc.get('category_id','')}/{acc.get('span_id','')}"
            lines.append(f"- Account: **{val}** _(span: {span})_")
        lines.append("")
    # Infrastructure
    if any([lits["domains"], lits["phones"], lits["emails"]]):
        lines.append("## Infrastructure (literal)\n")
        for c, lbl in [("domains","Domain"),("phones","Phone"),("emails","Email")]:
            for i in lits[c]:
                val = i.get("verbatim","") or i.get("literal","")
                span = f"{i.get('category_id','')}/{i.get('span_id','')}"
                lines.append(f"- {lbl}: **{val}** _(span: {span})_")
        lines.append("")
    # Observed Phrases
    if lits["texts"]:
        lines.append("## Observed Phrases (quotes)\n")
        for t in lits["texts"]:
            lines.append(mk_quote(t))
        lines.append("")
    # Advisory Augmentations (optional)
    if augmentations:
        lines.append("## Advisory Augmentations (optional)\n")
        lines.append("_The following are advisory interpretations; verify against quoted spans above._\n")
        lines.extend([f"- Advisory: {s}" for s in augmentations])
        lines.append("")
    return "\n".join(lines)

def maybe_llm_augment(lits):
    # Placeholder for optional model usage; OFF by default.
    # If ADVISORY_LLM=on and an API key is configured by the operator, you can add lightweight advisory bullets.
    # This function MUST only use information present in lits; no external retrieval.
    if os.environ.get("ADVISORY_LLM","off").lower() != "on":
        return None
    # To keep repo safe-by-default, we do NOT implement API calls here.
    # Operators may patch this function in their environment.
    return None

def main():
    ap = argparse.ArgumentParser(description="Generate Advisory Narrative (NON-AUTHORITATIVE)")
    ap.add_argument("--ir", type=str, help="Path to IR JSON", default=None)
    ap.add_argument("--rules", type=str, help="Path to rules JSON (compiled)", default="artifacts/demo_rules.json")
    ap.add_argument("--outdir", type=str, default="advisory")
    args = ap.parse_args()

    ir = load_json(Path(args.ir)) if args.ir else None
    rules = load_json(Path(args.rules)) if args.rules else None

    lits = extract_literals(ir, rules)
    augment = maybe_llm_augment(lits)
    md = render_markdown(lits, augmentations=augment)

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir/"narrative_advisory.md").write_text(md, encoding="utf-8")
    (outdir/"sources.json").write_text(json.dumps(lits, indent=2), encoding="utf-8")
    print("Wrote advisory/narrative_advisory.md and advisory/sources.json")

if __name__ == "__main__":
    main()