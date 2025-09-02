.PHONY: bootstrap test lint demo clean test-parity help test-v02 bundle audit-bundle

# Default target
help:
	@echo "Safety Sigma 2.0 - Available targets:"
	@echo "  bootstrap     - Initialize repository and dependencies"
	@echo "  test         - Run all tests including parity checks"
	@echo "  test-v02     - Run v0.2 validation tests (golden, unit, audit)"
	@echo "  test-parity  - Run parity tests against Safety Sigma 1.0"
	@echo "  lint         - Run code formatting and linting"
	@echo "  demo         - Run v0.2 PDF processing demo (atlas->html/json)"
	@echo "  bundle       - Create artifacts bundle with demo outputs"
	@echo "  audit-bundle - Build Audit Package v0.1 (source PDF + rules + tests + manifest)"
	@echo "  clean        - Clean build artifacts and caches"

bootstrap:
	@./scripts/bootstrap_repo.sh

test:
	@echo "Running all tests..."
	@source .venv/bin/activate && python -m pytest tests/ -v

test-parity:
	@echo "Running parity tests..."
	@source .venv/bin/activate && python -m pytest tests/test_parity_baseline.py -v

test-stage1:
	@echo "Running Stage 1 tests with tools enabled..."
	@source .venv/bin/activate && SS2_ENABLE_TOOLS=true python -m pytest tests/ -v -k "stage1"

test-stage2:
	@echo "Running Stage 2 tests with agent enabled..."
	@source .venv/bin/activate && SS2_USE_AGENT=true python -m pytest tests/ -v -k "stage2"

lint:
	@echo "Running code formatting and linting..."
	@source .venv/bin/activate && black safety_sigma/ tests/ --check
	@source .venv/bin/activate && isort safety_sigma/ tests/ --check-only
	@source .venv/bin/activate && flake8 safety_sigma/ tests/

format:
	@echo "Formatting code..."
	@source .venv/bin/activate && black safety_sigma/ tests/
	@source .venv/bin/activate && isort safety_sigma/ tests/

demo:
	@echo "🎬 Running Safety Sigma v0.2 PDF Demo..."
	./demo/run_demo.sh

test-v02:
	@echo "🧪 Running v0.2 validation tests..."
	@echo "Testing V-001,V-002 (Golden Cases):"
	@PYTHONPATH=. pytest -q tests/golden_cases
	@echo "Testing rule compiler (Unit Tests):"
	@PYTHONPATH=. pytest -q tests/unit  
	@echo "Testing V-003..V-005 (Audit Tests):"
	@PYTHONPATH=. pytest -q tests/audit
	@echo "✅ All v0.2 validation gates passed"

bundle:
	@echo "📦 Creating artifacts bundle..."
	@mkdir -p artifacts
	@echo "Running demo to ensure fresh artifacts..."
	@$(MAKE) demo
	@echo "Creating audit bundle..."
	@zip -r artifacts/audit_bundle.zip \
		Reports/*.pdf \
		artifacts/*.json \
		artifacts/*.html \
		demo/sample_outputs/* \
		|| true
	@echo "Bundle created: artifacts/audit_bundle.zip"
	@ls -lh artifacts/audit_bundle.zip || true

audit-bundle:
	@echo "📋 Building Audit Package v0.1..."
	@python3 scripts/build_audit_package.py --pdf Reports/atlas-highlights-scams-and-fraud.pdf --outdir artifacts/audit_package_v0_1
	@echo "Bundle at artifacts/audit_package_v0_1.zip"

clean:
	@echo "Cleaning build artifacts..."
	@rm -rf build/ dist/ *.egg-info/
	@find . -type d -name __pycache__ -exec rm -rf {} +
	@find . -type f -name "*.pyc" -delete
