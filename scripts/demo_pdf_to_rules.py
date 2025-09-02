#!/usr/bin/env python3
"""
Demo PDF to Rules - Enhanced with analyst-friendly HTML reporting
Processes PDF with zero-inference, generates rules + enhanced HTML report
"""
import argparse
import json
import re
import datetime
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Any, Set

try:
    import PyPDF2
except ImportError:
    print("PyPDF2 not installed. Run: pip install PyPDF2")
    exit(1)

def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract text from PDF file"""
    text = ""
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            text += page.extract_text() + "\n"
    return text

def quality_filter_phone(phone_text: str) -> bool:
    """Quality filter for phone numbers: ≥7 digits, ≤30% whitespace"""
    digit_count = sum(1 for c in phone_text if c.isdigit())
    if digit_count < 7:
        return False
    
    whitespace_count = sum(1 for c in phone_text if c in ' \n\t\r')
    whitespace_ratio = whitespace_count / len(phone_text) if phone_text else 0
    
    return whitespace_ratio <= 0.3

def compute_display_value(text: str) -> str:
    """Compute clean display value (for HTML only) without changing IR"""
    return text.rstrip('.,;:!?')

def extract_indicators(text: str) -> List[Dict[str, Any]]:
    """Extract indicators with zero-inference methodology"""
    indicators = []
    
    # Amount pattern (preserve exact format)
    amount_pattern = r'\$[\d,]+\.?\d*'
    for i, match in enumerate(re.finditer(amount_pattern, text)):
        verbatim = match.group()
        try:
            numeric = float(verbatim.replace('$', '').replace(',', ''))
        except ValueError:
            numeric = 0.0
        
        indicators.append({
            "kind": "amount",
            "verbatim": verbatim,
            "numeric": numeric,
            "category_id": "financial",
            "span_id": f"amount_{i:03d}",
            "display_value": verbatim  # Same as verbatim for amounts
        })
    
    # Domain pattern (preserve exact format including punctuation)
    domain_pattern = r'\b[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}[.,;:!?]?'
    for i, match in enumerate(re.finditer(domain_pattern, text)):
        verbatim = match.group()
        display_value = compute_display_value(verbatim)
        
        indicators.append({
            "kind": "domain",
            "verbatim": verbatim,
            "category_id": "infra",
            "span_id": f"domain_{i:03d}",
            "display_value": display_value
        })
    
    # Phone pattern with quality filtering
    phone_pattern = r'\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}'
    for i, match in enumerate(re.finditer(phone_pattern, text)):
        verbatim = match.group().strip()
        
        if quality_filter_phone(verbatim):
            indicators.append({
                "kind": "phone",
                "verbatim": verbatim,
                "category_id": "infra", 
                "span_id": f"phone_{i:03d}",
                "display_value": verbatim
            })
    
    # Email pattern
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}[.,;:!?]?'
    for i, match in enumerate(re.finditer(email_pattern, text)):
        verbatim = match.group()
        display_value = compute_display_value(verbatim)
        
        indicators.append({
            "kind": "email", 
            "verbatim": verbatim,
            "category_id": "infra",
            "span_id": f"email_{i:03d}",
            "display_value": display_value
        })
    
    # Account patterns (preserve exact phrasing)
    account_patterns = [
        r'Zelle\s+(?:account\s+)?(?:ending\s+in\s+|ID\s+)?\d+',
        r'Cash\s+App\s+account',
        r'PayPal\s+account',
        r'account\s+#?\d+',
    ]
    
    account_idx = 0
    for pattern in account_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            verbatim = match.group()
            indicators.append({
                "kind": "account",
                "verbatim": verbatim,
                "category_id": "financial",
                "span_id": f"account_{account_idx:03d}",
                "display_value": verbatim
            })
            account_idx += 1
    
    # Behavior patterns (preserve exact phrasing)
    behavior_patterns = [
        r'redirected? to WhatsApp',
        r'urgent action required',
        r'verify your identity',
        r'click here to',
        r'avoid account suspension',
        r'claim (?:your )?refund',
        r'VOID \d+',
    ]
    
    behavior_idx = 0
    for pattern in behavior_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            verbatim = match.group()
            indicators.append({
                "kind": "behavior",
                "verbatim": verbatim,
                "category_id": "tactics",
                "span_id": f"behavior_{behavior_idx:03d}",
                "display_value": verbatim
            })
            behavior_idx += 1
    
    # Text/memo patterns (key phrases)
    text_patterns = [
        r'"[^"]+refund[^"]+"',
        r'"[^"]+IRS[^"]+"',
        r'"[^"]+NOTICE[^"]+"',
        r'wa\.me/\d+',
    ]
    
    text_idx = 0
    for pattern in text_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            verbatim = match.group()
            indicators.append({
                "kind": "text",
                "verbatim": verbatim,
                "category_id": "phrases",
                "span_id": f"text_{text_idx:03d}",
                "display_value": verbatim
            })
            text_idx += 1
    
    return indicators

def deduplicate_for_display(indicators: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Deduplicate identical indicators for display (preserve all in rules)"""
    display_groups = defaultdict(list)
    
    # Group by display_value and kind
    for indicator in indicators:
        key = (indicator['kind'], indicator.get('display_value', indicator.get('verbatim', '')))
        display_groups[key].append(indicator)
    
    deduplicated = []
    for (kind, display_value), group in display_groups.items():
        if len(group) == 1:
            deduplicated.append(group[0])
        else:
            # Multiple instances - create display item with count and all span_ids
            representative = group[0].copy()
            representative['count'] = len(group)
            representative['all_span_ids'] = [item['span_id'] for item in group]
            representative['display_note'] = f"Found {len(group)} times"
            deduplicated.append(representative)
    
    return deduplicated

