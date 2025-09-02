#!/usr/bin/env python3
import json, sys, html, re, textwrap
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts"

def load_json(p):
    p = Path(p)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None

def _unescape_pattern(pat: str) -> str:
    # show \d instead of \\d in display
    return pat.replace("\\\\", "\\")

def _is_generic(token: str) -> bool:
    token = token.strip().lower()
    return token in {"apps","payments","transfers"}  # display-only filter

def _clean_text(text: str) -> str:
    """Clean text for readable HTML paragraphs - join words properly."""
    if not text:
        return ""
    # Remove excessive whitespace and join words into sentences
    tokens = text.split()
    return " ".join(tokens)

def _format_quote(quote: str) -> str:
    """Format evidence quotes as clean blockquotes."""
    clean_quote = _clean_text(quote)
    if not clean_quote:
        return ""
    # Wrap in blockquote for better formatting
    return f'<blockquote class="quote">{html.escape(clean_quote)}</blockquote>'

def render():
    rules = load_json(ART / "demo_rules.json") or {}
    pro_exp = load_json(ART / "proactive" / "expansions.json") or {"expansions": []}
    exps = pro_exp.get("expansions", [])

    # Display-only cleanup for proactive expansions (authoritative JSON unchanged)
    dedup = {}
    for e in exps:
        pat = _unescape_pattern(e.get("pattern",""))
        op  = e.get("operator","")
        if _is_generic(pat):  # drop noisy tokens from display
            continue
        key = (pat, op)
        rec = dedup.setdefault(key, {
            "pattern": pat,
            "operator": op,
            "status": e.get("status","advisory"),
            "parent_spans": set(),
            "quotes": set()
        })
        for s in e.get("parent_spans", []):
            rec["parent_spans"].add(s)
        if e.get("evidence_quote"):
            rec["quotes"].add(e["evidence_quote"])

    exps_clean = sorted(dedup.values(), key=lambda x: (x["operator"], x["pattern"]))

    # Basic scripted indicator summary (best-effort from rules JSON "json.indicators" or "indicators")
    inds = []
    if "json" in rules and isinstance(rules["json"], dict):
        inds = rules["json"].get("indicators", [])
    elif "indicators" in rules:
        inds = rules.get("indicators", [])

    # Count categories & uniques for display
    cats = {i.get("category_id","") for i in inds if i.get("category_id")}
    unique_display = {(i.get("kind"), i.get("verbatim") or i.get("literal")) for i in inds}
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def esc(x): return html.escape(str(x)) if x is not None else ""

    # HTML build
    parts = []
    parts.append(f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>🛡️ Safety Sigma v0.4 Report</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; margin: 40px auto; max-width: 1100px; line-height: 1.55; background: #fafafa; }}
.header {{ background: linear-gradient(135deg,#495057,#343a40); color:#fff; padding:20px; border-radius:10px; }}
.section {{ background:#fff; margin:20px 0; padding:20px; border-radius:10px; box-shadow:0 2px 4px rgba(0,0,0,.08); }}
h2 {{ border-bottom:2px solid #eee; padding-bottom:8px; color:#333; }}
.pill {{ display:inline-block; background:#eee; border-radius:999px; padding:2px 10px; margin-right:8px; font-size:.9em; }}
.advisory {{ background:linear-gradient(135deg,#ff6b6b,#ee5a52); color:#fff; padding:12px; border-radius:8px; font-weight:700; }}
.small {{ color:#666; font-size:.95em; }}
blockquote, .quote {{ background:#f8f8f8; padding:10px; border-left:3px solid #ddd; margin:8px 0; }}
p {{ margin:8px 0 16px 0; }}
table {{ width:100%; border-collapse:collapse; margin-top:12px; }}
th,td {{ padding:10px; border-bottom:1px solid #eee; text-align:left; vertical-align:top; }}
th {{ background:#f8f8f8; }}
.mono {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }}
.note {{ color:#666; }}
</style>
</head><body>
<div class="header">
  <h1>🛡️ Safety Sigma v0.4 — Scripted (AUTHORITATIVE) + LLM (ADVISORY) + Proactive (EDAP)</h1>
  <p class="small"><strong>Generated:</strong> {esc(now)} • <strong>Source PDF:</strong> atlas-highlights-scams-and-fraud.pdf</p>
  <p class="small"><span class="pill">Scripted = authoritative (V-001..V-005)</span>
                 <span class="pill">LLM = advisory</span>
                 <span class="pill">Proactive EDAP = advisory</span></p>
</div>

<div class="section">
  <h2>📊 Extraction Summary (Scripted — authoritative)</h2>
  <p class="small">Indicators shown here are verbatim, source-grounded, and traced with spans. They satisfy the validation contract (V-001..V-005).</p>
  <ul>
    <li><strong>Total indicators:</strong> {len(inds)}</li>
    <li><strong>Unique for display:</strong> {len(unique_display)}</li>
    <li><strong>Categories:</strong> {len(cats)}</li>
  </ul>
</div>

<div class="advisory">NON-AUTHORITATIVE Content Below — for analyst convenience only. Verify against authoritative artifacts.</div>

<div class="section">
  <h2>📝 Advisory Narrative (LLM lane)</h2>
  <p class="note">See the bundle's <span class="mono">llm_output/narrative.md</span> for full text. Every claim quotes a span; the LLM lane is advisory.</p>
</div>
""")

    # Scripted indicator quick table (minimal)
    parts.append("""<div class="section"><h2>🔍 Key Indicators (Scripted — authoritative)</h2>
<table><thead><tr><th>Kind</th><th>Value</th><th>Category</th><th>Span</th></tr></thead><tbody>""")
    for i in inds[:50]:
        val = i.get("verbatim") or i.get("literal")
        parts.append(f"<tr><td>{esc(i.get('kind'))}</td><td><strong>{esc(val)}</strong></td>"
                     f"<td>{esc(i.get('category_id'))}</td><td class='mono'>{esc(i.get('span_id'))}</td></tr>")
    parts.append("</tbody></table></div>")

    # Proactive scenarios section
    parts.append("""<div class="section">
  <h2>🧪 Proactive Scenarios (EDAP)</h2>
  <p class="small">These expansions are derived from explicit narrative in the input PDF. Each row includes a pattern, its operator, parent spans, and an evidence quote. Items marked <strong>ready</strong> met EDAP criteria (explicit enumeration, explicit range, or repetition evidence) and are suitable for preventive deployment after local backtesting.</p>
""")

    if exps_clean:
        parts.append("<table><thead><tr><th>Pattern</th><th>Operator</th><th>Status</th><th>Parent Spans</th><th>Evidence Quote</th></tr></thead><tbody>")
        for e in exps_clean:
            spans = ", ".join(sorted(e["parent_spans"])) if e["parent_spans"] else "-"
            quote = next(iter(e["quotes"])) if e["quotes"] else ""
            clean_quote = _clean_text(quote)  # Clean up quote formatting
            parts.append(f"<tr><td class='mono'>{esc(e['pattern'])}</td>"
                         f"<td>{esc(e['operator'])}</td>"
                         f"<td>{esc(e['status'])}</td>"
                         f"<td class='mono'>{esc(spans)}</td>"
                         f"<td>{esc(clean_quote)}</td></tr>")
        parts.append("</tbody></table>")
    else:
        parts.append("<p class='note'>No proactive expansions found (EDAP). Ensure artifacts/proactive/expansions.json exists.</p>")
    parts.append("</div>")

    parts.append("""<div class="section">
  <h2>⚖️ Processing Compliance</h2>
  <ul>
    <li><strong>Zero-inference (Scripted):</strong> verbatim indicators; span-level provenance; categories appear only if explicitly in source.</li>
    <li><strong>Validation Gates:</strong> V-001..V-005 apply to the scripted lane (authoritative).</li>
    <li><strong>Proactive EDAP:</strong> evidence-driven expansions; traceable to quotes; advisory unless explicitly promoted by EDAP rules.</li>
  </ul>
</div>

<div class="section"><p class="small">Generated by Safety Sigma v0.4 · Scripted authoritative core + LLM/advisory + Proactive/EDAP.</p></div>
</body></html>""")

    out = ART / "demo_report_v04.html"
    out.write_text("".join(parts), encoding="utf-8")
    print(f"Wrote {out}")

if __name__ == "__main__":
    try:
        render()
    except Exception as e:
        print("ERROR:", e, file=sys.stderr)
        sys.exit(1)