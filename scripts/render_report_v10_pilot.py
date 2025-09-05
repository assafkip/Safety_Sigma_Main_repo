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

def _risk_tier_badge(tier: str) -> str:
    """Format risk tier as colored badge."""
    if tier == "blocking":
        return f'<span class="badge tier-blocking">{tier.upper()}</span>'
    elif tier == "hunting": 
        return f'<span class="badge tier-hunting">{tier.upper()}</span>'
    elif tier == "enrichment":
        return f'<span class="badge tier-enrichment">{tier.upper()}</span>'
    else:
        return f'<span class="badge tier-unknown">{tier.upper() if tier else "UNKNOWN"}</span>'

def _confidence_bar(score: float) -> str:
    """Format confidence score as progress bar."""
    if score is None:
        return '<span class="confidence-missing">NO SCORE</span>'
    
    percentage = int(score * 100)
    color_class = "high" if score >= 0.7 else "medium" if score >= 0.4 else "low"
    
    return f'''<div class="confidence-bar">
        <div class="confidence-fill confidence-{color_class}" style="width: {percentage}%"></div>
        <span class="confidence-text">{score:.3f}</span>
    </div>'''

def _governance_status(decision: str, escalation_reason: str = None) -> str:
    """Format governance decision status."""
    if decision == "ready-deploy":
        return '<span class="gov-approved">✓ APPROVED</span>'
    elif decision == "ready-review":
        return '<span class="gov-review">⚠ REVIEW</span>'
    elif decision.startswith("escalate"):
        reason = escalation_reason or "Unknown"
        return f'<span class="gov-escalate">❌ ESCALATED</span><br><small>{html.escape(reason)}</small>'
    else:
        return f'<span class="gov-unknown">{html.escape(decision)}</span>'

def render_governance_dashboard(parts: list[str]):
    """Render v1.0 Pilot Readiness Governance Dashboard."""
    esc = html.escape
    
    parts.append("""<div class="section pilot-readiness">
  <h2>🎯 v1.0 Pilot Readiness Dashboard</h2>
  <p class="small">Governance gates for production deployment. All items must pass confidence scoring, risk tier classification, and metadata validation.</p>
""")
    
    # Load governance report from latest agentic run
    agentic_dir = ROOT / "agentic"
    governance_data = None
    if agentic_dir.exists():
        runs = [d for d in agentic_dir.iterdir() if d.is_dir() and d.name.startswith("run_")]
        if runs:
            latest_run = max(runs, key=lambda x: x.stat().st_mtime)
            governance_file = latest_run / "governance_report.json"
            if governance_file.exists():
                governance_data = load_json(governance_file)
    
    if governance_data and governance_data.get("governance_summary"):
        stats = governance_data["governance_summary"]
        
        # Governance summary metrics
        parts.append(f"""<div class="governance-summary">
    <div class="gov-metric">
        <div class="gov-number">{stats.get('total_candidates', 0)}</div>
        <div class="gov-label">Total Candidates</div>
    </div>
    <div class="gov-metric success">
        <div class="gov-number">{stats.get('ready_deploy', 0)}</div>
        <div class="gov-label">Ready Deploy</div>
    </div>
    <div class="gov-metric warning">
        <div class="gov-number">{stats.get('ready_review', 0)}</div>
        <div class="gov-label">Needs Review</div>
    </div>
    <div class="gov-metric error">
        <div class="gov-number">{stats.get('escalate_missing_confidence', 0) + stats.get('escalate_missing_tier', 0) + stats.get('escalate_missing_metadata', 0)}</div>
        <div class="gov-label">Escalated</div>
    </div>
    <div class="gov-metric">
        <div class="gov-number">{stats.get('governance_pass_rate', 0.0):.1%}</div>
        <div class="gov-label">Pass Rate</div>
    </div>
</div>""")
        
        # Escalation breakdown if any
        total_escalated = stats.get('escalate_missing_confidence', 0) + stats.get('escalate_missing_tier', 0) + stats.get('escalate_missing_metadata', 0)
        if total_escalated > 0:
            parts.append("""<div class="escalation-details">
    <h3>Escalation Breakdown</h3>
    <ul>""")
            if stats.get('escalate_missing_confidence', 0) > 0:
                parts.append(f"<li>Missing Confidence Score: {stats['escalate_missing_confidence']}</li>")
            if stats.get('escalate_missing_tier', 0) > 0:
                parts.append(f"<li>Missing Risk Tier: {stats['escalate_missing_tier']}</li>") 
            if stats.get('escalate_missing_metadata', 0) > 0:
                parts.append(f"<li>Missing Metadata: {stats['escalate_missing_metadata']}</li>")
            parts.append("</ul></div>")
    else:
        parts.append("<p class='note'>No governance analysis available. Run agentic workflow to generate governance report.</p>")
    
    parts.append("</div>")

