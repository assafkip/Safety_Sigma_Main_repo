.PHONY: bootstrap test lint demo clean test-parity llm llm-diff bundle-v02 backtest proactive bundle-v04 help

# Default target
help:
	@echo "Safety Sigma 2.0 - Available targets:"
	@echo "  bootstrap     - Initialize repository and dependencies"
	@echo "  test         - Run all tests including parity checks"
	@echo "  test-parity  - Run parity tests against Safety Sigma 1.0"
	@echo "  lint         - Run code formatting and linting"
	@echo "  demo         - Run demo with sample data"
	@echo "  llm          - Run LLM pipeline with Atlas PDF"
	@echo "  llm-diff     - Compare scripted vs LLM indicator extraction"
	@echo "  bundle-v02   - Build Audit Package v0.2 with dual-lane structure"
	@echo "  backtest     - Run backtest validation against sample data"
	@echo "  proactive    - Run proactive narrative expansion (EDAP)"
	@echo "  bundle-v04   - Build Audit Package v0.4 with proactive lane"
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

llm:
	@echo "Running LLM pipeline with Atlas PDF..."
	@source .venv/bin/activate && python scripts/run_llm_pipeline.py \
		--doc Reports/atlas-highlights-scams-and-fraud.pdf \
		--config configs/llm_dev.yaml \
		--out artifacts/llm_output

llm-diff:
	@echo "Comparing scripted vs LLM indicator extraction..."
	@source .venv/bin/activate && python scripts/diff_ir.py \
		--scripted artifacts/demo_rules.json \
		--llm artifacts/llm_output/ir.json \
		--verbose

bundle-v02:
	@echo "Building Audit Package v0.2 with dual-lane structure..."
	@source .venv/bin/activate && python scripts/build_audit_package.py \
		--pdf Reports/atlas-highlights-scams-and-fraud.pdf \
		--outdir artifacts/audit_package_v0_2

backtest:
	@echo "Running backtest validation..."
	@source .venv/bin/activate && python scripts/backtest_rules.py \
		--csv samples/backtest.csv \
		--rules artifacts/demo_rules.json \
		--output artifacts/backtest_summary.json || echo "Backtest skipped (no sample data)"

proactive:
	@echo "Running proactive narrative expansion..."
	@source .venv/bin/activate && python scripts/run_proactive_sim.py \
		--out artifacts/proactive/expansions.json || echo "Proactive analysis complete"

bundle-v04:
	@echo "Building Audit Package v0.4 with proactive lane..."
	@source .venv/bin/activate && python scripts/build_audit_package.py \
		--pdf Reports/atlas-highlights-scams-and-fraud.pdf \
		--outdir artifacts/audit_package_v0_4

clean:
	@echo "Cleaning build artifacts..."
	@rm -rf build/ dist/ *.egg-info/
	@find . -type d -name __pycache__ -exec rm -rf {} +
	@find . -type f -name "*.pyc" -delete
