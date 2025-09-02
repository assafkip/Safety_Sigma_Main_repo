#!/usr/bin/env python3
"""
Safety Sigma LLM Pipeline CLI

Command-line interface for running the complete LLM integration pipeline:
- Processes PDF documents through existing extractor
- Structures extractions into IR Schema v0.4 using LLM
- Compiles deployable rules preserving indicators exactly
- Generates practitioner narratives with verbatim quoted spans
- Produces complete audit trail with validation reports

Usage:
    python scripts/run_llm_pipeline.py --doc path/to/document.pdf --config configs/llm_dev.yaml --out output/
"""

import argparse
import json
import yaml
import sys
import time
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from llm_integration.adapter import LLMAdapter
from llm_integration.audit import AuditLogger, AuditContext
from llm_integration.validator import ValidationGateChecker


def load_config(config_path: Path) -> Dict[str, Any]:
    """Load YAML configuration file"""
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        if config_path.suffix.lower() == '.yaml':
            return yaml.safe_load(f)
        else:
            return json.load(f)


def extract_from_pdf(pdf_path: Path, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract text and spans from PDF using existing extractor
    Returns source document structure with extractions
    """
    try:
        # Use existing demo script functionality
        from scripts.demo_pdf_to_rules import extract_text_with_pypdf2, extract_indicators
        
        print(f"📄 Processing PDF: {pdf_path}")
        
        # Extract text
        full_text = extract_text_with_pypdf2(pdf_path)
        print(f"📄 Extracted {len(full_text)} characters from PDF")
        
        # Extract indicators using existing logic
        indicators = extract_indicators(full_text)
        print(f"🔍 Found {len(indicators)} indicators")
        
        # Convert to expected format
        extractions_raw = []
        for idx, indicator in enumerate(indicators):
            extraction = {
                "value": indicator.get("verbatim", indicator.get("literal", "")),
                "kind": indicator.get("kind", "text"),
                "page": 1,  # Simplified - would need proper page mapping
                "start": indicator.get("start", 0),
                "end": indicator.get("end", len(indicator.get("verbatim", ""))),
                "category_id": indicator.get("category_id", f"cat_{idx}"),
                "span_id": indicator.get("span_id", f"span_{idx}")
            }
            extractions_raw.append(extraction)
        
        source_doc = {
            "id": pdf_path.stem,
            "path": str(pdf_path),
            "pages": 1,  # Simplified
            "total_chars": len(full_text),
            "extraction_timestamp": time.time()
        }
        
        return {
            "source_doc": source_doc,
            "extractions_raw": extractions_raw
        }
        
    except ImportError:
        # Fallback if demo script not available
        print("Warning: Using minimal fallback extraction")
        return {
            "source_doc": {
                "id": pdf_path.stem,
                "path": str(pdf_path),
                "pages": 1
            },
            "extractions_raw": []
        }


def run_llm_pipeline(doc_path: Path, config_path: Path, output_dir: Path) -> Dict[str, Any]:
    """
    Run complete LLM integration pipeline
    
    Returns:
        Pipeline execution report
    """
    print("🚀 Starting Safety Sigma LLM Pipeline")
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load configuration
    print(f"⚙️ Loading config from {config_path}")
    config = load_config(config_path)
    
    # Initialize audit logger
    audit_log_path = output_dir / "audit" / "log.jsonl"
    audit_logger = AuditLogger(audit_log_path, redact_sensitive=config.get("redact_sensitive", True))
    
    run_id = f"pipeline_{int(time.time())}_{doc_path.stem}"
    
    with AuditContext(audit_logger, run_id, "llm_pipeline") as audit_ctx:
        try:
            # Step 1: Extract from PDF
            print("📑 Step 1: Extracting from PDF...")
            extraction_data = extract_from_pdf(doc_path, config)
            
            audit_logger.append({
                "event": "pdf_extraction_complete",
                "run_id": run_id,
                "source_doc": extraction_data["source_doc"],
                "extractions_count": len(extraction_data["extractions_raw"])
            })
            
            # Step 2: Initialize LLM adapter
            print("🤖 Step 2: Initializing LLM integration...")
            adapter = LLMAdapter(config, audit_logger)
            
            # Step 3: Build IR
            print("🏗️ Step 3: Building IR from extractions...")
            ir = adapter.build_ir(
                extraction_data["extractions_raw"],
                extraction_data["source_doc"], 
                config
            )
            
            # Save IR
            ir_path = output_dir / "ir.json"
            with open(ir_path, 'w', encoding='utf-8') as f:
                json.dump(ir, f, indent=2, ensure_ascii=False)
            print(f"💾 Saved IR to: {ir_path}")
            
            # Step 4: Compile rules
            print("⚙️ Step 4: Compiling rules...")
            rules = adapter.compile_rules(ir, config)
            
            # Save rules
            rules_dir = output_dir / "rules"
            rules_dir.mkdir(exist_ok=True)
            
            for target, content in rules.items():
                rule_path = rules_dir / f"rules.{target}"
                with open(rule_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"💾 Saved {target} rules to: {rule_path}")
            
            # Step 5: Generate narrative
            print("📝 Step 5: Generating practitioner narrative...")
            narrative = adapter.draft_narrative(ir, extraction_data["source_doc"])
            
            # Save narrative
            narrative_path = output_dir / "narrative.md"
            with open(narrative_path, 'w', encoding='utf-8') as f:
                f.write(narrative)
            print(f"💾 Saved narrative to: {narrative_path}")
            
            # Step 6: Validation
            print("✅ Step 6: Running validation gates...")
            validator = ValidationGateChecker()
            validation_report = validator.check_all_gates(ir, rules, config)
            
            # Save validation report
            validation_path = output_dir / "validation_report.json"
            with open(validation_path, 'w', encoding='utf-8') as f:
                json.dump(validation_report, f, indent=2, ensure_ascii=False)
            print(f"💾 Saved validation report to: {validation_path}")
            
            # Step 7: Generate pipeline report
            pipeline_report = {
                "pipeline_id": run_id,
                "timestamp": time.time(),
                "config": config,
                "source_document": extraction_data["source_doc"],
                "processing_stats": {
                    "extractions_processed": len(extraction_data["extractions_raw"]),
                    "ir_extractions": len(ir.get("extractions", [])),
                    "rules_generated": list(rules.keys()),
                    "narrative_length": len(narrative)
                },
                "validation": validation_report,
                "outputs": {
                    "ir": str(ir_path),
                    "rules": [str(rules_dir / f"rules.{target}") for target in rules.keys()],
                    "narrative": str(narrative_path),
                    "validation_report": str(validation_path),
                    "audit_log": str(audit_log_path)
                }
            }
            
            # Save pipeline report
            report_path = output_dir / "pipeline_report.json"
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(pipeline_report, f, indent=2, ensure_ascii=False)
            print(f"💾 Saved pipeline report to: {report_path}")
            
            # Print summary
            print("\\n" + "="*60)
            print("🎉 PIPELINE COMPLETED SUCCESSFULLY")
            print("="*60)
            print(f"📊 Processed: {len(extraction_data['extractions_raw'])} extractions")
            print(f"🏗️ Generated: {len(ir.get('extractions', []))} IR objects") 
            print(f"⚙️ Rules: {', '.join(rules.keys())}")
            print(f"✅ Validation: {'PASSED' if validation_report['all_gates_passed'] else 'FAILED'}")
            
            if not validation_report["all_gates_passed"]:
                print("❌ Failed gates:")
                for gate_id, gate_data in validation_report["gates"].items():
                    if not gate_data.get("passed", False):
                        print(f"   {gate_id}: {gate_data.get('issues', ['Unknown issue'])}")
            
            print(f"📁 Outputs saved to: {output_dir}")
            print("="*60)
            
            return pipeline_report
            
        except Exception as e:
            audit_logger.append({
                "event": "pipeline_error",
                "run_id": run_id,
                "error": str(e),
                "error_type": type(e).__name__
            })
            print(f"❌ Pipeline failed: {e}")
            raise


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Safety Sigma LLM Integration Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/run_llm_pipeline.py --doc report.pdf --config configs/llm_dev.yaml --out output/
  python scripts/run_llm_pipeline.py --doc /path/to/intel.pdf --out results/ --config dev.yaml

Outputs:
  ir.json                 - IR Schema v0.4 structured extractions
  rules/rules.regex       - Regex rules preserving exact indicators
  rules/rules.json        - JSON rule format
  rules/rules.python      - Python detection functions (if enabled)
  rules/rules.sql         - SQL queries (if enabled)
  narrative.md            - Practitioner narrative with verbatim quotes
  validation_report.json  - V-001 through V-005 gate validation
  audit/log.jsonl         - Complete tamper-evident audit trail
  pipeline_report.json    - Summary report with all metadata
"""
    )
    
    parser.add_argument(
        "--doc", 
        required=True,
        type=Path,
        help="Path to PDF document to process"
    )
    
    parser.add_argument(
        "--config",
        type=Path, 
        default="configs/llm_dev.yaml",
        help="Path to configuration file (YAML or JSON)"
    )
    
    parser.add_argument(
        "--out",
        type=Path,
        default="artifacts/llm_pipeline_output",
        help="Output directory for all generated files"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    parser.add_argument(
        "--validate-only",
        action="store_true", 
        help="Only run validation on existing IR/rules (skip processing)"
    )
    
    args = parser.parse_args()
    
    # Validate inputs
    if not args.doc.exists():
        print(f"❌ Error: Document not found: {args.doc}")
        sys.exit(1)
    
    if not args.config.exists():
        print(f"❌ Error: Config file not found: {args.config}")
        sys.exit(1)
    
    try:
        if args.validate_only:
            # Validation-only mode
            print("🔍 Running validation-only mode...")
            # TODO: Implement validation-only mode
            print("❌ Validation-only mode not yet implemented")
            sys.exit(1)
        else:
            # Full pipeline mode
            report = run_llm_pipeline(args.doc, args.config, args.out)
            
            # Exit with appropriate code
            if report["validation"]["all_gates_passed"]:
                print("✅ All validation gates passed")
                sys.exit(0)
            else:
                print("❌ Some validation gates failed")
                sys.exit(1)
                
    except KeyboardInterrupt:
        print("\\n⏹️ Pipeline interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"💥 Pipeline failed with error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()