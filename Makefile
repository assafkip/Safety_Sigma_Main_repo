.PHONY: bootstrap test lint demo clean test-parity llm llm-diff bundle-v02 backtest proactive bundle-v04 report-v05 bundle-v05 agentic agentic-test adapters share-export share-import report-v08 memory-index report-v09 report-v09b help

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
	@echo "  report-v05   - Generate HTML report v0.5 with backtesting metrics"
	@echo "  bundle-v05   - Build Audit Package v0.5 with backtesting & behavioral context"
	@echo "  agentic      - Run agentic orchestrator (advisory)"
	@echo "  agentic-test - Test agentic workflow components"
	@echo "  adapters     - Compile deployment adapters (V-006)"
	@echo "  share-export - Export bundle with checksums (V-007)"
	@echo "  share-import - Import and validate bundle (V-007)"
	@echo "  report-v08   - Generate HTML report v0.8 with agentic plan"
	@echo "  memory-index - Build/update cumulative reuse index (v0.9)"
	@echo "  report-v09   - Generate HTML report v0.9 with Living Knowledge Base"
	@echo "  report-v09b  - Generate HTML report v0.9b with Behavioral Slice features"
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
	PYTHONPATH=. python3 scripts/run_backtest.py --rules artifacts/demo_rules.json --clean samples/clean.csv --labeled samples/labeled.csv --out artifacts/proactive/backtest_report.json || true

proactive:
	@echo "Running proactive narrative expansion..."
	@source .venv/bin/activate && python scripts/run_proactive_sim.py \
		--out artifacts/proactive/expansions.json || echo "Proactive analysis complete"

bundle-v04:
	@echo "Building Audit Package v0.4 with proactive lane..."
	@source .venv/bin/activate && python scripts/build_audit_package.py \
		--pdf Reports/atlas-highlights-scams-and-fraud.pdf \
		--outdir artifacts/audit_package_v0_4

report-v05:
	PYTHONPATH=. python3 scripts/render_report_v05.py

bundle-v05:
	python3 scripts/build_audit_package.py --pdf Reports/atlas-highlights-scams-and-fraud.pdf --outdir artifacts/audit_package_v0_5

agentic:
	PYTHONPATH=. python3 scripts/run_agentic.py

agentic-test:
	PYTHONPATH=. pytest -q tests/agentic/test_agentic_v08.py

adapters:
	python3 adapters/splunk/compile.py || true
	python3 adapters/elastic/compile.py || true
	python3 adapters/sql/compile.py || true

share-export:
	python3 scripts/share_export.py || true

share-import:
	python3 scripts/share_import.py artifacts/audit_package_v0_7_*.zip || ls -1 artifacts/audit_package_v0_*.zip | tail -1 | xargs python3 scripts/share_import.py || true

report-v08:
	PYTHONPATH=. python3 scripts/render_report_v08.py || true

memory-index:
	PYTHONPATH=. python3 scripts/build_reuse_index.py || true

report-v09:
	PYTHONPATH=. python3 scripts/render_report_v09.py || true

report-v09b:
	PYTHONPATH=. python3 scripts/render_report_v09b.py || true

clean:
	@echo "Cleaning build artifacts..."
	@rm -rf build/ dist/ *.egg-info/
	@find . -type d -name __pycache__ -exec rm -rf {} +
	@find . -type f -name "*.pyc" -delete
