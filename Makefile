.PHONY: bootstrap test lint demo clean test-parity help advisory audit-bundle

# Default target
help:
	@echo "Safety Sigma 2.0 - Available targets:"
	@echo "  bootstrap     - Initialize repository and dependencies"
	@echo "  test         - Run all tests including parity checks"
	@echo "  test-parity  - Run parity tests against Safety Sigma 1.0"
	@echo "  lint         - Run code formatting and linting"
	@echo "  demo         - Run demo with sample data"
	@echo "  advisory     - Generate NON-AUTHORITATIVE narrative from rules"
	@echo "  audit-bundle - Build Audit Package v0.1 (PDF + rules + advisory + manifest)"
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
	@echo "Running demo..."
	@source .venv/bin/activate && python -m safety_sigma.demo

advisory:
	@echo "📝 Generating Advisory Narrative (NON-AUTHORITATIVE)..."
	@python3 scripts/generate_advisory.py --rules artifacts/demo_rules.json --outdir advisory

audit-bundle:
	@echo "📋 Building Audit Package v0.1..."
	@python3 scripts/build_audit_package.py --pdf Reports/atlas-highlights-scams-and-fraud.pdf --outdir artifacts/audit_package_v0_1
	@echo "Bundle at artifacts/audit_package_v0_1.zip"

clean:
	@echo "Cleaning build artifacts..."
	@rm -rf build/ dist/ *.egg-info/
	@find . -type d -name __pycache__ -exec rm -rf {} +
	@find . -type f -name "*.pyc" -delete