def build_findings_sentences(indicators: List[Dict[str, Any]]) -> List[str]:
    """Build literal-stitch sentences from indicators"""
    findings = []
    
    # Group indicators by category for sentence building
    by_category = defaultdict(list)
    for ind in indicators:
        by_category[ind['category_id']].append(ind)
    
    # Financial findings
    if by_category.get('financial'):
        amounts = [ind for ind in by_category['financial'] if ind['kind'] == 'amount']
        accounts = [ind for ind in by_category['financial'] if ind['kind'] == 'account']
        
        for amount in amounts[:3]:  # Limit to first few for readability
            span_ref = f"({amount['category_id']}/{amount['span_id']})"
            sentence = f"Observed amount **{amount['verbatim']}** {span_ref}"
            
            # Look for related accounts
            for account in accounts[:1]:
                acc_span_ref = f"({account['category_id']}/{account['span_id']})"
                sentence += f" with account **{account['verbatim']}** {acc_span_ref}"
                break
                
            findings.append(sentence + ".")
    
    # Infrastructure findings
    if by_category.get('infra'):
        infra_items = by_category['infra'][:5]  # Limit for readability
        for item in infra_items:
            span_ref = f"({item['category_id']}/{item['span_id']})"
            findings.append(f"Observed {item['kind']} **{item.get('display_value', item['verbatim'])}** {span_ref}.")
    
    # Behavior findings
    if by_category.get('tactics'):
        behaviors = by_category['tactics'][:3]
        for behavior in behaviors:
            span_ref = f"({behavior['category_id']}/{behavior['span_id']})"
            findings.append(f"Observed behavior: **{behavior['verbatim']}** {span_ref}.")
    
    return findings

