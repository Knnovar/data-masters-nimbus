from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR  = BASE_DIR / "data"

# ── Camadas da arquitetura medallion ─────────────────────────────────────────
LANDING_DIR    = DATA_DIR / "landing"      # bronze  — dado bruto
PROCESSED_DIR  = DATA_DIR / "processed"   # silver  — dado validado
GOLD_DIR       = DATA_DIR / "gold"        # gold    — dado agregado
QUARANTINE_DIR = DATA_DIR / "quarantine"  # DLQ     — breaking changes
CONTRACTS_DIR  = DATA_DIR / "contracts"
METRICS_DIR    = DATA_DIR / "metrics"
REPORTS_DIR    = DATA_DIR / "reports"

for d in [LANDING_DIR, PROCESSED_DIR, GOLD_DIR, QUARANTINE_DIR,
          CONTRACTS_DIR, METRICS_DIR, REPORTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ── Storage backend ───────────────────────────────────────────────────────────
# False → disco local (padrão, sem dependências externas)
# True  → MinIO      (requer: docker compose up -d && pip install minio)
USE_MINIO = False

# ── MinIO (usado apenas quando USE_MINIO = True) ──────────────────────────────
MINIO_ENDPOINT   = "localhost:9000"
MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "minioadmin"

# ── Ollama ────────────────────────────────────────────────────────────────────
# Modelos recomendados por prioridade:
#   phi3.5          → melhor custo/benefício em CPU (3.8B)
#   phi4            → melhor qualidade de documentação (14B, lento em CPU)
#   qwen2.5-coder:7b → alternativa, mas otimizado para código
OLLAMA_HOST  = "http://localhost:11434"
OLLAMA_MODEL = "qwen2.5-coder:7b"

# Desativa o SLM sem alterar código (útil para testar o pipeline sem Ollama)
SKIP_SLM = False

# ── Qualidade ─────────────────────────────────────────────────────────────────
NULL_TOLERANCE_PCT  = 30.0   # % de nulos acima do qual o SLM reporta anomalia
DUPLICATE_TOLERANCE = 0.02   # 2% de duplicatas aceitas antes de warning
