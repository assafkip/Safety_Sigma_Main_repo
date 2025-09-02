#!/usr/bin/env python3
"""
Safety Sigma 2.0 Main Entry Point

Provides command-line interface with backward compatibility to Safety Sigma 1.0
while supporting staged evolution through feature toggles.
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Optional

from safety_sigma import get_version_info, FEATURE_TOGGLES


def create_argument_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser"""
    parser = argparse.ArgumentParser(
        description="Safety Sigma 2.0 - Advanced Threat Intelligence Detection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  # Run in v1.0 parity mode (default)
  safety-sigma --pdf report.pdf --instructions prompt.md
  
  # Enable tool abstraction (Stage 1)
  SS2_ENABLE_TOOLS=true safety-sigma --pdf report.pdf --instructions prompt.md
  
  # Enable agent processing (Stage 2)
  SS2_USE_AGENT=true safety-sigma --pdf report.pdf --instructions prompt.md

Feature Toggles:
  SS2_ENABLE_TOOLS      - Tool abstraction layer (Stage 1)
  SS2_USE_AGENT         - Agent-based processing (Stage 2)  
  SS2_ENHANCE_DOCS      - Documentation enhancement (Stage 3)
  SS2_DYNAMIC_WORKFLOWS - Dynamic workflow selection (Stage 4)
  SS2_MULTI_AGENT       - Multi-agent coordination (Stage 5)
  SS2_SELF_IMPROVE      - Self-improvement loop (Stage 6)
        """
    )
    
    # Core arguments (compatible with Safety Sigma 1.0)
    parser.add_argument(
        "--pdf", "-p",
        type=str,
        required=True,
        help="Path to PDF report to process"
    )
    
    parser.add_argument(
        "--instructions", "-i", 
        type=str,
        required=True,
        help="Path to instruction markdown file"
    )
    
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=".",
        help="Output directory for results (default: current directory)"
    )
    
    # v2.0 specific arguments
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file (.env format)"
    )
    
    parser.add_argument(
        "--audit-dir",
        type=str,
        help="Directory for audit logs (default: audit_logs)"
    )
    
    parser.add_argument(
        "--simulate",
        action="store_true",
        help="Simulate processing without API calls (for testing)"
    )
    
    # Information and debugging
    parser.add_argument(
        "--version",
        action="store_true", 
        help="Show version and configuration information"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser


def load_configuration(config_path: Optional[str] = None) -> None:
    """Load configuration from .env file if specified"""
    if config_path:
        config_file = Path(config_path)
        if config_file.exists():
            # Simple .env loading (could use python-dotenv for more robust parsing)
            with open(config_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()


def get_processor_class():
    """Get the appropriate processor class based on enabled features"""
    # Import the unified processor that handles all stages
    from safety_sigma.processor import SafetySigmaProcessor
    return SafetySigmaProcessor


def main() -> None:
    """Main entry point"""
    parser = create_argument_parser()
    
    # Check for version flag before full parsing
    if len(sys.argv) > 1 and '--version' in sys.argv:
        version_info = get_version_info()
        print(f"Safety Sigma {version_info['version']}")
        print(f"Active Stage: {version_info['active_stage']}")
        print("\nFeature Toggles:")
        for feature, enabled in version_info['feature_toggles'].items():
            status = "ENABLED" if enabled else "disabled"
            print(f"  {feature}: {status}")
        print("\nCompliance Mode:")
        for setting, enabled in version_info['compliance_mode'].items():
            status = "ENABLED" if enabled else "disabled"
            print(f"  {setting}: {status}")
        return
    
    args = parser.parse_args()
    
    # Load configuration if specified
    load_configuration(args.config)
    
    # Validate required files
    pdf_path = Path(args.pdf)
    instructions_path = Path(args.instructions)
    output_path = Path(args.output)
    
    if not pdf_path.exists():
        print(f"ERROR: PDF file not found: {pdf_path}")
        sys.exit(1)
    
    if not instructions_path.exists():
        print(f"ERROR: Instructions file not found: {instructions_path}")
        sys.exit(1)
    
    if not output_path.exists():
        output_path.mkdir(parents=True, exist_ok=True)
    
    # Get appropriate processor for current stage
    try:
        ProcessorClass = get_processor_class()
        processor = ProcessorClass()
        
        if args.verbose:
            version_info = get_version_info()
            print(f"Running Safety Sigma {version_info['version']}")
            print(f"Active Stage: {version_info['active_stage']}")
        
        # Process the document (v1.0 compatible interface)
        print("🔍 Reading instruction file...")
        instructions = processor.read_instruction_file(str(instructions_path))
        
        print("📄 Extracting text from PDF report...")
        report_content = processor.extract_pdf_text(str(pdf_path))
        
        print(f"📊 Report contains {len(report_content)} characters")
        
        if args.simulate:
            print("🎭 Simulating processing (no API calls)...")
            results = f"# Safety Sigma Analysis (SIMULATED)\n\nSimulated processing of {pdf_path.name}"
        else:
            print("🤖 Processing with AI...")
            results = processor.process_report(instructions, report_content)
        
        print("💾 Saving results...")
        processor.save_results(results, str(output_path))
        
        print("✅ Processing complete!")
        
    except KeyboardInterrupt:
        print("\n🛑 Processing interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()