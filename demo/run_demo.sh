#!/usr/bin/env bash
set -euo pipefail

echo "🎬 Safety Sigma v0.2 Demo - Zero-Inference Processing"
echo "======================================================"

# Set up virtual environment
echo "📦 Setting up environment..."
python3 -m venv .venv && source .venv/bin/activate
python -m pip install -U pip PyPDF2 >/dev/null 2>&1

# Check if PDF exists
PDF_PATH="Reports/atlas-highlights-scams-and-fraud.pdf"
if [ ! -f "$PDF_PATH" ]; then
    echo "❌ Error: PDF not found at $PDF_PATH"
    echo "Please ensure the Atlas PDF is present in the Reports directory"
    exit 1
fi

# Create artifacts directory
mkdir -p artifacts demo/sample_outputs

# Run the demo
echo "🔄 Processing PDF with zero-inference methodology..."
./scripts/demo_pdf_to_rules.py \
    --pdf "$PDF_PATH" \
    --json-out artifacts/demo_rules.json \
    --html-out artifacts/demo_report.html

# Copy to sample outputs
echo "📋 Copying artifacts to sample outputs..."
cp artifacts/demo_report.html demo/sample_outputs/ || true
cp artifacts/demo_rules.json  demo/sample_outputs/ || true

# Show results
echo ""
echo "✅ Demo completed successfully!"
echo ""
echo "Generated artifacts:"
ls -lh artifacts/demo_*.{json,html} 2>/dev/null || true
echo ""
echo "Sample outputs:"
ls -lh demo/sample_outputs/ 2>/dev/null || true
echo ""
echo "📊 Open artifacts/demo_report.html in your browser to view the interactive report"
echo "📄 JSON rules available in artifacts/demo_rules.json"
echo ""
echo "Demo artifacts available in:"
echo "  - artifacts/ (primary outputs)"  
echo "  - demo/sample_outputs/ (for distribution)"