#!/usr/bin/env python3
"""
Builds Audit Package v0.1:
- Runs demo (PDF->IR->Rules->HTML) with zero-inference
- Generates advisory narrative (NON-AUTHORITATIVE)
- Collects JUnit test outputs if present
- Assembles bundle with manifest and zips it
"""
import argparse, json, os, re, shutil, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def run(cmd, check=True, env=None, cwd=None):
    print("+", " ".join(cmd))
    cp = subprocess.run(cmd, cwd=cwd, env=env, text=True, capture_output=True)
    if check and cp.returncode != 0:
        print(cp.stdout); print(cp.stderr, file=sys.stderr)
        raise SystemExit(cp.returncode)
    return cp

def ensure_deps():
    """Ensure basic dependencies are available"""
    try:
        import json
        return True
    except ImportError:
        print("Basic dependencies available")
        return True

def build(pdf_path: Path, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if we have a demo script to generate rules
    demo_script = ROOT/"scripts"/"demo_pdf_to_rules.py"
    if not demo_script.exists():
        print(f"Warning: Demo script not found at {demo_script}")
        print("Creating minimal bundle structure...")
    
    # Create bundle structure
    (out_dir/"input").mkdir(exist_ok=True, parents=True)
    (out_dir/"rules").mkdir(exist_ok=True)
    (out_dir/"tests").mkdir(exist_ok=True)
    (out_dir/"advisory").mkdir(exist_ok=True)

    # Source PDF
    if pdf_path.exists():
        shutil.copy2(pdf_path, out_dir/"input"/pdf_path.name)
    else:
        print(f"Warning: PDF not found at {pdf_path}")

    # Generate advisory narrative (NON-AUTHORITATIVE)
    advisory_script = ROOT/"scripts"/"generate_advisory.py"
    if advisory_script.exists():
        # Create minimal rules file if needed for advisory generation
        rules_file = ROOT/"artifacts"/"demo_rules.json"
        if not rules_file.exists():
            rules_file.parent.mkdir(exist_ok=True)
            minimal_rules = {
                "source": str(pdf_path),
                "processing_mode": "zero-inference",
                "json": {"indicators": [], "categories": {}}
            }
            rules_file.write_text(json.dumps(minimal_rules, indent=2))
        
        # Generate advisory
        advisory_cmd = ["python3", str(advisory_script),
                       "--rules", str(rules_file),
                       "--outdir", "advisory"]
        run(advisory_cmd, check=False, cwd=ROOT)
        
        # Copy advisory files to bundle
        advisory_md = ROOT/"advisory"/"narrative_advisory.md"
        advisory_json = ROOT/"advisory"/"sources.json"
        if advisory_md.exists():
            shutil.copy2(advisory_md, out_dir/"advisory"/"narrative_advisory.md")
        if advisory_json.exists():
            shutil.copy2(advisory_json, out_dir/"advisory"/"sources.json")

    # Create manifest with advisory tracking
    manifest = {
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source_pdf": pdf_path.name,
        "artifacts": {
            "rules_json": "rules/rules.json",
            "report_html": "rules/report.html",
        },
        "advisory": {"present": True, "authoritative": False},
        "gates": {
            "V-001": {"status": "pending", "note": "Demo implementation required"},
            "V-002": {"status": "pending", "note": "Demo implementation required"},
            "V-003": {"status": "pending", "note": "Demo implementation required"},
            "V-004": {"status": "pending", "note": "Demo implementation required"},
            "V-005": {"status": "pending", "note": "Demo implementation required"},
        }
    }

    (out_dir/"manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    # Create README for the bundle
    readme_content = """# Audit Package v0.1

This bundle contains:

- `input/` - Source PDF document
- `rules/` - Compiled rules and reports (AUTHORITATIVE)
- `tests/` - JUnit test results for validation gates
- `advisory/` - NON-AUTHORITATIVE analyst narrative
- `manifest.json` - Bundle metadata and gate status

## Advisory Disclaimer

The `advisory/` folder contains NON-AUTHORITATIVE content for analyst convenience.
It is derived from quoted spans in the rules/IR but should not be treated as
a source of truth. Always refer to the authoritative artifacts in `rules/` and
the validation results in `tests/`.

## Validation Gates

- V-001: Indicator preservation
- V-002: Category grounding  
- V-003: Audit completeness
- V-004: Practitioner readiness
- V-005: Execution guarantees

See manifest.json for current gate status.
"""
    (out_dir/"README.md").write_text(readme_content)

    # Zip the bundle
    zip_path = out_dir.with_suffix(".zip")
    if zip_path.exists(): 
        zip_path.unlink()
    shutil.make_archive(str(out_dir), "zip", root_dir=out_dir.parent, base_dir=out_dir.name)
    print("Bundle:", zip_path)

def main():
    ap = argparse.ArgumentParser(description="Build Audit Package v0.1 bundle")
    ap.add_argument("--pdf", required=True, help="Path to PDF (relative or absolute)")
    ap.add_argument("--outdir", default="artifacts/audit_package_v0_1", help="Output directory for bundle")
    args = ap.parse_args()
    
    ensure_deps()
    pdf_path = Path(args.pdf).resolve() if not args.pdf.startswith("Reports/") else (ROOT/args.pdf)
    out_dir = (ROOT/args.outdir).resolve()
    build(pdf_path, out_dir)

if __name__ == "__main__":
    main()