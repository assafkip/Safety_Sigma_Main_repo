#!/usr/bin/env python3
import json, sys
from pathlib import Path

def main():
    root = Path(__file__).resolve().parents[2]
    art = root/"artifacts"/"demo_rules.json"
    out_dir = Path(__file__).resolve().parent/"out"
    out_dir.mkdir(parents=True, exist_ok=True)

    data = json.loads(art.read_text(encoding="utf-8")) if art.exists() else {}
    
    # Handle both old regex format and new JSON structure
    regs = data.get("regex", [])
    if not regs and "json" in data:
        # Extract patterns from indicators for demo purposes
        indicators = data["json"].get("indicators", [])
        regs = [{"pattern": f".*{ind.get('verbatim', '')}.*", "meta": {"source_span": ind.get("span_id", "")}} 
                for ind in indicators if ind.get("verbatim")]
    
    if not regs:
        print("No patterns found; nothing to compile.")
        return 0

    errs = 0
    lines = []
    for r in regs:
        pat = r.get("pattern")
        if not isinstance(pat, str) or not pat:
            errs += 1
            continue
        # Minimal SPL (illustrative); real adapters will template this.
        span = r.get('meta', {}).get('source_span', '') if isinstance(r.get('meta'), dict) else ''
        lines.append(f"search _raw=\"{pat}\"  /* span: {span}, owner: Sigma, sla: 48h, fields: _raw */")
    
    # Add metadata comments
    metadata_lines = [
        "/* Sigma Rule Metadata */",
        "/* severity_label: Medium */", 
        "/* rule_owner: Sigma */",
        "/* detection_type: hunting */",
        "/* sla: 48 hours */",
        "/* log_field_targets: _raw, message */",
        "",
        "/* Field Mapping Guide: Map to your index fields */",
        "/* Common fields: caller_id, payment_method, message */",
        ""
    ]
    final_lines = metadata_lines + lines
    (out_dir/"splunk_rules.spl").write_text("\n".join(final_lines), encoding="utf-8")
    (Path(__file__).parent/"compile_log.txt").write_text(f"compiled={len(lines)} errors={errs}\n", encoding="utf-8")
    return 1 if errs else 0

if __name__ == "__main__":
    sys.exit(main())