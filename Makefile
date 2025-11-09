# ---------- Config ----------
SHELL := /bin/bash
PY := uv run python
UV := uv
APP := mortis
MODULE := mortis.app
DEMO := examples/demo.py

# Environment variables
ENV_FILE := .env
REQUIRED_ENV := MULTIVERSE_COMPACTIFAI_API_KEY

# ---------- Targets ----------
.PHONY: help install sync lock upgrade run run-m calibrate test-gesture demo fmt lint test check-env add-% export clean

help:
	@echo "Available commands:"
	@echo "  make install     - Install dependencies (creates .venv if it doesn't exist)"
	@echo "  make sync        - Same as install (alias)"
	@echo "  make lock        - Generate/update uv.lock"
	@echo "  make upgrade     - Upgrade versions and regenerate lock"
	@echo "  make run         - Run CLI '$(APP)'"
	@echo "  make run-m       - Run 'python -m $(MODULE)'"
	@echo "  make calibrate   - Run the robot calibration script"
	@echo "  make test-gesture- Run a test gesture with the robotic arm"
	@echo "  make demo        - Run $(DEMO)"
	@echo "  make check-env   - Check $(ENV_FILE) and required variables"
	@echo "  make add-<pkg>   - Add dependency with uv (e.g., make add-python-dotenv)"
	@echo "  make export      - Export requirements.txt from uv.lock"
	@echo "  make clean       - Clean artifacts"

install: sync
sync:
	$(UV) sync

lock:
	$(UV) lock

upgrade:
	$(UV) lock --upgrade
	$(UV) sync

run: check-env
	$(UV) run $(APP)

run-m: check-env
	$(UV) run python -m $(MODULE)

calibrate:
	$(UV) run calibrate

test-gesture:
	$(UV) run python -m mortis.robot

demo: check-env
	@test -f $(DEMO) || { echo "$(DEMO) does not exist. Create a demo or change the path."; exit 1; }
	$(UV) run python $(DEMO)

check-env:
	@test -f $(ENV_FILE) || { echo "$(ENV_FILE) is missing in the root directory."; exit 1; }
	@set -o allexport; source $(ENV_FILE); set +o allexport; \
	for v in $(REQUIRED_ENV); do \
		if [ -z "$${!v}" ]; then echo "Missing variable $$v in $(ENV_FILE) or environment"; exit 1; fi; \
	done
	@echo "✅ MULTIVERSE_COMPACTIFAI_API_KEY in $(ENV_FILE) OK"

add-%:
	$(UV) add $*

export:
	$(UV) export > requirements.txt
	@echo "requirements.txt generated from uv.lock"

clean:
	rm -rf dist build *.egg-info
