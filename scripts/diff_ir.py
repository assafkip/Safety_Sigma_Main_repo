#!/usr/bin/env python3
"""
Safety Sigma IR Diff Tool

Compares indicators and categories between scripted JSON and LLM ir.json.
Prints human-readable diff showing:
- Indicators found in both pipelines
- Indicators unique to scripted pipeline  
- Indicators unique to LLM pipeline
- Category differences
- Provenance comparison

Usage:
    python scripts/diff_ir.py [--scripted path] [--llm path] [--format text|json]
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Set, Any, Tuple
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class IndicatorInfo:
    """Information about an indicator"""
    value: str
    kind: str
    category: str = ""
    provenance: Dict[str, Any] = None
    source: str = ""  # "scripted" or "llm"
    

class IRDiffer:
    """Compare indicators and categories between scripted and LLM IR"""
    
    def __init__(self):
        self.scripted_indicators: List[IndicatorInfo] = []
        self.llm_indicators: List[IndicatorInfo] = []
        
    def load_scripted_ir(self, path: Path) -> None:
        """Load indicators from scripted rules.json"""
        if not path.exists():
            raise FileNotFoundError(f"Scripted file not found: {path}")
            
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract from various sections of scripted output
        indicators = []
        
        # From IR section
        ir_section = data.get("ir", {})
        if "indicators" in ir_section:
            for ind in ir_section["indicators"]:
                indicators.append(IndicatorInfo(
                    value=ind.get("verbatim", ind.get("literal", "")),
                    kind=ind.get("kind", "unknown"),
                    category=ind.get("category_id", ""),
                    provenance=ind.get("source_span", {}),
                    source="scripted"
                ))
        
        # From JSON section 
        json_section = data.get("json", {})
        if "indicators" in json_section:
            for ind in json_section["indicators"]:
                # Avoid duplicates from IR section
                value = ind.get("verbatim", ind.get("literal", ""))
                if not any(i.value == value for i in indicators):
                    indicators.append(IndicatorInfo(
                        value=value,
                        kind=ind.get("kind", "unknown"),
                        category=ind.get("category_id", ""),
                        provenance=ind.get("source_span", {}),
                        source="scripted"
                    ))
        
        self.scripted_indicators = indicators
        
    def load_llm_ir(self, path: Path) -> None:
        """Load indicators from LLM ir.json"""
        if not path.exists():
            raise FileNotFoundError(f"LLM IR file not found: {path}")
            
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        indicators = []
        extractions = data.get("extractions", [])
        
        for ext in extractions:
            indicators.append(IndicatorInfo(
                value=ext.get("value", ""),
                kind=ext.get("type", "unknown"),
                category="",  # LLM might not have categories
                provenance=ext.get("provenance", {}),
                source="llm"
            ))
        
        self.llm_indicators = indicators
    
    def compare_indicators(self) -> Dict[str, Any]:
        """Compare indicators between pipelines"""
        scripted_values = {ind.value for ind in self.scripted_indicators}
        llm_values = {ind.value for ind in self.llm_indicators}
        
        common = scripted_values & llm_values
        scripted_only = scripted_values - llm_values
        llm_only = llm_values - scripted_values
        
        return {
            "common": sorted(common),
            "scripted_only": sorted(scripted_only),
            "llm_only": sorted(llm_only),
            "total_scripted": len(scripted_values),
            "total_llm": len(llm_values),
            "total_common": len(common)
        }
    
    def compare_by_kind(self) -> Dict[str, Dict[str, Any]]:
        """Compare indicators grouped by kind/type"""
        scripted_by_kind = defaultdict(set)
        llm_by_kind = defaultdict(set)
        
        for ind in self.scripted_indicators:
            scripted_by_kind[ind.kind].add(ind.value)
            
        for ind in self.llm_indicators:
            llm_by_kind[ind.kind].add(ind.value)
        
        all_kinds = set(scripted_by_kind.keys()) | set(llm_by_kind.keys())
        
        comparison = {}
        for kind in all_kinds:
            scripted_vals = scripted_by_kind[kind]
            llm_vals = llm_by_kind[kind]
            
            comparison[kind] = {
                "common": sorted(scripted_vals & llm_vals),
                "scripted_only": sorted(scripted_vals - llm_vals),
                "llm_only": sorted(llm_vals - scripted_vals),
                "total_scripted": len(scripted_vals),
                "total_llm": len(llm_vals)
            }
        
        return comparison
    
    def compare_golden_indicators(self) -> Dict[str, Any]:
        """Check for critical golden indicators"""
        golden_indicators = ["$1,998.88", "VOID 2000", "wa.me/123456789"]
        
        scripted_values = {ind.value for ind in self.scripted_indicators}
        llm_values = {ind.value for ind in self.llm_indicators}
        
        golden_status = {}
        for golden in golden_indicators:
            golden_status[golden] = {
                "in_scripted": golden in scripted_values,
                "in_llm": golden in llm_values,
                "match": golden in scripted_values and golden in llm_values
            }
        
        return golden_status
    
    def compare_provenance(self) -> Dict[str, Any]:
        """Compare provenance information"""
        scripted_with_provenance = sum(1 for ind in self.scripted_indicators if ind.provenance)
        llm_with_provenance = sum(1 for ind in self.llm_indicators if ind.provenance)
        
        return {
            "scripted_with_provenance": scripted_with_provenance,
            "scripted_total": len(self.scripted_indicators),
            "llm_with_provenance": llm_with_provenance,
            "llm_total": len(self.llm_indicators),
            "scripted_provenance_rate": scripted_with_provenance / max(len(self.scripted_indicators), 1),
            "llm_provenance_rate": llm_with_provenance / max(len(self.llm_indicators), 1)
        }
    
    def generate_full_comparison(self) -> Dict[str, Any]:
        """Generate complete comparison report"""
        return {
            "summary": self.compare_indicators(),
            "by_kind": self.compare_by_kind(),
            "golden_indicators": self.compare_golden_indicators(),
            "provenance": self.compare_provenance(),
            "metadata": {
                "scripted_indicators_count": len(self.scripted_indicators),
                "llm_indicators_count": len(self.llm_indicators),
                "comparison_timestamp": "2024-09-02"  # Would use actual timestamp
            }
        }


def print_text_diff(comparison: Dict[str, Any]) -> None:
    """Print human-readable text diff"""
    summary = comparison["summary"]
    by_kind = comparison["by_kind"]
    golden = comparison["golden_indicators"]
    provenance = comparison["provenance"]
    
    print("🔍 Safety Sigma IR Pipeline Comparison")
    print("=" * 50)
    
    # Summary
    print(f"\n📊 Summary:")
    print(f"   Scripted indicators: {summary['total_scripted']}")
    print(f"   LLM indicators: {summary['total_llm']}")
    print(f"   Common indicators: {summary['total_common']}")
    print(f"   Match rate: {summary['total_common'] / max(summary['total_scripted'], summary['total_llm'], 1):.1%}")
    
    # Golden indicators
    print(f"\n⭐ Golden Indicators:")
    all_golden_match = True
    for indicator, status in golden.items():
        match_icon = "✅" if status["match"] else "❌"
        scripted_icon = "📄" if status["in_scripted"] else "❌"
        llm_icon = "🤖" if status["in_llm"] else "❌"
        print(f"   {match_icon} {indicator:20} | Scripted: {scripted_icon} | LLM: {llm_icon}")
        if not status["match"]:
            all_golden_match = False
    
    if all_golden_match:
        print("   🎉 All golden indicators preserved in both pipelines!")
    
    # Common indicators
    if summary["common"]:
        print(f"\n✅ Common Indicators ({len(summary['common'])}):")
        for indicator in summary["common"][:10]:  # Show first 10
            print(f"   • {indicator}")
        if len(summary["common"]) > 10:
            print(f"   ... and {len(summary['common']) - 10} more")
    
    # Differences
    if summary["scripted_only"]:
        print(f"\n📄 Scripted Only ({len(summary['scripted_only'])}):")
        for indicator in summary["scripted_only"][:5]:
            print(f"   • {indicator}")
        if len(summary["scripted_only"]) > 5:
            print(f"   ... and {len(summary['scripted_only']) - 5} more")
    
    if summary["llm_only"]:
        print(f"\n🤖 LLM Only ({len(summary['llm_only'])}):")
        for indicator in summary["llm_only"][:5]:
            print(f"   • {indicator}")
        if len(summary["llm_only"]) > 5:
            print(f"   ... and {len(summary['llm_only']) - 5} more")
    
    # By kind breakdown
    print(f"\n📋 By Indicator Kind:")
    for kind, data in by_kind.items():
        if data["total_scripted"] > 0 or data["total_llm"] > 0:
            match_rate = len(data["common"]) / max(data["total_scripted"], data["total_llm"], 1)
            print(f"   {kind:12} | Scripted: {data['total_scripted']:2} | LLM: {data['total_llm']:2} | Match: {match_rate:.1%}")
    
    # Provenance
    print(f"\n🔗 Provenance:")
    print(f"   Scripted: {provenance['scripted_with_provenance']}/{provenance['scripted_total']} ({provenance['scripted_provenance_rate']:.1%})")
    print(f"   LLM: {provenance['llm_with_provenance']}/{provenance['llm_total']} ({provenance['llm_provenance_rate']:.1%})")
    
    print("\n" + "=" * 50)


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Compare indicators between scripted and LLM IR",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/diff_ir.py  # Use default paths
  python scripts/diff_ir.py --scripted artifacts/demo_rules.json --llm artifacts/llm_output/ir.json
  python scripts/diff_ir.py --format json > comparison.json
"""
    )
    
    parser.add_argument(
        "--scripted",
        type=Path,
        default="artifacts/demo_rules.json",
        help="Path to scripted rules JSON file"
    )
    
    parser.add_argument(
        "--llm", 
        type=Path,
        default="artifacts/llm_output/ir.json",
        help="Path to LLM IR JSON file"
    )
    
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    try:
        differ = IRDiffer()
        
        # Load data
        if args.verbose:
            print(f"Loading scripted IR from: {args.scripted}")
        differ.load_scripted_ir(args.scripted)
        
        if args.verbose:
            print(f"Loading LLM IR from: {args.llm}")
        differ.load_llm_ir(args.llm)
        
        # Generate comparison
        comparison = differ.generate_full_comparison()
        
        # Output results
        if args.format == "json":
            print(json.dumps(comparison, indent=2, ensure_ascii=False))
        else:
            print_text_diff(comparison)
            
        # Exit with appropriate code
        golden_status = comparison["golden_indicators"]
        all_golden_preserved = all(status["match"] for status in golden_status.values())
        
        if all_golden_preserved:
            sys.exit(0)  # Success
        else:
            if args.verbose:
                print("\n⚠️ Some golden indicators not preserved in both pipelines")
            sys.exit(1)  # Failure
            
    except FileNotFoundError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        print("💡 Tip: Run pipelines first to generate artifacts for comparison", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"💥 Unexpected error: {e}", file=sys.stderr)
        sys.exit(3)


if __name__ == "__main__":
    main()