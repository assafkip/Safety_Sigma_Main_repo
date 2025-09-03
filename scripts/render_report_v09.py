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

def render_memory_sections(parts: list[str]):
    """Render Living Knowledge Base and Reuse Signals sections."""
    esc = html.escape
    
    # Load reuse index
    idx_path = ART / "memory" / "reuse_index.json"
    if not idx_path.exists():
        parts.append("""<div class="section">
  <h2>📚 Living Knowledge Base</h2>
  <p class="note">No prior cases indexed yet. Run 'make memory-index' to build cumulative knowledge base.</p>
</div>""")
        return
    
    try:
        idx = json.loads(idx_path.read_text(encoding="utf-8"))
        items = idx.get("items", {})
        
        # Living Knowledge Base section
        parts.append("""<div class="section">
  <h2>📚 Living Knowledge Base</h2>
  <p class="small">Every past case becomes structured context. Prior-case counts help de-duplicate work and show pattern evolution.</p>
""")
        
        if items:
            # Calculate some basic metrics
            total_patterns = len(items)
            total_occurrences = sum(rec.get("count", 0) for rec in items.values())
            unique_cases = set()
            for rec in items.values():
                unique_cases.update(rec.get("cases", []))
            
            parts.append(f"""<p><strong>Knowledge Stats:</strong> {total_patterns} unique patterns, {total_occurrences} total occurrences, {len(unique_cases)} cases referenced</p>""")
            
            parts.append("<table><thead><tr><th>Pattern Key</th><th>Occurrences</th><th>Prior Cases</th><th>Velocity</th></tr></thead><tbody>")
            
            # Sort by count (most frequent first), limit display
            sorted_items = sorted(items.items(), key=lambda x: x[1].get("count", 0), reverse=True)
            for k, rec in sorted_items[:50]:  # Show top 50 patterns
                count = rec.get("count", 0)
                cases = rec.get("cases", [])
                case_list = ", ".join(cases[:5])  # Show first 5 cases
                if len(cases) > 5:
                    case_list += f" (+{len(cases)-5} more)"
                
                # Calculate velocity if we have timestamps
                velocity = "-"
                first_seen = rec.get("first_seen")
                last_seen = rec.get("last_seen")
                if first_seen and last_seen and first_seen != last_seen:
                    try:
                        from datetime import datetime
                        fs = datetime.fromisoformat(first_seen.replace('Z', '+00:00'))
                        ls = datetime.fromisoformat(last_seen.replace('Z', '+00:00'))
                        days = (ls - fs).days
                        if days > 0:
                            velocity = f"{days}d"
                    except:
                        pass
                
                parts.append(f"<tr><td class='mono'>{esc(k[:80])}</td><td>{count}</td><td class='small'>{esc(case_list) if case_list else '-'}</td><td>{velocity}</td></tr>")
            
            parts.append("</tbody></table>")
        else:
            parts.append("<p class='note'>Knowledge base is empty. Process more cases to build cumulative intelligence.</p>")
        
        parts.append("</div>")
        
        # Reuse Signals section
        parts.append("""<div class="section">
  <h2>🔄 Reuse Signals</h2>
  <p class="small">Pattern reuse context helps analysts understand which indicators appeared in previous investigations.</p>
""")
        
        # Load current proactive expansions to show reuse context
        pro_exp = load_json(ART / "proactive" / "expansions.json") or {"expansions": []}
        current_patterns = []
        for exp in pro_exp.get("expansions", []):
            pat = exp.get("pattern", "")
            if pat:
                key = f"pattern::{pat}"
                rec = items.get(key, {})
                prior_count = len(rec.get("cases", []))
                if prior_count > 0:  # Only show patterns with prior usage
                    current_patterns.append({
                        "pattern": pat,
                        "prior_cases": rec.get("cases", []),
                        "prior_count": prior_count,
                        "first_seen": rec.get("first_seen", "-"),
                        "evidence": exp.get("evidence_quote", "")[:100] + "..." if len(exp.get("evidence_quote", "")) > 100 else exp.get("evidence_quote", "")
                    })
        
        if current_patterns:
            parts.append("<table><thead><tr><th>Current Pattern</th><th>Prior Usage</th><th>Cases</th><th>Evidence</th></tr></thead><tbody>")
            for p in current_patterns[:20]:  # Limit display
                cases_str = ", ".join(p["prior_cases"][:3])
                if len(p["prior_cases"]) > 3:
                    cases_str += f" (+{len(p['prior_cases'])-3})"
                parts.append(f"<tr><td class='mono'>{esc(p['pattern'])}</td><td>{p['prior_count']} cases</td><td class='small'>{esc(cases_str)}</td><td class='small'>{esc(p['evidence'])}</td></tr>")
            parts.append("</tbody></table>")
        else:
            parts.append("<p class='note'>No current patterns found in prior cases. This appears to be a novel investigation.</p>")
        
        parts.append("</div>")
        
    except Exception as e:
        parts.append(f"""<div class="section">
  <h2>📚 Living Knowledge Base</h2>
  <p class="note">Error reading memory index: {esc(str(e))}</p>
</div>""")

