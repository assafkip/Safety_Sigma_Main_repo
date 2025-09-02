#!/usr/bin/env python3
"""
Backtest Rules v0.1 - Local Performance Evaluation

Tests compiled rules against a CSV dataset with optional labels.
NO external IO; pure local execution for compliance.
"""
import argparse
import csv
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional

def load_rules(rules_path: Path) -> Dict[str, Any]:
    """Load compiled rules from JSON file"""
    if not rules_path.exists():
        raise FileNotFoundError(f"Rules file not found: {rules_path}")
    
    rules_data = json.loads(rules_path.read_text(encoding="utf-8"))
    return rules_data

def load_csv_data(csv_path: Path) -> List[Dict[str, str]]:
    """Load CSV data with text column and optional label column"""
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    data = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if 'text' not in row:
                raise ValueError("CSV must contain 'text' column")
            data.append(row)
    
    return data

def extract_regex_rules(rules_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract regex rules from compiled rules data"""
    regex_rules = []
    
    # Check for regex section in rules
    if 'regex' in rules_data and 'rules' in rules_data['regex']:
        for rule in rules_data['regex']['rules']:
            if 'pattern' in rule:
                regex_rules.append({
                    'pattern': rule['pattern'],
                    'name': rule.get('meta', {}).get('name', 'unnamed'),
                    'kind': rule.get('meta', {}).get('kind', 'unknown'),
                    'source_span': rule.get('meta', {}).get('source_span', {}),
                })
    
    return regex_rules

def test_rule_against_text(pattern: str, text: str) -> List[str]:
    """Test a single regex pattern against text, return matches"""
    try:
        matches = re.findall(pattern, text, re.IGNORECASE)
        return matches if isinstance(matches, list) else [matches] if matches else []
    except re.error:
        # Invalid regex pattern
        return []

def compute_precision_proxy(matches_by_rule: Dict[str, int], 
                          labels: Optional[List[str]], 
                          positive_labels: set = {"malicious", "fraud", "scam", "threat"}) -> Dict[str, float]:
    """Compute precision proxy if labels available"""
    if not labels:
        return {}
    
    precision_scores = {}
    total_positive = sum(1 for label in labels if label.lower() in positive_labels)
    
    if total_positive == 0:
        return {}
    
    for rule_name, match_count in matches_by_rule.items():
        if match_count > 0:
            # Simple proxy: matches in positive samples / total matches
            # Real precision would need more sophisticated evaluation
            precision_scores[rule_name] = min(match_count / total_positive, 1.0)
    
    return precision_scores

def run_backtest(rules_path: Path, csv_path: Path, output_path: Path):
    """Run backtest evaluation"""
    print(f"Loading rules from {rules_path}")
    rules_data = load_rules(rules_path)
    
    print(f"Loading CSV data from {csv_path}")
    csv_data = load_csv_data(csv_path)
    
    print(f"Extracting regex rules...")
    regex_rules = extract_regex_rules(rules_data)
    
    if not regex_rules:
        print("Warning: No regex rules found in rules file")
        return
    
    print(f"Testing {len(regex_rules)} rules against {len(csv_data)} samples")
    
    # Initialize counters
    matches_by_rule = {rule['name']: 0 for rule in regex_rules}
    rule_details = {rule['name']: rule for rule in regex_rules}
    
    # Extract labels if present
    labels = [row.get('label', '') for row in csv_data] if 'label' in csv_data[0] else None
    
    # Test each rule against each text sample
    for i, row in enumerate(csv_data):
        text = row['text']
        
        for rule in regex_rules:
            pattern = rule['pattern']
            rule_name = rule['name']
            
            matches = test_rule_against_text(pattern, text)
            if matches:
                matches_by_rule[rule_name] += len(matches)
    
    # Compute precision proxy if labels available
    precision_scores = compute_precision_proxy(matches_by_rule, labels)
    
    # Generate summary
    summary = {
        "backtest_metadata": {
            "rules_file": str(rules_path),
            "csv_file": str(csv_path),
            "total_samples": len(csv_data),
            "total_rules": len(regex_rules),
            "has_labels": labels is not None,
        },
        "rule_performance": {},
        "summary_stats": {
            "rules_with_matches": sum(1 for count in matches_by_rule.values() if count > 0),
            "total_matches": sum(matches_by_rule.values()),
            "avg_matches_per_rule": sum(matches_by_rule.values()) / len(regex_rules) if regex_rules else 0,
        }
    }
    
    # Add rule details
    for rule_name, match_count in matches_by_rule.items():
        rule_info = rule_details[rule_name]
        summary["rule_performance"][rule_name] = {
            "matches": match_count,
            "kind": rule_info.get('kind', 'unknown'),
            "pattern": rule_info.get('pattern', ''),
            "source_span": rule_info.get('source_span', {}),
        }
        
        if precision_scores and rule_name in precision_scores:
            summary["rule_performance"][rule_name]["precision_proxy"] = precision_scores[rule_name]
    
    # Save results
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    
    print(f"Backtest complete. Results saved to {output_path}")
    print(f"Rules with matches: {summary['summary_stats']['rules_with_matches']}")
    print(f"Total matches: {summary['summary_stats']['total_matches']}")

def main():
    parser = argparse.ArgumentParser(description="Backtest compiled rules against CSV dataset")
    parser.add_argument("--csv", required=True, help="Path to CSV file with 'text' column")
    parser.add_argument("--rules", default="artifacts/demo_rules.json", help="Path to compiled rules JSON")
    parser.add_argument("--output", default="artifacts/backtest_summary.json", help="Output path for results")
    
    args = parser.parse_args()
    
    csv_path = Path(args.csv)
    rules_path = Path(args.rules)
    output_path = Path(args.output)
    
    try:
        run_backtest(rules_path, csv_path, output_path)
    except Exception as e:
        print(f"Backtest failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())