#!/usr/bin/env python3
import json, yaml
from pathlib import Path
from src.metrics.confidence import score_from_metrics

def main():
    """Batch annotator for advisory items with confidence scoring and risk tier assignment."""
    root = Path(__file__).resolve().parents[1]
    art = root/"artifacts"
    
    # Load risk tier configuration
    tiers_path = root/"configs"/"risk_tiers.yaml"
    if not tiers_path.exists():
        print(f"Warning: {tiers_path} not found, using defaults")
        tiers = {
            "tiers": {
                "blocking": {"max_fpr": 0.005, "min_confidence": 0.90},
                "hunting": {"max_fpr": 0.02, "min_confidence": 0.70},
                "enrichment": {"max_fpr": 0.10, "min_confidence": 0.40}
            }
        }
    else:
        tiers = yaml.safe_load(tiers_path.read_text(encoding="utf-8"))
    
    # Load backtest results
    bt_path = art/"proactive"/"backtest_report.json"
    if bt_path.exists():
        bt = json.loads(bt_path.read_text(encoding="utf-8"))
    else:
        print("Warning: No backtest results found, using zero metrics")
        bt = {"rules": {}}

    # Annotate expansions with metrics+confidence+tier
    exp_path = art/"proactive"/"expansions.json"
    if exp_path.exists():
        exp = json.loads(exp_path.read_text(encoding="utf-8"))
        
        for e in exp.get("expansions", []):
            pat = e.get("pattern", "")
            
            # Get backtest metrics for this pattern
            m = bt.get("rules", {}).get(pat, {
                "false_positive_rate": 1.0,
                "true_positive_rate": 0.0, 
                "samples_tested": 0,
                "matches": 0,
                "tp": 0,
                "fp": 0
            })
            
            fpr = m.get("false_positive_rate", 1.0)
            tpr = m.get("true_positive_rate", 0.0)
            n = m.get("samples_tested", 0)
            
            # Calculate confidence score
            conf = score_from_metrics(fpr, tpr, n)
            
            # Add metrics and confidence to expansion
            e["metrics"] = m
            e["confidence_score"] = conf
            
            # Assign risk tier based on policy
            tier_config = tiers["tiers"]
            if (fpr <= tier_config["blocking"]["max_fpr"] and 
                conf >= tier_config["blocking"]["min_confidence"]):
                e["risk_tier"] = "blocking"
            elif (fpr <= tier_config["hunting"]["max_fpr"] and 
                  conf >= tier_config["hunting"]["min_confidence"]):
                e["risk_tier"] = "hunting"
            else:
                e["risk_tier"] = "enrichment"
        
        # Write updated expansions
        exp_path.write_text(json.dumps(exp, indent=2), encoding="utf-8")
        print(f"Annotated {len(exp.get('expansions', []))} expansions with metrics/confidence/risk_tier")
    else:
        print("Warning: No expansions file found to annotate")

if __name__ == "__main__":
    main()