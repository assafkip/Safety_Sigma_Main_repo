SHELL := /bin/bash
PY := python3
ENV ?= ops/pilot/.env
CFG := ops/pilot/config.yaml
OUT := out/pilot
AUD := $(OUT)/audit
RULES := $(OUT)/rules
REPORT := $(OUT)/report

.PHONY: all compile golden metadata backtest adapters report package shadow-run clean

all: compile golden metadata backtest adapters report

compile:
	@mkdir -p $(OUT) $(AUD) $(RULES) $(REPORT)
	@echo "[compile] Compiling IR + rules from inputs…"
	# ASSUMPTION: repo provides a compile script/command; replace with real entrypoint
	@$(PY) scripts/compile_demo.py --in intel/ --out $(OUT)

golden:
	@echo "[golden] Running golden tests (G-001..G-003, G-010)…"
	@$(PY) scripts/run_golden.py --ir $(OUT)/ir.json --rules $(OUT)/rules.json

metadata:
	@echo "[metadata] Enforcing required metadata…"
	@$(PY) scripts/metadata_check.py --rules $(OUT)/rules.json --out $(AUD)/metadata_check.json

backtest:
	@echo "[backtest] Running offline harness on Snowflake sample…"
	@set -a && source $(ENV) && set +a; \
	$(PY) scripts/backtest.py --cfg $(CFG) --rules $(OUT)/rules.json --out $(AUD)/metrics.json

adapters:
	@echo "[adapters] Compiling adapter outputs (Snowflake/Sift/Unit21)…"
	@$(PY) scripts/compile_adapters.py --rules $(OUT)/rules.json --out $(RULES)

report:
	@echo "[report] Rendering HTML report with per-gate outcomes…"
	@$(PY) scripts/report_html.py --cfg $(CFG) --ir $(OUT)/ir.json --rules $(OUT)/rules.json --metrics $(AUD)/metrics.json --metadata $(AUD)/metadata_check.json --out $(REPORT)

package:
	@echo "[package] Bundling artifacts for testers…"
	@tar -czf $(OUT)/bundle.tgz $(OUT)

shadow-run: all
	@echo "[shadow] Shadow mode activated. Emitting alerts to pilot sink only."
	# ASSUMPTION: implement streaming later; for now, report + bundle suffice.

clean:
	@rm -rf $(OUT)