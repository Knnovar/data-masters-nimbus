import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env", override=False)
except ImportError:
    if (BASE_DIR / ".env").exists():
        print("[CONFIG] python-dotenv nao instalado: .env ignorado. "
              "Instale com: pip install python-dotenv")
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
# Credencial sem default: com USE_MINIO=true e variavel vazia, get_storage() falha
# com mensagem explicita em vez de tentar uma credencial embutida no codigo.
MINIO_ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY", "")
MINIO_SECRET_KEY = os.environ.get("MINIO_SECRET_KEY", "")
MINIO_SECURE = os.environ.get("MINIO_SECURE", "false").lower() in ("true", "1", "yes")
MINIO_REGION = os.environ.get("MINIO_REGION") or None
BUCKET_PREFIX = os.environ.get("BUCKET_PREFIX", "nimbus")
MINIO_CREATE_BUCKETS = os.environ.get("MINIO_CREATE_BUCKETS", "true").lower() in ("true", "1", "yes")

OLLAMA_HOST  = os.environ.get("OLLAMA_HOST",  "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "phi4")
SKIP_SLM     = os.environ.get("SKIP_SLM", "false").lower() in ("true", "1", "yes")
SLM_NUM_PREDICT = int(os.environ.get("SLM_NUM_PREDICT", "1500"))

# Data de referencia da carga (YYYY-MM-DD). Vazia = derivada do run_id. E a
# identidade da janela de dados: reprocessar a mesma dat_ref sobrescreve a
# particao em vez de acumular duplicata (ver src/ingestion/idempotency.py).
DAT_REF = os.environ.get("DAT_REF") or None

STRICT_TYPING = os.environ.get("STRICT_TYPING", "true").lower() in ("true", "1", "yes")
QUALITY_GATE = os.environ.get("QUALITY_GATE", "true").lower() in ("true", "1", "yes")

#Gate de governanca: Exige Manifesto promovido pelo Data Steward (manifest_status
#VALIDATED) para publicar a Silver. Desligado por padrao - com ele ligado, contrato
# em DRAFT bloqueia a publicacao e o exit code, com o gate de rejeicao.
REQUIRE_VALIDATED_MANIFEST = os.environ.get(
    "REQUIRE_VALIDATED_MANIFEST", "false").lower() in ("true", '1', "yes")

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
# Quarentena contem o dado bruto que falhou o contrato, inclusive PII em claro.
# Publicar isso e decisao de governanca, nao default: desligado, e a ligacao
# exige DATABRICKS_QUARANTINE_UPLOAD=true explicito.
DATABRICKS_QUARANTINE_UPLOAD = os.environ.get("DATABRICKS_QUARANTINE_UPLOAD", "False").lower() in ("true", "1", "yes")

# Mascara as colunas marcadas LGPD_SENSITIVE no Manifest antes de gravar o
# arquivo de rejeitos. O token e deterministico, entao a mesma pessoa continua
# correlacionavel entre linhas sem que o valor original seja legivel.
QUARANTINE_MASK_PII = os.environ.get("QUARANTINE_MASK_PII", "true").lower() in ("true", "1", "yes")

# Carga reprovada pelo gate sai da Silver e vai para a quarentena, para que
# nenhum consumidor leia dado bloqueado. Desligar mantem o comportamento antigo.
QUARANTINE_BLOCKED_SILVER = os.environ.get("QUARANTINE_BLOCKED_SILVER", "true").lower() in ("true", "1", "yes")