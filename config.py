import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env", override=False)
except ImportError:
    pass
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
SLM_NUM_PREDICT = int(os.environ.get("SLM_NUM_PREDICT", "1500"))

NULL_TOLERANCE_PCT  = float(os.environ.get("NULL_TOLERANCE_PCT",  "30.0"))
DUPLICATE_TOLERANCE = float(os.environ.get("DUPLICATE_TOLERANCE", "0.02"))

DATABRICKS_HOST         = os.environ.get("DATABRICKS_HOST",         "")
DATABRICKS_TOKEN        = os.environ.get("DATABRICKS_TOKEN",    "")
DATABRICKS_WAREHOUSE_ID = os.environ.get("DATABRICKS_WAREHOUSE_ID", "")
DATABRICKS_VOLUME       = os.environ.get("DATABRICKS_VOLUME",    "landing")
DATABRICKS_CATALOG      = os.environ.get("DATABRICKS_CATALOG",      "nimbus")
DATABRICKS_SCHEMA       = os.environ.get("DATABRICKS_SCHEMA",       "silver")
DATABRICKS_SILVER_SCHEMA = os.environ.get("DATABRICKS_SILVER_SCHEMA",   DATABRICKS_SCHEMA)
DATABRICKS_BRONZE_SCHEMA = os.environ.get("DATABRICKS_BRONZE_SCHEMA",   "bronze")
DATABRICKS_AUTO_UPLOAD  = os.environ.get("DATABRICKS_AUTO_UPLOAD",  "True").lower() in ("true", "1", "yes")
DATABRICKS_BRONZE_VOLUME = os.environ.get("DATABRICKS_BRONZE_VOLUME", "landing")
DATABRICKS_BRONZE_UPLOAD = os.environ.get("DATABRICKS_BRONZE_UPLOAD", "True").lower() in ("true", "1", "yes")
