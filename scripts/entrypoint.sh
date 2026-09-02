#!/bin/bash
set -euo pipefail
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
log() { echo -e "${BLUE}[NIMBUS]${NC} $*"; }
ok()  { echo -e "${GREEN}[OK]${NC} $*"; }
warn(){ echo -e "${YELLOW}[WARN]${NC} $*"; }

SCENARIO=${DEFAULT_SCENARIO:-baseline}
FORMAT=${DEFAULT_FORMAT:-all}
OLLAMA_MODEL=${OLLAMA_MODEL:-phi3.5}
OLLAMA_HOST=${OLLAMA_HOST:-http://ollama:11434}
PREFECT_API_URL=${PREFECT_API_URL:-http://127.0.0.1:4200/api}
MINIO_ENDPOINT=${MINIO_ENDPOINT:-minio:9000}

log "Aguardando MinIO em ${MINIO_ENDPOINT}..."
until curl -sf "http://${MINIO_ENDPOINT}/minio/health/live" > /dev/null 2>&1; do echo -n "."; sleep 2; done
ok "MinIO pronto"

log "Aguardando Ollama em ${OLLAMA_HOST}..."
until curl -sf "${OLLAMA_HOST}/api/tags" > /dev/null 2>&1; do echo -n "."; sleep 3; done
ok "Ollama pronto"

log "Verificando modelo: ${OLLAMA_MODEL}"
if curl -sf "${OLLAMA_HOST}/api/tags" | grep -q "\"${OLLAMA_MODEL%%:*}"; then
    ok "Modelo ${OLLAMA_MODEL} ja disponivel"
else
    log "Baixando ${OLLAMA_MODEL} (primeira execucao — pode demorar)..."
    if curl -sf --max-time 1800 "${OLLAMA_HOST}/api/pull" \
        -d "{\"name\": \"${OLLAMA_MODEL}\", \"stream\": false}" \
        -H "Content-Type: application/json" > /dev/null; then
    ok "Modelo ${OLLAMA_MODEL} pronto"
    else
        warn "Pull de ${OLLAMA_MODEL} falhou - seguindo com SKIP_SLM=true"
        export SKIP_SLM=true
fi

log "Iniciando servidor Prefect..."
export PREFECT_API_URL
prefect server start --host 0.0.0.0 --port 4200 &
PREFECT_PID=$!

log "Aguardando Prefect API..."
until curl -sf "${PREFECT_API_URL}/health" > /dev/null 2>&1; do echo -n "."; sleep 2; done
ok "Prefect pronto — UI em http://localhost:4200"

log "Registrando deployments..."
python setup_prefect.py && ok "Deployments registrados" || warn "Falha nos deployments — continuando"

log "Iniciando worker Prefect..."
prefect worker start --pool nimbus-local &
sleep 5

log "=============================================="
log " Pipeline: cenario=${SCENARIO} | formato=${FORMAT}"
log "=============================================="
EXIT=0
python run_pipeline.py --scenario "${SCENARIO}" --format "${FORMAT}" || EXIT=$?
[ $EXIT -eq 0 ] && ok "Pipeline concluida" || warn "Pipeline com exit code ${EXIT}"

log "Container pronto para comandos:"
log "  docker compose exec nimbus python tasks.py metrics"
log "  docker compose exec nimbus python tasks.py upload-silver"
log "  Prefect UI : http://localhost:4200"
log "  MinIO UI   : http://localhost:9001"

wait $PREFECT_PID
