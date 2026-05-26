from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR  = BASE_DIR / "data"

LANDING_DIR    = DATA_DIR / "landing"
QUARANTINE_DIR = DATA_DIR / "quarantine"
PROCESSED_DIR  = DATA_DIR / "processed"
CONTRACTS_DIR  = DATA_DIR / "contracts"
METRICS_DIR    = DATA_DIR / "metrics"
REPORTS_DIR    = DATA_DIR / "reports"

for d in [LANDING_DIR, QUARANTINE_DIR, PROCESSED_DIR, CONTRACTS_DIR, METRICS_DIR, REPORTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ── Ollama ───────────────────────────────────────────────────────────────────
# Troque por "phi4" ou "llama3.1:8b" para documentação semântica mais rica.
# Qwen2.5-Coder funciona, mas é otimizado para código — não para linguagem de negócio.
OLLAMA_HOST  = "http://localhost:11434"
OLLAMA_MODEL = "qwen2.5-coder:7b"

# ── MinIO (opcional — usado quando docker-compose estiver no ar) ──────────────
MINIO_ENDPOINT   = "localhost:9000"
MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "minioadmin"
MINIO_BUCKET     = "data-masters-landing"

# ── Pipeline ─────────────────────────────────────────────────────────────────
NULL_TOLERANCE_PCT   = 30.0   # acima disso → anomalia relatada pelo SLM
DUPLICATE_TOLERANCE  = 0.02   # 2 % de duplicatas aceitas antes de warning
