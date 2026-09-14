# Proximos Passos — Projeto Nimbus

> Substituido a cada sessao. Historico acumulado fica no CHANGELOG.md.

Ultima atualizacao: sprint `feature/expand-minio` — metricas/relatorios no storage configuravel,
portabilidade S3 (TLS, regiao, prefixo), idempotencia com SHA-256 do input, geracao deterministica e
cobertura de teste dos componentes novos (592 testes).

---

## 1. Concluido nesta sprint

- Metricas, relatorio e ledger gravados pelo storage configurado (local ou MinIO/S3), e
  `show_metrics.py` lendo do mesmo backend.
- `MinIOStorage` com `MINIO_SECURE`, `MINIO_REGION`, `BUCKET_PREFIX` e `MINIO_CREATE_BUCKETS`;
  pipeline exercitado em MinIO e em um segundo servidor S3-compativel com HTTPS.
- `GateBlocked`: bloqueio de publicacao aparece como run **Failed** no Prefect, mantendo exit 2 na
  CLI; `--no-prefect` passou a executar as funcoes puras, sem servidor efemero.
- Idempotencia: `(tabela, dat_ref, formato)` + SHA-256 do arquivo de entrada, com
  `FIRST_LOAD` / `REPROCESS_IDENTICAL` / `REPROCESS_MODIFIED`, `previous_sha256` e `--skip-existing`
  respeitando conteudo modificado e carga `BLOCKED`.
- Geracao deterministica por `--dat-ref` (semente derivada de `SHA-256(scenario|format|dat_ref)`),
  o que torna o caso "reprocessamento identico" demonstravel.
- Cobertura dos componentes novos: `test_idempotency.py`, `test_quality_score.py`,
  `test_minio_storage.py`, `test_slm_metrics.py`, `test_prefect_flow.py` e determinismo em
  `test_data_generator.py`.
- Higiene do ambiente de demonstracao: imagens pinadas
  (`quay.io/minio/minio:RELEASE.2025-09-07T16-13-09Z`, `ollama/ollama:0.32.15`,
  `python:3.11.15-slim-bookworm`) e credencial de object storage sem default — compose com
  `${MINIO_ACCESS_KEY:?...}`, `config.py` com variavel vazia e `get_storage()` levantando
  `RuntimeError` quando `USE_MINIO=true` sem credencial.

---

## 2. Pendente — maior retorno primeiro

**Versionamento de Manifest.** O ciclo DRAFT -> VALIDATED e real e auditavel, mas `version` fica
fixa em `1.0.0`: falta bump automatico (`non_breaking` -> minor, `breaking` -> major), diff do
`_draft` contra o vigente no `check-manifest` e algum registry/historico. Hoje a evolucao de versao
e manual e nao rastreada.

**Ordem gate/Silver.** O gate barra a publicacao, mas a Silver local ja foi escrita. Duas saidas:
promover para Silver somente depois do gate, ou marcar explicitamente o artefato reprovado
(sufixo/pasta de staging) para que nenhum consumidor leia carga bloqueada por engano.

**Quarentena com PII.** Os rejeitos preservam o valor original e `DATABRICKS_QUARANTINE_UPLOAD` vem
`true`. Decidir: mascarar na quarentena, restringir o schema de destino, ou desligar o upload por
padrao.

**Deteccao de dado sensivel.** A marcacao e heuristica por nome de coluna; nomes legados
(`NRDOC`, `DDD_FONE`, `LOGRAD`) escapam. Uma lista de sinonimos declarada no Manifest resolveria a
maior parte dos casos sem prometer classificacao juridica.

**Papel da SLM.** O modelo local propoe metadado e nada mais: toda saida nasce `[AI_METADATA_STATUS:
DRAFT]` e so vira contrato depois de `validate-manifest` com Steward nomeado. Isso e desenho, nao
governanca de IA corporativa — falta politica de uso de modelo, registro de prompt/resposta e
revisao formal de vies antes de qualquer uso alem de PoC.

**Decidir o destino do Gold.** Ou uma agregacao minima de verdade (serie historica de score, por
exemplo), ou remover Gold da narrativa e do compose e declarar "medallion ate Silver, por escopo".

---

## 3. Planejado (fora do escopo desta PoC)

**Databricks em workspace real.** Codigo e testes cobrem Files API, CTAS STRING no Bronze e Parquet
no Silver com mock. Falta confirmar no workspace:

```sql
CREATE SCHEMA IF NOT EXISTS nimbus.bronze;
CREATE SCHEMA IF NOT EXISTS nimbus.silver;
CREATE VOLUME IF NOT EXISTS nimbus.bronze.landing;
CREATE VOLUME IF NOT EXISTS nimbus.silver.landing;
```

```bash
# .env: DATABRICKS_HOST, DATABRICKS_TOKEN, DATABRICKS_WAREHOUSE_ID
python tasks.py test-databricks
python tasks.py upload-bronze
python tasks.py upload-silver --dry-run
python tasks.py baseline
```

**AWS S3 em conta real.** A compatibilidade de API, TLS, regiao e prefixo esta exercitada com dois
servidores S3-compativeis. Para AWS falta conta, IAM de escopo minimo, nome unico de bucket e
controle de custo — nao codigo. Receita e politica de exemplo em [STORAGE_S3.md](STORAGE_S3.md).

**Terraform.** Provisionar catalog `nimbus`, schemas `bronze`/`silver`, Volumes `landing`, warehouse
e permissoes.

**Fix Docker/Ollama — servico `ollama-init`.** Separar o pull do modelo em um servico que roda uma
vez e encerra antes do `nimbus` subir, eliminando o timeout do healthcheck no primeiro boot.

**`MERGE INTO` para upsert incremental.** Hoje cada particao `dat_ref` substitui a anterior com
`overwrite=true`. Para dado real com PK declarada no Manifest, upsert via `MERGE INTO`.

**`DESCRIBE HISTORY` no dashboard.** `show_metrics.py` mostrando o historico Delta junto das
metricas locais.

**Operacao.** Retry com backoff, lock de execucao, estado `RUNNING` no ledger e atomicidade entre
publicacao e ledger — o que falta para "operavel por terceiros" sem ressalva.

**Escala.** Substituir o executor pandas por Spark caso o volume deixe de caber em single-node. O
Manifest, o roteamento de rejeito e o contrato de exit code sobrevivem a essa troca; e o executor que
muda.
