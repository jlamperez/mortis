# ---------- Config ----------
SHELL := /bin/bash
PY := uv run python
UV := uv
APP := mortis
MODULE := mortis.app
DEMO := examples/demo.py

# Variables de entorno esperadas
ENV_FILE := .env
REQUIRED_ENV := MULTIVERSE_COMPACTIFAI_API_KEY

# ---------- Targets ----------
.PHONY: help install sync lock upgrade run run-m calibrate demo fmt lint test check-env add-% export clean

help:
	@echo "Comandos:"
	@echo "  make install     - Instala deps (crea .venv si no existe)"
	@echo "  make sync        - Igual que install (alias)"
	@echo "  make lock        - Genera/actualiza uv.lock"
	@echo "  make upgrade     - Sube versiones y regenera lock"
	@echo "  make run         - Ejecuta CLI '$(APP)'"
	@echo "  make run-m       - Ejecuta 'python -m $(MODULE)'"
	@echo "  make calibrate   - Ejecuta el script de calibración del robot"
	@echo "  make demo        - Ejecuta $(DEMO)"
	@echo "  make check-env   - Verifica $(ENV_FILE) y variables requeridas"
	@echo "  make add-<pkg>   - Añade dependencia con uv (ej: make add-python-dotenv)"
	@echo "  make export      - Exporta requirements.txt desde uv.lock"
	@echo "  make clean       - Limpia artefactos"

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

demo: check-env
	@test -f $(DEMO) || { echo "No existe $(DEMO). Crea un demo o cambia la ruta."; exit 1; }
	$(UV) run python $(DEMO)

check-env:
	@test -f $(ENV_FILE) || { echo "Falta $(ENV_FILE) en la raíz."; exit 1; }
	@set -o allexport; source $(ENV_FILE); set +o allexport; \
	for v in $(REQUIRED_ENV); do \
		if [ -z "$${!v}" ]; then echo "Falta variable $$v en $(ENV_FILE) o en el entorno"; exit 1; fi; \
	done
	@echo "✅ MULTIVERSE_COMPACTIFAI_API_KEY in $(ENV_FILE) OK"

add-%:
	$(UV) add $*

export:
	$(UV) export > requirements.txt
	@echo "requirements.txt generated from uv.lock"

clean:
	rm -rf dist build *.egg-info
