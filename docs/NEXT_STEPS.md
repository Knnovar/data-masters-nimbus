# Próximos Passos — Projeto Nimbus

> Substituído a cada sessão. Histórico acumulado fica no CHANGELOG.md.

Última atualização: Sprint Databricks v3 — Volumes (Unity Catalog) e Files API.

---

## Pendente da última sessão

**Databricks — validação em ambiente real pós-migração para Volumes.** O código foi atualizado para usar a Files API e Volumes UC. Os passos para validar:

```sql
-- No SQL Editor do Databricks, antes do primeiro upload:
CREATE SCHEMA IF NOT EXISTS workspace.nimbus;
CREATE VOLUME IF NOT EXISTS workspace.nimbus.landing;
```

```bash
# Preenche .env com DATABRICKS_HOST, DATABRICKS_TOKEN, DATABRICKS_WAREHOUSE_ID
# DATABRICKS_CATALOG=workspace  (padrão CE com UC)
# DATABRICKS_VOLUME=landing

python tasks.py test-databricks        # valida os 4 níveis
python tasks.py upload-silver --dry-run
python tasks.py baseline && python tasks.py upload-silver
```

**Docker + Ollama — problema de timing.** Na primeira execução com `docker compose up --build`, o download do modelo pode ultrapassar o timeout do healthcheck. Solução imediata enquanto o fix definitivo não é implementado:

```bash
docker run --rm -v ollama_models:/root/.ollama ollama/ollama pull phi3.5
docker compose up --build
```

---

## Planejado

**Sprint C — Terraform.** Com a integração Databricks funcionando via Volumes, o Terraform tem escopo concreto: provisionar workspace CE, criar catalog `workspace`, schema `nimbus` e Volume `landing`, configurar warehouse e permissões de acesso.

**Fix Docker/Ollama — serviço `ollama-init`.** Separar o pull do modelo em um serviço que roda uma vez e encerra antes do `nimbus` subir, eliminando a condição de corrida entre healthcheck e download.

**`MERGE INTO` para upsert incremental.** Hoje cada partição `dat_ref` substitui a anterior com `overwrite=true`. Para dados reais com chave primária declarada no Manifest, implementar upsert via `MERGE INTO` usando a chave do contrato.

**`DESCRIBE HISTORY` no dashboard.** `show_metrics.py` consultando histórico Delta das tabelas no Databricks e exibindo junto com as métricas locais.

**CLI unificada de extração de Manifest.** `python tasks.py extract --file <path> --table <nome>` com detecção automática de formato.

**Série histórica de quality score.** Tabela Gold consolidando histórico de scores por execução.