def generate_html_report(pdf_path: Path, indicators: List[Dict[str, Any]], 
                        rules_json: Dict[str, Any], advisory_content: str = "") -> str:
    """Generate enhanced HTML report with analyst-friendly features"""
    
    # Deduplicate for display
    display_indicators = deduplicate_for_display(indicators)
    
    # Build findings sentences
    findings = build_findings_sentences(indicators)
    
    # Group indicators by type for sections
    by_kind = defaultdict(list)
    for ind in display_indicators:
        by_kind[ind['kind']].append(ind)
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🛡️ Safety Sigma Demo Report</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 40px auto; max-width: 1000px; line-height: 1.6; background: #fafafa; }}
        .header {{ background: linear-gradient(135deg, #495057, #343a40); color: white; padding: 20px; border-radius: 8px; text-align: center; margin-bottom: 30px; }}
        .advisory-banner {{ background: linear-gradient(135deg, #ff6b6b, #ee5a52); color: white; padding: 15px; border-radius: 8px; margin: 20px 0; font-weight: bold; }}
        .advisory-banner::before {{ content: "⚠️ "; margin-right: 8px; }}
        .section {{ background: white; margin: 20px 0; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .findings {{ border-left: 4px solid #28a745; }}
        .financial {{ border-left: 4px solid #ffc107; }}
        .infrastructure {{ border-left: 4px solid #007bff; }}
        .behaviors {{ border-left: 4px solid #dc3545; }}
        .relationships {{ border-left: 4px solid #6610f2; }}
        .stats {{ display: flex; gap: 20px; margin: 20px 0; }}
        .stat-box {{ background: white; padding: 15px; border: 1px solid #dee2e6; border-radius: 6px; text-align: center; flex: 1; }}
        .indicator-table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
        .indicator-table th, .indicator-table td {{ padding: 12px; text-align: left; border-bottom: 1px solid #dee2e6; }}
        .indicator-table th {{ background: #f8f9fa; font-weight: 600; }}
        .indicator-item {{ background: #f8f9fa; padding: 10px; margin: 8px 0; border-radius: 4px; border-left: 3px solid #6c757d; }}
        .span-ref {{ font-family: monospace; background: #e9ecef; padding: 2px 6px; border-radius: 3px; font-size: 0.85em; color: #6c757d; }}
        .count-badge {{ background: #17a2b8; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.85em; margin-left: 8px; }}
        h2 {{ color: #495057; border-bottom: 2px solid #e9ecef; padding-bottom: 8px; }}
        .findings-list li {{ margin: 8px 0; }}
        .no-data {{ text-align: center; color: #6c757d; font-style: italic; padding: 20px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🛡️ Safety Sigma Demo Report</h1>
        <p><strong>Source PDF:</strong> {pdf_path.name}</p>
        <p><strong>Processing Mode:</strong> Zero-inference with exact preservation</p>
        <p><strong>Generated:</strong> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>

    <div class="section">
        <h2>📊 Extraction Summary</h2>
        <div class="stats">
            <div class="stat-box">
                <strong>{len(indicators)}</strong><br>
                Total Indicators
            </div>
            <div class="stat-box">
                <strong>{len(display_indicators)}</strong><br>
                Unique for Display
            </div>
            <div class="stat-box">
                <strong>{len(set(ind['category_id'] for ind in indicators))}</strong><br>
                Categories
            </div>
            <div class="stat-box">
                <strong>{len([ind for ind in indicators if ind.get('count', 1) > 1])}</strong><br>
                Duplicates Found
            </div>
        </div>
    </div>
"""

    # Advisory section if available
    if advisory_content:
        html += f"""
    <div class="advisory-banner">
        <strong>NON-AUTHORITATIVE Advisory Content Below</strong> — 
        For analyst convenience only. Verify against authoritative artifacts.
    </div>
    <div class="section">
        <h2>📝 Advisory Narrative</h2>
        <div style="background: #f8f9fa; padding: 15px; border-radius: 6px;">
            <pre style="white-space: pre-wrap; margin: 0; font-family: inherit;">{advisory_content}</pre>
        </div>
    </div>
"""

    # Findings section  
    if findings:
        html += """
    <div class="section findings">
        <h2>🔍 Key Findings (literal-stitch)</h2>
        <ul class="findings-list">
"""
        for finding in findings:
            html += f"            <li>{finding}</li>\n"
        html += """        </ul>
    </div>
"""

    # Financial section
    if by_kind.get('amount') or by_kind.get('account'):
        html += """
    <div class="section financial">
        <h2>💰 Financial Indicators</h2>
        <table class="indicator-table">
            <thead>
                <tr><th>Type</th><th>Value</th><th>Span Reference</th><th>Notes</th></tr>
            </thead>
            <tbody>
"""
        for item in by_kind.get('amount', []) + by_kind.get('account', []):
            count_badge = f'<span class="count-badge">{item.get("count", 1)}x</span>' if item.get('count', 1) > 1 else ''
            span_info = f"<span class='span-ref'>{item['span_id']}</span>"
            if item.get('all_span_ids'):
                span_info = f"<span class='span-ref' title='{', '.join(item['all_span_ids'])}'>{item['span_id']} +{len(item['all_span_ids'])-1}</span>"
            
            html += f"""                <tr>
                    <td>{item['kind'].title()}</td>
                    <td><strong>{item.get('display_value', item['verbatim'])}</strong>{count_badge}</td>
                    <td>{span_info}</td>
                    <td>{item.get('display_note', '')}</td>
                </tr>
"""
        html += """            </tbody>
        </table>
    </div>
"""

    # Infrastructure section
    if by_kind.get('domain') or by_kind.get('phone') or by_kind.get('email'):
        html += """
    <div class="section infrastructure">
        <h2>🌐 Infrastructure Indicators</h2>
        <table class="indicator-table">
            <thead>
                <tr><th>Type</th><th>Value</th><th>Span Reference</th><th>Notes</th></tr>
            </thead>
            <tbody>
"""
        for item in by_kind.get('domain', []) + by_kind.get('phone', []) + by_kind.get('email', []):
            count_badge = f'<span class="count-badge">{item.get("count", 1)}x</span>' if item.get('count', 1) > 1 else ''
            span_info = f"<span class='span-ref'>{item['span_id']}</span>"
            if item.get('all_span_ids'):
                span_info = f"<span class='span-ref' title='{', '.join(item['all_span_ids'])}'>{item['span_id']} +{len(item['all_span_ids'])-1}</span>"
            
            html += f"""                <tr>
                    <td>{item['kind'].title()}</td>
                    <td><strong>{item.get('display_value', item['verbatim'])}</strong>{count_badge}</td>
                    <td>{span_info}</td>
                    <td>{item.get('display_note', '')}</td>
                </tr>
"""
        html += """            </tbody>
        </table>
    </div>
"""

    # Behaviors section
    if by_kind.get('behavior'):
        html += """
    <div class="section behaviors">
        <h2>🎯 Behavior Patterns</h2>
"""
        for item in by_kind['behavior']:
            count_badge = f'<span class="count-badge">{item.get("count", 1)}x</span>' if item.get('count', 1) > 1 else ''
            span_ref = f"<span class='span-ref'>{item['span_id']}</span>"
            html += f"""        <div class="indicator-item">
            <strong>{item.get('display_value', item['verbatim'])}</strong>{count_badge} {span_ref}
        </div>
"""
        html += "    </div>\n"

    # Relationships section (if links exist)
    links = rules_json.get('json', {}).get('links', [])
    if links:
        html += """
    <div class="section relationships">
        <h2>🔗 Explicit Relationships</h2>
        <table class="indicator-table">
            <thead>
                <tr><th>From</th><th>To</th><th>Relationship</th></tr>
            </thead>
            <tbody>
"""
        for link in links:
            html += f"""                <tr>
                    <td>{link.get('from_value', 'N/A')}</td>
                    <td>{link.get('to_value', 'N/A')}</td>
                    <td>{link.get('relationship', 'linked')}</td>
                </tr>
"""
        html += """            </tbody>
        </table>
    </div>
"""

    html += """
    <div class="section">
        <h2>⚖️ Processing Compliance</h2>
        <ul>
            <li><strong>Zero-inference:</strong> All indicators preserved exactly as found in source</li>
            <li><strong>Exact preservation:</strong> Verbatim text maintained in rules.json</li>
            <li><strong>Display cleanup:</strong> HTML rendering may clean punctuation for readability</li>
            <li><strong>Audit trail:</strong> Every indicator includes source span reference</li>
            <li><strong>Category grounding:</strong> Categories derive from literal content patterns</li>
        </ul>
    </div>

    <div style="text-align: center; margin-top: 40px; padding: 20px; border-top: 1px solid #dee2e6; color: #6c757d;">
        <p>Generated by Safety Sigma v2.0 | Zero-inference processing | Analyst readiness enhanced</p>
    </div>
</body>
</html>"""

    return html

def compile_to_rules(indicators: List[Dict[str, Any]], categories: Dict[str, Any], source_path: str = "unknown") -> Dict[str, Any]:
    """Compile indicators to rules format (preserve exact data for V-001..V-005)"""
    
    # Build regex rules
    regex_rules = []
    for ind in indicators:
        verbatim = ind.get('verbatim', '')
        if verbatim:
            # Escape special regex characters for exact matching
            pattern = re.escape(verbatim)
            regex_rules.append({
                "pattern": pattern,
                "meta": {
                    "name": verbatim,
                    "kind": ind['kind'],
                    "source_span": {
                        "category_id": ind['category_id'],
                        "span_id": ind['span_id']
                    },
                    "provenance": {"stage": "compile", "version": "v0.2"}
                }
            })
    
    # Build JSON output (preserve all fields for validation)
    json_indicators = []
    for ind in indicators:
        json_ind = {
            "kind": ind['kind'],
            "category_id": ind['category_id'], 
            "span_id": ind['span_id']
        }
        if 'verbatim' in ind:
            json_ind['verbatim'] = ind['verbatim']
        if 'numeric' in ind:
            json_ind['numeric'] = ind['numeric']
        if 'literal' in ind:
            json_ind['literal'] = ind['literal']
        
        # Add provenance
        json_ind.update({
            "source_span": {"category_id": ind['category_id'], "span_id": ind['span_id']},
            "provenance": {"stage": "compile", "version": "v0.2"}
        })
        
        json_indicators.append(json_ind)
    
    return {
        "source": str(source_path),
        "processing_mode": "zero-inference",
        "ir": {
            "extractions": [],
            "indicators": json_indicators
        },
        "regex": {
            "rules": regex_rules
        },
        "json": {
            "categories": categories,
            "indicators": json_indicators  
        }
    }

def main():
    parser = argparse.ArgumentParser(description="Demo PDF to Rules with enhanced HTML")
    parser.add_argument("--pdf", required=True, help="Path to PDF file")
    parser.add_argument("--json-out", required=True, help="Output path for rules JSON")
    parser.add_argument("--html-out", required=True, help="Output path for HTML report")
    
    args = parser.parse_args()
    
    pdf_path = Path(args.pdf)
    json_path = Path(args.json_out)
    html_path = Path(args.html_out)
    
    print(f"🔄 Processing PDF: {pdf_path}")
    
    # Extract text
    text = extract_text_from_pdf(pdf_path)
    print(f"📄 Extracted {len(text)} characters from PDF")
    
    # Extract indicators
    indicators = extract_indicators(text)
    print(f"🔍 Found {len(indicators)} indicators")
    
    # Build categories
    categories = {}
    for ind in indicators:
        cat_id = ind['category_id']
        if cat_id not in categories:
            categories[cat_id] = {"name": cat_id, "description": f"Category: {cat_id}"}
    
    # Compile to rules
    rules_json = compile_to_rules(indicators, categories, pdf_path)
    print(f"⚙️ Generated {len(rules_json.keys())} artifact types")
    
    # Save JSON
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(rules_json, indent=2, ensure_ascii=False))
    print(f"💾 Saved JSON to: {json_path}")
    
    # Load advisory content if available
    advisory_content = ""
    advisory_path = Path("advisory/narrative_advisory.md")
    if advisory_path.exists():
        advisory_content = advisory_path.read_text(encoding="utf-8")
    
    # Generate HTML
    html_content = generate_html_report(pdf_path, indicators, rules_json, advisory_content)
    
    html_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.write_text(html_content, encoding="utf-8")
    print(f"📊 Saved HTML report to: {html_path}")
    
    print("✅ Demo completed successfully!")

if __name__ == "__main__":
    main()