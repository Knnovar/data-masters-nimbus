# Makefile - Data Masters PoC
# Uso: make <target>
# Windows: instale make via choco install make ou use o Git Bash

.PHONY: run baseline non-breaking breaking metrics issues slm clean clean-data setup prefect-setup help

# ── Pipeline ──────────────────────────────────────────────────────────────────

run:
	python run_pipeline.py

baseline:
	python run_pipeline.py --scenario baseline

non-breaking:
	python run_pipeline.py --scenario non_breaking

breaking:
	python run_pipeline.py --scenario breaking

# ── Dashboard ─────────────────────────────────────────────────────────────────

metrics:
	python show_metrics.py

metrics-all:
	python show_metrics.py --all

issues:
	python show_metrics.py --issues

slm:
	python show_metrics.py --slm

export:
	python show_metrics.py --csv data/metrics_export.csv

# ── Manifesto ─────────────────────────────────────────────────────────────────

check-manifest:
	@echo "Uso: make check-manifest FILE=data/contracts/tb_clientes.yaml"
	python -m src.manifest.manifest_validator --file $(FILE) --check-only

validate-manifest:
	@echo "Uso: make validate-manifest FILE=data/contracts/tb_clientes.yaml STEWARD='Nome'"
	python -m src.manifest.manifest_validator --file $(FILE) --steward "$(STEWARD)"

# ── Prefect ───────────────────────────────────────────────────────────────────

prefect-setup:
	python setup_prefect.py

prefect-run:
	prefect deployment run 'data-masters-pipeline/baseline-manual'

# ── Setup e limpeza ───────────────────────────────────────────────────────────

setup:
	pip install -r requirements.txt

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true

clean-data:
	@echo "Removendo dados gerados (landing, processed, quarantine, gold)..."
	rm -f data/landing/*.csv data/processed/*.csv data/quarantine/*.csv
	rm -f data/contracts/*.yaml data/metrics/*.json data/reports/*.md

help:
	@echo ""
	@echo "Targets disponiveis:"
	@echo ""
	@echo "  Pipeline:"
	@echo "    make run           Executa todos os cenarios"
	@echo "    make baseline      Executa cenario baseline"
	@echo "    make non-breaking  Executa cenario non_breaking"
	@echo "    make breaking      Executa cenario breaking"
	@echo ""
	@echo "  Dashboard:"
	@echo "    make metrics       Resumo geral do ultimo run"
	@echo "    make metrics-all   Historico completo de runs"
	@echo "    make issues        Apenas registros com problemas"
	@echo "    make slm           Status do enriquecimento SLM"
	@echo "    make export        Exporta metricas para CSV"
	@echo ""
	@echo "  Manifesto:"
	@echo "    make check-manifest FILE=data/contracts/tb_clientes.yaml"
	@echo "    make validate-manifest FILE=... STEWARD='Nome'"
	@echo ""
	@echo "  Prefect:"
	@echo "    make prefect-setup  Cria work pool e registra deployments"
	@echo "    make prefect-run    Dispara run baseline via Prefect"
	@echo ""
	@echo "  Manutencao:"
	@echo "    make setup          Instala dependencias Python"
	@echo "    make clean          Remove __pycache__ e .pyc"
	@echo "    make clean-data     Remove dados gerados (cuidado!)"
