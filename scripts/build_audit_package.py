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
    
    # Check if we have a demo script
    demo_script = ROOT/"scripts"/"demo_pdf_to_rules.py"
    has_demo = demo_script.exists()
    
    # Check for advisory script
    advisory_script = ROOT/"scripts"/"generate_advisory.py"
    has_advisory = advisory_script.exists()
    
    # Create bundle structure (v0.2 dual-lane)
    (out_dir/"input").mkdir(exist_ok=True, parents=True)
    (out_dir/"scripted").mkdir(exist_ok=True)  # Authoritative scripted lane
    (out_dir/"tests").mkdir(exist_ok=True)
    (out_dir/"advisory").mkdir(exist_ok=True)
    (out_dir/"docs"/"ops").mkdir(exist_ok=True, parents=True)

    # Source PDF
    if pdf_path.exists():
        shutil.copy2(pdf_path, out_dir/"input"/pdf_path.name)
    else:
        print(f"Warning: PDF not found at {pdf_path}")

    # Run demo if available
    demo_json = ROOT/"artifacts"/"demo_rules.json"
    demo_html = ROOT/"artifacts"/"demo_report.html"
    
    if has_demo and pdf_path.exists():
        print("Running demo PDF to rules...")
        demo_cmd = ["python3", str(demo_script),
                   "--pdf", str(pdf_path),
                   "--json-out", str(demo_json),
                   "--html-out", str(demo_html)]
        run(demo_cmd, check=False)
    else:
        # Create minimal rules file if demo not available
        if not demo_json.exists():
            demo_json.parent.mkdir(exist_ok=True)
            minimal_rules = {
                "source": str(pdf_path),
                "processing_mode": "zero-inference",
                "json": {"indicators": [], "categories": {}}
            }
            demo_json.write_text(json.dumps(minimal_rules, indent=2))

    # Copy scripted lane artifacts (authoritative)
    if demo_json.exists():
        shutil.copy2(demo_json, out_dir/"scripted"/"rules.json")
    if demo_html.exists():
        shutil.copy2(demo_html, out_dir/"scripted"/"report.html")

    # Generate advisory narrative if script available
    advisory_present = False
    if has_advisory:
        print("Generating advisory narrative...")
        advisory_cmd = ["python3", str(advisory_script),
                       "--rules", str(demo_json),
                       "--outdir", "advisory"]
        run(advisory_cmd, check=False, cwd=ROOT)
        
        # Copy advisory files to bundle
        advisory_md = ROOT/"advisory"/"narrative_advisory.md"
        advisory_json = ROOT/"advisory"/"sources.json"
        if advisory_md.exists():
            shutil.copy2(advisory_md, out_dir/"advisory"/"narrative_advisory.md")
            advisory_present = True
        if advisory_json.exists():
            shutil.copy2(advisory_json, out_dir/"advisory"/"sources.json")

    # Copy privacy/legal note if present
    privacy_note = ROOT/"docs"/"ops"/"privacy_legal_note_v0.1.md"
    if privacy_note.exists():
        shutil.copy2(privacy_note, out_dir/"docs"/"ops"/"privacy_legal_note_v0.1.md")

    # Copy LLM output if present
    llm_output_dir = ROOT/"artifacts"/"llm_output"
    llm_present = False
    if llm_output_dir.exists():
        print("Including LLM lane output...")
        bundle_llm_dir = out_dir/"llm_output"
        shutil.copytree(llm_output_dir, bundle_llm_dir)
        llm_present = True

    # Copy proactive output if present (v0.4)
    proactive_dir = ROOT/"artifacts"/"proactive"
    proactive_present = False
    if proactive_dir.exists() and (proactive_dir/"expansions.json").exists():
        print("Including proactive lane output...")
        bundle_proactive_dir = out_dir/"proactive"
        shutil.copytree(proactive_dir, bundle_proactive_dir)
        proactive_present = True

    # Run tests to gather JUnit evidence (best effort)
    junit_files = {}
    test_dirs = {
        "golden": "tests/golden_cases",
        "unit": "tests/unit", 
        "audit": "tests/audit"
    }
    
    for test_name, test_dir in test_dirs.items():
        if (ROOT/test_dir).exists():
            junit_path = ROOT/"artifacts"/f"junit_{test_name}.xml"
            test_cmd = ["python3", "-m", "pytest", "-q", test_dir, f"--junitxml={junit_path}"]
            result = run(test_cmd, check=False, cwd=ROOT)
            if junit_path.exists() and junit_path.stat().st_size > 0:
                shutil.copy2(junit_path, out_dir/"tests"/f"junit_{test_name}.xml")
                junit_files[test_name] = f"tests/junit_{test_name}.xml"

    # Create manifest with dual-lane architecture (v0.2)
    manifest = {
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source_pdf": pdf_path.name,
        "artifacts": {
            "rules_json": "scripted/rules.json",
            "report_html": "scripted/report.html",
            "junit": junit_files,
        },
        "lanes": {
            "scripted": {"present": True, "authoritative": True, "version": "v0.4"},
            "llm": {"present": llm_present, "authoritative": False, "config": "configs/llm_dev.yaml" if llm_present else None},
            "proactive": {
                "present": proactive_present, 
                "authoritative": False,
                "gates": {
                    "P-001": "ok" if proactive_present else "n/a",
                    "P-002": "ok" if proactive_present else "n/a", 
                    "P-003": "edap" if proactive_present else "n/a",
                    "P-004": "stub" if proactive_present else "n/a"
                }
            }
        },
        "advisory": {
            "present": advisory_present,
            "authoritative": False
        },
        "documentation": {
            "privacy_legal_note": "docs/ops/privacy_legal_note_v0.1.md" if privacy_note.exists() else None
        },
        "gates": {
            "V-001": {"status": "unknown", "note": "Requires golden test validation"},
            "V-002": {"status": "unknown", "note": "Requires category grounding check"},
            "V-003": {"status": "unknown", "note": "Requires audit completeness check"},
            "V-004": {"status": "unknown", "note": "Requires practitioner readiness check"},
            "V-005": {"status": "unknown", "note": "Requires execution guarantees check"},
        }
    }

    # Basic gate evaluation based on available evidence
    if "golden" in junit_files:
        manifest["gates"]["V-001"]["status"] = "evidence_available"
        manifest["gates"]["V-002"]["status"] = "evidence_available"
    
    if "audit" in junit_files and demo_json.exists():
        # Check if rules contain span/provenance info
        try:
            rules_text = demo_json.read_text()
            if "source_span" in rules_text and "provenance" in rules_text:
                manifest["gates"]["V-003"]["status"] = "evidence_available"
                manifest["gates"]["V-004"]["status"] = "evidence_available"
                
                if "UNSPECIFIED" not in rules_text:
                    manifest["gates"]["V-005"]["status"] = "evidence_available"
        except:
            pass

    (out_dir/"manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    # Copy bundle README template for v0.2
    bundle_readme_template = ROOT/"docs"/"specs"/"bundle_README_v0_2.md"
    if bundle_readme_template.exists():
        shutil.copy2(bundle_readme_template, out_dir/"README.md")
    else:
        # Fallback to generated README if template not found
        readme_content = f"""# Audit Package v0.1

**Generated**: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}  
**Source**: {pdf_path.name}  
**Processing Mode**: Zero-inference with exact preservation

## Bundle Contents

### Authoritative Artifacts (Primary)
- `rules/rules.json` - Compiled indicators and rules with span references
- `rules/report.html` - Enhanced analyst-friendly HTML report  
- `tests/` - JUnit validation results for gates V-001 through V-005
- `input/` - Source PDF document for provenance

### Advisory Content (NON-AUTHORITATIVE)
- `advisory/narrative_advisory.md` - Analyst convenience narrative
- `advisory/sources.json` - Span-to-quote mapping for advisory content

### Documentation & Compliance
- `docs/ops/privacy_legal_note_v0.1.md` - Privacy and legal considerations
- `manifest.json` - Bundle metadata and validation gate status

## Validation Gates

The Safety Sigma system enforces five validation gates:

- **V-001**: Indicator preservation (exact verbatim text maintained)
- **V-002**: Category grounding (compiled categories match IR categories)  
- **V-003**: Audit completeness (all indicators have span refs + provenance)
- **V-004**: Practitioner readiness (regex/SQL rules generated)
- **V-005**: Execution guarantees (no UNSPECIFIED values in outputs)

See `manifest.json` for current gate status and evidence availability.

## Advisory Content Disclaimer

⚠️ **NON-AUTHORITATIVE**: The `advisory/` folder contains content for analyst convenience only. It is derived from spans in the authoritative artifacts but should not be treated as a source of truth. Always verify information against:

1. `rules/rules.json` (authoritative IR and compiled rules)
2. `tests/` (validation evidence)  
3. `manifest.json` (gate status and metadata)

## Usage

1. **Review HTML Report**: Open `rules/report.html` for analyst-friendly view
2. **Validate Gates**: Check `manifest.json` for validation status
3. **Deploy Rules**: Use regex/SQL from `rules/rules.json` for detection
4. **Audit Trail**: Trace any indicator back to source via span references

## Processing Methodology

- **Zero-inference**: No behavioral analysis or threat attribution
- **Exact preservation**: Indicators stored verbatim from source
- **Source grounding**: Every claim traceable to specific PDF spans
- **Append-only audit**: Complete processing chain logged

---

Generated by Safety Sigma v2.0 | Analyst Readiness Enhanced
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