import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR  = BASE_DIR / "data"

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

USE_MINIO = os.environ.get("USE_MINIO", "false").lower() in ("true", "1", "yes")

MINIO_ENDPOINT   = os.environ.get("MINIO_ENDPOINT",   "localhost:9000")
MINIO_ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.environ.get("MINIO_SECRET_KEY", "minioadmin")

OLLAMA_HOST  = os.environ.get("OLLAMA_HOST",  "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "phi4")
SKIP_SLM     = os.environ.get("SKIP_SLM", "false").lower() in ("true", "1", "yes")

NULL_TOLERANCE_PCT  = float(os.environ.get("NULL_TOLERANCE_PCT",  "30.0"))
DUPLICATE_TOLERANCE = float(os.environ.get("DUPLICATE_TOLERANCE", "0.02"))

DATABRICKS_HOST         = os.environ.get("DATABRICKS_HOST",         "https://dbc-63c6e362-54f2.cloud.databricks.com")
DATABRICKS_TOKEN        = os.environ.get("DATABRICKS_TOKEN",        "")
DATABRICKS_WAREHOUSE_ID = os.environ.get("DATABRICKS_WAREHOUSE_ID", "d1d694270bee33ae")
DATABRICKS_VOLUME    = os.environ.get("DATABRICKS_VOLUME",    "landing")
DATABRICKS_CATALOG      = os.environ.get("DATABRICKS_CATALOG",      "workspace")
DATABRICKS_SCHEMA       = os.environ.get("DATABRICKS_SCHEMA",       "nimbus")
DATABRICKS_AUTO_UPLOAD  = os.environ.get("DATABRICKS_AUTO_UPLOAD",  "true").lower() in ("true", "1", "yes")