def render_proactive_v10(parts: list[str], exps_clean: list, exps: list):
    """Enhanced proactive section with v1.0 pilot readiness features."""
    esc = html.escape
    
    parts.append("""<div class="section">
  <h2>🧪 Proactive Scenarios (EDAP) — v1.0 Pilot Ready</h2>
  <p class="small">Enhanced with confidence scoring, risk tier classification, and governance validation for production deployment readiness.</p>
""")

    if exps_clean:
        parts.append("<table class='pilot-table'><thead><tr><th>Pattern</th><th>Confidence</th><th>Risk Tier</th><th>Governance</th><th>FPR</th><th>Evidence</th><th>Metadata</th></tr></thead><tbody>")
        
        for e in exps_clean:
            # Find original expansion data for enhanced fields
            orig_data = None
            for orig_exp in exps:
                if orig_exp.get("pattern") == e["pattern"] and orig_exp.get("operator") == e["operator"]:
                    orig_data = orig_exp
                    break
            
            pattern = esc(e['pattern'][:50])
            
            # Confidence scoring
            confidence = orig_data.get("confidence_score") if orig_data else None
            confidence_html = _confidence_bar(confidence)
            
            # Risk tier
            risk_tier = orig_data.get("risk_tier", "") if orig_data else ""
            tier_html = _risk_tier_badge(risk_tier)
            
            # Governance status
            decision = orig_data.get("decision", "") if orig_data else ""
            escalation_reason = orig_data.get("escalation_reason", "") if orig_data else ""
            governance_html = _governance_status(decision, escalation_reason)
            
            # FPR from backtest
            fpr = orig_data.get("fpr", "N/A") if orig_data else "N/A"
            fpr_display = f"{fpr:.3f}" if isinstance(fpr, (int, float)) else str(fpr)
            
            # Evidence quote
            quote = next(iter(e["quotes"])) if e["quotes"] else ""
            clean_quote = _clean_text(quote)[:80] + "..." if len(_clean_text(quote)) > 80 else _clean_text(quote)
            
            # Metadata status
            metadata_fields = ["severity_label", "rule_owner", "detection_type", "sla"] 
            metadata_missing = []
            if orig_data:
                for field in metadata_fields:
                    if not orig_data.get(field):
                        metadata_missing.append(field)
            
            metadata_html = "✓ Complete" if not metadata_missing else f"❌ Missing: {', '.join(metadata_missing)}"
            
            parts.append(f"""<tr>
                <td class='mono'>{pattern}</td>
                <td>{confidence_html}</td>
                <td>{tier_html}</td>
                <td>{governance_html}</td>
                <td>{fpr_display}</td>
                <td class='small'>{esc(clean_quote)}</td>
                <td class='small'>{metadata_html}</td>
            </tr>""")
        
        parts.append("</tbody></table>")
    else:
        parts.append("<p class='note'>No proactive expansions found (EDAP). Ensure artifacts/proactive/expansions.json exists.</p>")
    
    parts.append("</div>")

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

    # Basic scripted indicator summary 
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

    # HTML build with v1.0 pilot readiness styling
    parts = []
    parts.append(f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>🛡️ Safety Sigma v1.0 Pilot Readiness Report</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; margin: 40px auto; max-width: 1200px; line-height: 1.55; background: #fafafa; }}
.header {{ background: linear-gradient(135deg,#2c5aa0,#1e3a8a); color:#fff; padding:20px; border-radius:10px; }}
.section {{ background:#fff; margin:20px 0; padding:20px; border-radius:10px; box-shadow:0 2px 4px rgba(0,0,0,.08); }}
.pilot-readiness {{ border-left: 4px solid #2c5aa0; }}
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

/* v1.0 Pilot Readiness Styles */
.governance-summary {{ display: flex; gap: 20px; margin: 20px 0; flex-wrap: wrap; }}
.gov-metric {{ text-align: center; padding: 15px; background: #f8f9fa; border-radius: 8px; min-width: 120px; }}
.gov-metric.success {{ background: #d4edda; border-left: 4px solid #28a745; }}
.gov-metric.warning {{ background: #fff3cd; border-left: 4px solid #ffc107; }}
.gov-metric.error {{ background: #f8d7da; border-left: 4px solid #dc3545; }}
.gov-number {{ font-size: 2em; font-weight: bold; }}
.gov-label {{ font-size: 0.9em; color: #666; }}

.badge {{ padding: 3px 8px; border-radius: 12px; font-size: 0.8em; font-weight: bold; }}
.tier-blocking {{ background: #dc3545; color: white; }}
.tier-hunting {{ background: #fd7e14; color: white; }}
.tier-enrichment {{ background: #20c997; color: white; }}
.tier-unknown {{ background: #6c757d; color: white; }}

.confidence-bar {{ position: relative; width: 80px; height: 20px; background: #e9ecef; border-radius: 10px; }}
.confidence-fill {{ height: 100%; border-radius: 10px; }}
.confidence-high {{ background: #28a745; }}
.confidence-medium {{ background: #ffc107; }}
.confidence-low {{ background: #dc3545; }}
.confidence-text {{ position: absolute; top: 0; left: 0; width: 100%; text-align: center; line-height: 20px; font-size: 0.75em; font-weight: bold; }}
.confidence-missing {{ color: #dc3545; font-weight: bold; font-size: 0.8em; }}

.gov-approved {{ color: #28a745; font-weight: bold; }}
.gov-review {{ color: #ffc107; font-weight: bold; }}
.gov-escalate {{ color: #dc3545; font-weight: bold; }}
.gov-unknown {{ color: #6c757d; }}

.pilot-table th {{ background: #2c5aa0; color: white; }}
.pilot-table tr:hover {{ background: #f8f9fa; }}

.escalation-details {{ background: #f8d7da; padding: 15px; border-radius: 8px; margin: 15px 0; }}
.escalation-details h3 {{ color: #721c24; margin-top: 0; }}
</style>
</head><body>
<div class="header">
  <h1>🛡️ Safety Sigma v1.0 Pilot Readiness — Production-Ready Governance</h1>
  <p class="small"><strong>Generated:</strong> {esc(now)} • <strong>Source PDF:</strong> atlas-highlights-scams-and-fraud.pdf</p>
  <p class="small"><span class="pill">Scripted = authoritative</span>
                 <span class="pill">LLM = advisory</span>
                 <span class="pill">EDAP = advisory</span>
                 <span class="pill">v1.0 Governance = pilot</span>
                 <span class="pill">Confidence Scoring</span>
                 <span class="pill">Risk Tiers</span></p>
</div>

<div class="advisory">v1.0 PILOT READINESS — Enhanced with confidence scoring, risk tier classification, metadata validation, and governance gates for limited production deployment.</div>
""")

    # Governance Dashboard first for v1.0 focus
    render_governance_dashboard(parts)

    # Original sections with slight modifications
    parts.append(f"""<div class="section">
  <h2>📊 Extraction Summary (Scripted — authoritative)</h2>
  <p class="small">Indicators shown here are verbatim, source-grounded, and traced with spans. They satisfy the validation contract (V-001..V-005).</p>
  <ul>
    <li><strong>Total indicators:</strong> {len(inds)}</li>
    <li><strong>Unique for display:</strong> {len(unique_display)}</li>
    <li><strong>Categories:</strong> {len(cats)}</li>
  </ul>
</div>

<div class="section"><h2>🔍 Key Indicators (Scripted — authoritative)</h2>
<table><thead><tr><th>Kind</th><th>Value</th><th>Category</th><th>Span</th></tr></thead><tbody>""")
    
    for i in inds[:50]:
        val = i.get("verbatim") or i.get("literal")
        parts.append(f"<tr><td>{esc(i.get('kind'))}</td><td><strong>{esc(val)}</strong></td>"
                     f"<td>{esc(i.get('category_id'))}</td><td class='mono'>{esc(i.get('span_id'))}</td></tr>")
    parts.append("</tbody></table></div>")

    # Enhanced Proactive section with v1.0 features
    render_proactive_v10(parts, exps_clean, exps)

    # Enhanced Backtest Metrics
    parts.append("""<div class="section">
  <h2>📊 Backtest Metrics — v1.0 Enhanced</h2>
  <p class="small">Performance metrics with confidence scoring integration. FPR thresholds determine risk tier assignments.</p>
""")
    
    backtest_rules = backtest_data.get("rules", {})
    if backtest_rules:
        parts.append("<table class='pilot-table'><thead><tr><th>Pattern</th><th>Samples</th><th>Matches</th><th>FPR</th><th>TPR</th><th>Confidence</th><th>Risk Assessment</th></tr></thead><tbody>")
        for pattern, metrics in backtest_rules.items():
            fpr = metrics.get('false_positive_rate', 0.0)
            tpr = metrics.get('true_positive_rate', 0.0)
            samples = metrics.get('samples_tested', 0)
            
            # Calculate confidence score using the v1.0 algorithm
            confidence_score = None
            if samples > 0:
                base = max(0.0, min(1.0, 1.0 - fpr))
                sample_factor = min(1.0, samples / 100.0)
                confidence_score = (base * 0.8 + tpr * 0.2) * sample_factor
            
            confidence_html = _confidence_bar(confidence_score) if confidence_score else "N/A"
            
            # Risk assessment
            risk_assessment = "❌ High Risk (FPR > 1%)" if fpr > 0.01 else "⚠️ Medium Risk" if fpr > 0.005 else "✅ Low Risk"
            
            parts.append(f"<tr><td class='mono'>{esc(pattern)}</td>"
                         f"<td>{metrics.get('samples_tested', 0)}</td>"
                         f"<td>{metrics.get('matches', 0)}</td>"
                         f"<td>{fpr:.3f}</td>"
                         f"<td>{tpr:.3f}</td>"
                         f"<td>{confidence_html}</td>"
                         f"<td>{risk_assessment}</td></tr>")
        parts.append("</tbody></table>")
    else:
        parts.append("<p class='note'>No backtest metrics available. Run backtesting to see v1.0 confidence scoring.</p>")
    parts.append("</div>")

    # Governance Decision Tree reference
    parts.append("""<div class="section">
  <h2>⚖️ Governance Framework</h2>
  <p class="small">v1.0 governance decision tree ensures all deployed rules meet production standards.</p>
  <ul>
    <li><strong>Gate 1:</strong> Confidence Scoring (composite FPR/TPR metrics)</li>
    <li><strong>Gate 2:</strong> Risk Tier Classification (blocking/hunting/enrichment)</li>
    <li><strong>Gate 3:</strong> Metadata Validation (owner, severity, SLA, detection type)</li>
    <li><strong>Gate 4:</strong> Policy Compliance (FPR thresholds, justification requirements)</li>
  </ul>
  <p><strong>Decision Tree:</strong> <a href="../docs/governance_decision_tree.md">governance_decision_tree.md</a></p>
</div>""")

    # Deployment section with v1.0 enhancements
    parts.append("""<div class="section">
  <h2>🚀 v1.0 Deployment Pipeline</h2>
  <p class="small">Enhanced adapters with governance metadata for production deployment.</p>
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
        parts.append("<table class='pilot-table'><thead><tr><th>Target</th><th>Status</th><th>v1.0 Enhancements</th><th>Details</th></tr></thead><tbody>")
        for result in adapter_results:
            status_badge = "✅ Ready" if result["status"] == "compiled" else "❌ Error"
            v10_features = "Governance metadata, field mapping, SLA tracking"
            parts.append(f"<tr><td class='mono'>{esc(result['target'])}</td>"
                        f"<td>{status_badge}</td>"
                        f"<td class='small'>{v10_features}</td>"
                        f"<td class='small'>{esc(result['details'])}</td></tr>")
        parts.append("</tbody></table>")
    else:
        parts.append("<p class='note'>No adapter results found. Run 'make adapters' to generate v1.0 deployment targets.</p>")
    parts.append("</div>")

    parts.append("""<div class="section">
  <h2>⚖️ v1.0 Processing Compliance</h2>
  <ul>
    <li><strong>Authoritative Lane:</strong> V-001..V-005 validation gates preserved</li>
    <li><strong>Advisory Lane:</strong> Enhanced with confidence scoring and governance validation</li>
    <li><strong>Pilot Readiness:</strong> Production deployment gates with escalation paths</li>
    <li><strong>Risk Management:</strong> Tiered FPR thresholds with mandatory metadata</li>
  </ul>
</div>

<div class="section"><p class="small">Generated by Safety Sigma v1.0 Pilot Readiness · Enhanced governance framework for limited production deployment.</p></div>
</body></html>""")

    out = ART / "demo_report_v10_pilot.html"
    out.write_text("".join(parts), encoding="utf-8")
    print(f"Wrote {out}")

if __name__ == "__main__":
    try:
        render()
    except Exception as e:
        print("ERROR:", e, file=sys.stderr)
        sys.exit(1)