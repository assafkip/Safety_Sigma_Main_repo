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
    
    errs = 0
    stmts = []
    for r in regs:
        pat = r.get("pattern")
        if not pat:
            errs += 1
            continue
        span = r.get('meta', {}).get('source_span', '') if isinstance(r.get('meta'), dict) else ''
        stmts.append(f"-- Sigma pattern (span: {span})\nSELECT * FROM events WHERE REGEXP_LIKE(message, '{pat}');")
    (out_dir/"sql_rules.sql").write_text("\n\n".join(stmts), encoding="utf-8")
    (Path(__file__).parent/"compile_log.txt").write_text(f"compiled={len(stmts)} errors={errs}\n", encoding="utf-8")
    return 1 if errs else 0

if __name__ == "__main__":
    sys.exit(main())