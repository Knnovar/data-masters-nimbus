# Próximos Passos — Projeto Nimbus

> Substituído a cada sessão. Histórico acumulado fica no CHANGELOG.md.

Última atualização: Sprint Databricks v2 — Delta Lake e diagnóstico estruturado.

---

## Pendente da última sessão

**Databricks — validação em ambiente real.** Tudo testado via mock. Quando as credenciais estiverem disponíveis:

```bash
# 1. Preenche .env com DATABRICKS_HOST, DATABRICKS_TOKEN, DATABRICKS_WAREHOUSE_ID
# 2. Valida conectividade
python tasks.py test-databricks
# 3. Simula sem enviar
python tasks.py upload-silver --dry-run
# 4. Upload real
python tasks.py baseline && python tasks.py upload-silver
```

**Docker + Ollama — timing na primeira execução.** Solução imediata:

```bash
docker run --rm -v ollama_models:/root/.ollama ollama/ollama pull phi3.5
docker compose up
```

Solução definitiva pendente: serviço `ollama-init` no `docker-compose.yml` que faz o pull e encerra antes do `nimbus` subir.

---

## Planejado

**Sprint C — Terraform.** Provisionar workspace Databricks CE, configurar MinIO como external location, criar schemas no metastore, definir permissões. `tfstate` local para a PoC.

**`MERGE INTO` para upsert incremental.** Hoje cada execução substitui os dados no Delta. Com chave primária declarada no Manifest, o uploader pode fazer merge incremental em vez de substituição completa.

**Fix Docker/Ollama.** Serviço `ollama-init` no compose que faz o pull uma vez e encerra antes do `nimbus` subir.

**`DESCRIBE HISTORY` no dashboard.** `show_metrics.py` consultando histórico Delta e exibindo junto com métricas locais.

**CLI unificada de extração de Manifest.** `python tasks.py extract --file <path> --table <nome>` com detecção automática de formato.

**Série histórica de quality score.** Tabela Gold consolidando histórico de scores por execução para acompanhamento contínuo.
