# Próximos Passos — Projeto Nimbus

> Substituído a cada sessão. Histórico acumulado fica no CHANGELOG.md.

Última atualização: Sprint Databricks v4 — Bronze no UC + catalog `nimbus`.

---

## Pendente da última sessão

**Databricks — validação em ambiente real do layout bronze/silver.** O código e os testes de mock cobrem Files API, CTAS STRING no Bronze e Parquet no Silver. Falta confirmar no workspace:

```sql
CREATE SCHEMA IF NOT EXISTS nimbus.bronze;
CREATE SCHEMA IF NOT EXISTS nimbus.silver;
CREATE VOLUME IF NOT EXISTS nimbus.bronze.landing;
CREATE VOLUME IF NOT EXISTS nimbus.silver.landing;
```

```bash
# .env: DATABRICKS_HOST, DATABRICKS_TOKEN, DATABRICKS_WAREHOUSE_ID
# DATABRICKS_CATALOG=nimbus
# DATABRICKS_SILVER_SCHEMA=silver
# DATABRICKS_BRONZE_SCHEMA=bronze

python tasks.py test-databricks
python tasks.py upload-bronze
python tasks.py upload-silver --dry-run
python tasks.py baseline
```

**Docker + Ollama — problema de timing.** Na primeira execução com `docker compose up --build`, o download do modelo pode ultrapassar o timeout do healthcheck. Solução imediata enquanto o fix definitivo não é implementado:

```bash
docker run --rm -v ollama_models:/root/.ollama ollama/ollama pull phi3.5
docker compose up --build
```

---

## Planejado

**Sprint C — Terraform.** Provisionar catalog `nimbus`, schemas `bronze` e `silver`, Volumes `landing` em cada schema, warehouse e permissões.

**Fix Docker/Ollama — serviço `ollama-init`.** Separar o pull do modelo em um serviço que roda uma vez e encerra antes do `nimbus` subir.

**`MERGE INTO` para upsert incremental.** Hoje cada partição `dat_ref` substitui a anterior com `overwrite=true`. Para dados reais com chave primária declarada no Manifest, implementar upsert via `MERGE INTO`.

**`DESCRIBE HISTORY` no dashboard.** `show_metrics.py` consultando histórico Delta das tabelas no Databricks e exibindo junto com as métricas locais.

**CLI unificada de extração de Manifest.** `python tasks.py extract --file <path> --table <nome>` com detecção automática de formato.

**Série histórica de quality score.** Tabela Gold consolidando histórico de scores por execução.

**Publicação Databricks no `prefect_flow.py`.** O `run_pipeline.py` já chama `publish_bronze` / `publish_table`; o fluxo Prefect ainda não.
