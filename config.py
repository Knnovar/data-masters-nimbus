"""
config.py — Configuracao central do Projeto Nimbus.

Prioridade de valores (maior para menor):
  1. Variavel de ambiente (definida no .env ou no docker-compose.yml)
  2. Valor default hardcoded abaixo

Em ambiente Docker, todas as configuracoes vem via variavel de ambiente.
Em ambiente local, os defaults abaixo entram em acao.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR  = BASE_DIR / "data"

# ── Camadas medallion ─────────────────────────────────────────────────────────
LANDING_DIR    = DATA_DIR / "landing"
PROCESSED_DIR  = DATA_DIR / "processed"
GOLD_DIR       = DATA_DIR / "gold"
QUARANTINE_DIR = DATA_DIR / "quarantine"
CONTRACTS_DIR  = DATA_DIR / "contracts"
METRICS_DIR    = DATA_DIR / "metrics"
REPORTS_DIR    = DATA_DIR / "reports"

for d in [LANDING_DIR, PROCESSED_DIR, GOLD_DIR, QUARANTINE_DIR,
          CONTRACTS_DIR, METRICS_DIR, REPORTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ── Storage backend ───────────────────────────────────────────────────────────
USE_MINIO = os.environ.get("USE_MINIO", "false").lower() in ("true", "1", "yes")

# ── MinIO ─────────────────────────────────────────────────────────────────────
MINIO_ENDPOINT   = os.environ.get("MINIO_ENDPOINT",   "localhost:9000")
MINIO_ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.environ.get("MINIO_SECRET_KEY", "minioadmin")

# ── Ollama / SLM ──────────────────────────────────────────────────────────────
OLLAMA_HOST  = os.environ.get("OLLAMA_HOST",  "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "phi4")
SKIP_SLM     = os.environ.get("SKIP_SLM",    "false").lower() in ("true", "1", "yes")

# ── Qualidade ─────────────────────────────────────────────────────────────────
NULL_TOLERANCE_PCT  = float(os.environ.get("NULL_TOLERANCE_PCT",  "30.0"))
DUPLICATE_TOLERANCE = float(os.environ.get("DUPLICATE_TOLERANCE", "0.02"))

# ── Databricks ────────────────────────────────────────────────────────────────
DATABRICKS_HOST        = os.environ.get("DATABRICKS_HOST",        "")
DATABRICKS_TOKEN       = os.environ.get("DATABRICKS_TOKEN",       "")
DATABRICKS_DBFS_BASE   = os.environ.get("DATABRICKS_DBFS_BASE",   "/nimbus/silver")
DATABRICKS_CATALOG     = os.environ.get("DATABRICKS_CATALOG",     "hive_metastore")
DATABRICKS_SCHEMA      = os.environ.get("DATABRICKS_SCHEMA",      "nimbus")
DATABRICKS_AUTO_UPLOAD = os.environ.get("DATABRICKS_AUTO_UPLOAD", "false").lower() in ("true", "1", "yes")
