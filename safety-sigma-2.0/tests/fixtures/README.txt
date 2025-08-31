Test Fixtures for Safety Sigma 2.0

This directory contains test data for parity testing:
- baseline_outputs.json: Reference outputs from Safety Sigma 1.0
- test_instructions.md: Sample instruction files
- Sample PDFs: Test documents (add as needed)

Usage:
1. Generate baseline: python -m tests.test_parity_baseline --generate-baseline
2. Run parity tests: python -m pytest tests/test_parity_baseline.py