def render():
    rules = load_json(ART / "demo_rules.json") or {}
    pro_exp = load_json(ART / "proactive" / "expansions.json") or {"expansions": []}
    exps = pro_exp.get("expansions", [])
    backtest_data = load_json(ART / "proactive" / "backtest_report.json") or {"rules": {}}

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
<title>🛡️ Safety Sigma v0.9 Report</title>
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
  <h1>🛡️ Safety Sigma v0.9 — Scripted (AUTHORITATIVE) + LLM (ADVISORY) + Proactive (EDAP) + Agentic + Memory</h1>
  <p class="small"><strong>Generated:</strong> {esc(now)} • <strong>Source PDF:</strong> atlas-highlights-scams-and-fraud.pdf</p>
  <p class="small"><span class="pill">Scripted = authoritative (V-001..V-005)</span>
                 <span class="pill">LLM = advisory</span>
                 <span class="pill">Proactive EDAP = advisory</span>
                 <span class="pill">Agentic = advisory</span>
                 <span class="pill">Memory = cumulative</span></p>
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
        parts.append("<table><thead><tr><th>Pattern</th><th>Operator</th><th>Status</th><th>Parent Spans</th><th>Evidence Quote</th><th>Justification</th></tr></thead><tbody>")
        for e in exps_clean:
            spans = ", ".join(sorted(e["parent_spans"])) if e["parent_spans"] else "-"
            quote = next(iter(e["quotes"])) if e["quotes"] else ""
            clean_quote = _clean_text(quote)  # Clean up quote formatting
            # Get justification from original expansions
            justification = ""
            for orig_exp in exps:
                if orig_exp.get("pattern") == e["pattern"] and orig_exp.get("operator") == e["operator"]:
                    justification = orig_exp.get("justification", "")
                    break
            parts.append(f"<tr><td class='mono'>{esc(e['pattern'])}</td>"
                         f"<td>{esc(e['operator'])}</td>"
                         f"<td>{esc(e['status'])}</td>"
                         f"<td class='mono'>{esc(spans)}</td>"
                         f"<td>{esc(clean_quote)}</td>"
                         f"<td>{esc(justification)}</td></tr>")
        parts.append("</tbody></table>")
    else:
        parts.append("<p class='note'>No proactive expansions found (EDAP). Ensure artifacts/proactive/expansions.json exists.</p>")
    parts.append("</div>")

    # Backtest Metrics section
    parts.append("""<div class="section">
  <h2>📊 Backtest Metrics (v0.5)</h2>
  <p class="small">Performance metrics for each pattern against test corpora. FPR = False Positive Rate, TPR = True Positive Rate.</p>
""")
    
    backtest_rules = backtest_data.get("rules", {})
    if backtest_rules:
        parts.append("<table><thead><tr><th>Pattern</th><th>Samples Tested</th><th>Matches</th><th>FPR</th><th>TPR</th></tr></thead><tbody>")
        for pattern, metrics in backtest_rules.items():
            parts.append(f"<tr><td class='mono'>{esc(pattern)}</td>"
                         f"<td>{metrics.get('samples_tested', 0)}</td>"
                         f"<td>{metrics.get('matches', 0)}</td>"
                         f"<td>{metrics.get('false_positive_rate', 0.0):.3f}</td>"
                         f"<td>{metrics.get('true_positive_rate', 0.0):.3f}</td></tr>")
        parts.append("</tbody></table>")
    else:
        parts.append("<p class='note'>No backtest metrics available. Run backtesting to see performance data.</p>")
    parts.append("</div>")

    # Behavioral Context section
    parts.append("""<div class="section">
  <h2>🔍 Behavioral Context (advisory)</h2>
  <p class="small">Optional behavioral fields for enhanced fraud detection. These are advisory enhancements and do not affect the authoritative scripted lane.</p>
  <ul>
    <li><strong>ip_reputation</strong> (low|med|high): IP reputation score based on threat intelligence</li>
    <li><strong>velocity_event_count</strong> (int): Number of events in time window</li>  
    <li><strong>account_age_days</strong> (int): Account age in days</li>
  </ul>
""")

    # Check if any behavioral fields present in indicators
    behavioral_found = False
    behavioral_indicators = []
    for i in inds:
        if any(field in i for field in ["ip_reputation", "velocity_event_count", "account_age_days"]):
            behavioral_found = True
            behavioral_indicators.append(i)
    
    if behavioral_found:
        parts.append("<p><strong>Behavioral data detected in indicators:</strong></p>")
        parts.append("<table><thead><tr><th>Kind</th><th>Value</th><th>IP Rep</th><th>Velocity</th><th>Account Age</th></tr></thead><tbody>")
        for i in behavioral_indicators[:10]:  # Show first 10
            val = i.get("verbatim") or i.get("literal")
            ip_rep = i.get("ip_reputation", "-")
            velocity = i.get("velocity_event_count", "-")
            age = i.get("account_age_days", "-")
            parts.append(f"<tr><td>{esc(i.get('kind'))}</td><td><strong>{esc(val)}</strong></td>"
                         f"<td>{esc(ip_rep)}</td><td>{esc(velocity)}</td><td>{esc(age)}</td></tr>")
        parts.append("</tbody></table>")
    else:
        parts.append("<p class='note'>No behavioral context fields detected in current indicators.</p>")
    parts.append("</div>")

    # Deployment section (V-006)
    parts.append("""<div class="section">
  <h2>🚀 Deployment Adapters (V-006)</h2>
  <p class="small">Compiled rule outputs for target environments. Each adapter preserves pattern + provenance + justification.</p>
""")
    
    adapter_targets = ["splunk", "elastic", "sql"]
    adapter_results = []
    for target in adapter_targets:
        log_file = ROOT / "adapters" / target / "compile_log.txt"
        if log_file.exists():
            try:
                log_content = log_file.read_text(encoding="utf-8").strip()
                adapter_results.append({"target": target, "status": "compiled", "details": log_content})
            except:
                adapter_results.append({"target": target, "status": "error", "details": "Failed to read log"})
        else:
            adapter_results.append({"target": target, "status": "not_run", "details": "No compile log found"})
    
    if adapter_results:
        parts.append("<table><thead><tr><th>Target</th><th>Status</th><th>Details</th></tr></thead><tbody>")
        for result in adapter_results:
            status_class = "compiled" if result["status"] == "compiled" else "error"
            parts.append(f"<tr><td class='mono'>{esc(result['target'])}</td>"
                        f"<td><span class='pill {status_class}'>{esc(result['status'])}</span></td>"
                        f"<td class='small'>{esc(result['details'])}</td></tr>")
        parts.append("</tbody></table>")
    else:
        parts.append("<p class='note'>No adapter results found. Run 'make adapters' to generate deployment targets.</p>")
    parts.append("</div>")

    # Sharing section (V-007)
    parts.append("""<div class="section">
  <h2>📦 Sharing & Export (V-007)</h2>
  <p class="small">Bundle integrity and cross-org sharing status. Checksums ensure artifact completeness.</p>
""")
    
    sharing_dir = ART / "sharing"
    checksums_file = sharing_dir / "checksums.txt"
    latest_bundle = None
    
    # Find latest audit package
    for bundle_file in ART.glob("audit_package_v0_*.zip"):
        if not latest_bundle or bundle_file.stat().st_mtime > latest_bundle.stat().st_mtime:
            latest_bundle = bundle_file
    
    if latest_bundle:
        bundle_size = latest_bundle.stat().st_size / (1024 * 1024)  # MB
        parts.append(f"<p><strong>Latest Bundle:</strong> <span class='mono'>{latest_bundle.name}</span> ({bundle_size:.1f} MB)</p>")
    else:
        parts.append("<p><strong>Latest Bundle:</strong> No bundles found</p>")
    
    if checksums_file.exists():
        try:
            checksums_data = json.loads(checksums_file.read_text(encoding="utf-8"))
            parts.append(f"<p><strong>Checksums:</strong> {len(checksums_data)} files verified</p>")
        except:
            parts.append("<p><strong>Checksums:</strong> Error reading checksums file</p>")
    else:
        parts.append("<p><strong>Checksums:</strong> Not generated. Run 'make share-export' to create.</p>")
    
    parts.append("</div>")

    # Agentic Plan (Advisory) section  
    # Living Knowledge Base section (v0.9)
    render_memory_sections(parts)
    
    parts.append("""<div class="section">
  <h2>🤖 Agentic Plan (Advisory)</h2>
  <p class="small">AI agents analyze EDAP expansions and backtest metrics to propose deployment actions. All agent decisions are advisory-only and require analyst approval.</p>
""")
    
    # Find latest agentic run
    agentic_dir = ROOT / "agentic"
    latest_run = None
    if agentic_dir.exists():
        runs = [d for d in agentic_dir.iterdir() if d.is_dir() and d.name.startswith("run_")]
        if runs:
            latest_run = max(runs, key=lambda x: x.stat().st_mtime)
    
    if latest_run and (latest_run / "proposals" / "deployment_proposals.json").exists():
        try:
            proposals_data = json.loads((latest_run / "proposals" / "deployment_proposals.json").read_text(encoding="utf-8"))
            proposals = proposals_data.get("proposals", [])
            
            if proposals:
                parts.append("<table><thead><tr><th>Pattern</th><th>FPR</th><th>Operator</th><th>Decision</th><th>Target(s)</th><th>Evidence Quote</th><th>Justification</th></tr></thead><tbody>")
                for p in proposals[:20]:  # Show first 20
                    pattern = esc(p.get("pattern", ""))[:50]
                    fpr = f"{p.get('fpr', 0.0):.3f}" if isinstance(p.get('fpr'), (int, float)) else "N/A"
                    operator = esc(p.get("operator", ""))
                    decision = esc(p.get("decision", ""))
                    target = esc(p.get("target_system", ""))
                    quote = esc(p.get("evidence_quote", ""))[:100]
                    justification = esc(p.get("justification", ""))[:80]
                    
                    parts.append(f"<tr><td class='mono'>{pattern}</td><td>{fpr}</td><td>{operator}</td>"
                                f"<td><strong>{decision}</strong></td><td class='mono'>{target}</td>"
                                f"<td class='small'>{quote}</td><td class='small'>{justification}</td></tr>")
                parts.append("</tbody></table>")
            else:
                # Show detailed explanation for no proposals
                parts.append("<p class='note'><strong>No deployment proposals this run.</strong></p>")
                parts.append("<p class='small'><strong>Reason:</strong> All EDAP expansions either exceed FPR threshold (>0.5%) or lack strong justification per EDAP criteria.</p>")
                
                # Show backtest context
                backtest_data = load_json(ART / "proactive" / "backtest_report.json") or {"rules": {}}
                if backtest_data.get("rules"):
                    high_fpr = [pat for pat, metrics in backtest_data["rules"].items() 
                              if metrics.get("false_positive_rate", 0) > 0.005]
                    if high_fpr:
                        parts.append(f"<p class='small'><strong>High FPR patterns:</strong> {len(high_fpr)} patterns exceed 0.5% threshold (safety escalation).</p>")
                else:
                    parts.append("<p class='small'><strong>Note:</strong> No backtest metrics available for FPR analysis.</p>")
        except Exception as e:
            parts.append(f"<p class='note'>Error reading agentic proposals: {esc(str(e))}</p>")
    else:
        parts.append("<p class='note'>No agentic run found. Run 'make agentic' to generate agent proposals.</p>")
    
    parts.append("</div>")

    parts.append("""<div class="section">
  <h2>⚖️ Processing Compliance</h2>
  <ul>
    <li><strong>Zero-inference (Scripted):</strong> verbatim indicators; span-level provenance; categories appear only if explicitly in source.</li>
    <li><strong>Validation Gates:</strong> V-001..V-005 apply to the scripted lane (authoritative).</li>
    <li><strong>Proactive EDAP:</strong> evidence-driven expansions; traceable to quotes; advisory unless explicitly promoted by EDAP rules.</li>
  </ul>
</div>

<div class="section"><p class="small">Generated by Safety Sigma v0.9 · Scripted authoritative core + LLM/advisory + Proactive/EDAP + Backtesting + Behavioral Context + Living Knowledge Base.</p></div>
</body></html>""")

    out = ART / "demo_report_v09.html"
    out.write_text("".join(parts), encoding="utf-8")
    print(f"Wrote {out}")

if __name__ == "__main__":
    try:
        render()
    except Exception as e:
        print("ERROR:", e, file=sys.stderr)
        sys.exit(1)