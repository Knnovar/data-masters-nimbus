# Changelog — Projeto Nimbus

Histórico de evolução do projeto. O objetivo deste documento é que alguém de fora consiga entender por que o projeto está estruturado como está — não apenas o que existe hoje, mas as decisões que moldaram cada escolha.

---

## Sprint 1 — Fundação

Arquitetura medallion completa com abstração de Storage, modelo de contrato estendido (`source`, `regulatory`, `steward`, `business_context`, `sample_queries`), extrator SAS7BDAT, fluxo HITL DRAFT → VALIDATED, integração SLM via Ollama, orquestração com `run_pipeline.py` e `prefect_flow.py` mapeado para Control-M. 65 testes unitários.

---

## Sprint 2 — Multi-formato e encoding

`normalizer.py` para encoding, extratores de Manifest para CSV, Fixed-Width e JSON. Refatoração do gerador de dados com padrão Strategy (`BaseWriter`, `CSVWriter`, `JSONWriter`, `FixedWidthWriter`). Sidecar `.layout` para fixed-width. Seis bugs corrigidos com causa raiz documentada. 148 testes unitários.

---

## Reestruturação e rebrand

`tasks.py` como runner cross-platform, documentação reorganizada em `docs/`, README reescrito como porta de entrada. Projeto renomeado de Data Masters para **Projeto Nimbus**.

---

## Sprint A — Parquet no Silver

O Silver passou a armazenar dados em Parquet com compressão Snappy. O arquivo original é preservado em `bronze/_archive/` para rastreabilidade. O `Storage.read()` detecta o formato pela extensão e usa o parser correto para cada um. 158 testes unitários.

---

## Sprint B — Integração Databricks (v1)

`src/connectors/databricks_uploader.py` com upload via DBFS API, registro de tabela no metastore e `test_connection()`. `DATABRICKS_AUTO_UPLOAD` ativa o upload automático após cada promoção Silver. Testes via mock sem chamadas reais. 175 testes unitários.

---

## Deploy Docker one-click

Stack Docker completo com três serviços: `nimbus`, `ollama` e `minio`. `scripts/entrypoint.sh` coordena a sequência de inicialização — aguarda healthchecks, baixa o modelo via `ollama pull`, inicia Prefect server, registra deployments, sobe worker e executa o pipeline. GPU NVIDIA e AMD/ROCm suportadas via configuração comentada. Modelo Ollama configurável via `.env`, baixado no primeiro boot. `config.py` reescrito para ler tudo via variáveis de ambiente.

---

## Sprint Parquet v2 — Tipagem governada pelo Manifest

O Parquet no Silver passou a respeitar os tipos declarados no Manifest em vez de inferi-los pelo PyArrow. A contradição arquitetural estava aqui: o Manifest era declarado como fonte de verdade sobre o schema, mas o Silver tinha tipos decididos pelo PyArrow na serialização — sem relação com o que o Data Steward havia validado.

`src/storage/schema_utils.py` é o módulo novo de responsabilidade única: converte tipos semânticos do Manifest para tipos físicos PyArrow e aplica o cast coluna a coluna. O cast é não-destrutivo — se mais de 5% dos valores falham, a coluna mantém string e o evento é registrado como WARNING. Booleanos reconhecem os domínios `S/N`, `0/1`, `SIM/NÃO`, `TRUE/FALSE`. Datas tentam o formato declarado no `business_rules` com fallback para formatos brasileiros conhecidos.

`promote_to_parquet()` passou a aceitar `contract=None`. Quando passado, aplica o schema declarado. Quando não, mantém inferência (backward-compatible).

Todo Parquet gerado carrega metadata rastreável no footer: `nimbus.schema_source`, `nimbus.manifest_version`, `nimbus.table`, `nimbus.generated_at`, `nimbus.warnings_count`. O Silver é auto-documentado.

`prefect_flow.py` e `run_pipeline.py` carregam o contrato antes da promoção e o passam ao `promote_to_parquet()`. O log indica `schema=manifest` ou `schema=inferido`. 231 testes unitários.

---

## Sprint Databricks v2 — Delta Lake e diagnóstico estruturado

O módulo de integração foi refatorado completamente para resolver três problemas: ausência do `warehouse_id` obrigatório, upload de arquivo único sem histórico e erros engolidos silenciosamente.

O fluxo por execução agora tem quatro etapas: upload em pasta por tabela (`/nimbus/silver/<tabela>/`), conversão para Delta via `CONVERT TO DELTA` (idempotente), registro com `CREATE TABLE USING DELTA` na primeira vez e `REFRESH TABLE` nas seguintes, e população automática de comentários de colunas a partir do Manifest.

`DATABRICKS_WAREHOUSE_ID` foi adicionado como variável obrigatória. O `diagnose()` valida a conectividade em quatro níveis sequenciais com mensagens de erro específicas. O `upload-silver` ganhou `--dry-run`, `--no-comments` e `--table`. 242 testes unitários.

---

## Sprint Databricks v3 — Volumes (Unity Catalog) e Files API

A integração com o Databricks foi refatorada para abandonar o DBFS em favor dos Volumes do Unity Catalog. A mudança foi motivada pelo erro `PERMISSION_DENIED: Public DBFS root is disabled` — workspaces Databricks novos bloqueiam o root do DBFS por padrão, e a direção da plataforma é descontinuá-lo em favor de Volumes gerenciados pelo Unity Catalog.

**O que mudou no upload.** A DBFS API (create → add-block → close com blocos base64) foi substituída pela Files API: um único `PUT /api/2.0/fs/files/<volume-path>?overwrite=true` com o binário do arquivo no corpo da requisição. O path segue o padrão de Volumes do Unity Catalog: `/Volumes/<catalog>/<schema>/<volume>/<tabela>/dat_ref=YYYY-MM-DD/`. O particionamento por data (`dat_ref`) foi introduzido nesta versão — cada execução do Nimbus adiciona uma partição ao Volume, permitindo rastrear histórico sem depender do Delta `_delta_log/`.

**O que mudou no registro de tabela.** O fluxo anterior usava `CONVERT TO DELTA` seguido de `CREATE TABLE USING DELTA LOCATION`. O novo usa `CREATE OR REPLACE TABLE ... AS SELECT * FROM read_files('<volume-path>', format => 'parquet')` — um CTAS direto que registra a tabela como managed Delta table lendo o Volume como fonte. Isso elimina a necessidade de conversão explícita e funciona com Unity Catalog sem configurações extras de external location.

**Metadata de tabela via tags.** O método `apply_table_metadata()` novo usa `COMMENT ON TABLE` para a descrição do `business_context` e `ALTER TABLE SET TAGS` / `ALTER COLUMN SET TAGS` para as `regulatory_flags` do Manifest. As tags aparecem no Unity Catalog como metadados pesquisáveis — um analista pode buscar todas as tabelas com a tag `LGPD_SENSITIVE` sem abrir nenhum arquivo.

**`publish_table()` substitui `upload_silver_table()` como interface principal.** Retorna sempre um dict `{table, status, target, error}` — nunca levanta exceção. O `run_pipeline.py` chama `publish_table()` explicitamente após `promote_to_parquet()` e coleta os resultados para reportar no resumo final.

**Suporte a OAuth.** Quando `DATABRICKS_TOKEN` está vazio, o uploader tenta OAuth via `databricks-sdk` (se instalado). Isso permite autenticação via browser em workspaces corporativos sem precisar gerar um PAT.

**Novos parâmetros de configuração:** `DATABRICKS_VOLUME` (nome do Volume UC onde os Parquets vão), `DATABRICKS_CATALOG` mudou default de `hive_metastore` para `workspace` (catalog padrão do CE com Unity Catalog habilitado).

**Passos para usar:**
```sql
-- No SQL Editor do Databricks, antes do primeiro upload:
CREATE SCHEMA IF NOT EXISTS workspace.nimbus;
CREATE VOLUME IF NOT EXISTS workspace.nimbus.landing;
```
```bash
python tasks.py test-databricks    # diagnóstico em 4 níveis
python tasks.py upload-silver --dry-run
python tasks.py upload-silver
```

---

## Sprint Databricks v4 — Camada Bronze e catalog `nimbus`

O Unity Catalog passou a espelhar a medallion local: catalog `nimbus`, schema `bronze` para o arquivo bruto e schema `silver` para o Parquet tipado. `DATABRICKS_SCHEMA` continua existindo como fallback; o uploader Silver lê `DATABRICKS_SILVER_SCHEMA` e o Bronze lê `DATABRICKS_BRONZE_SCHEMA`.

**Bronze no Databricks.** `src/connectors/bronze_uploader.py` reusa a Files API do Silver, mas preserva o nome original do arquivo e registra a tabela com `inferColumnTypes => false`. Colunas `_ingest_file`, `_ingest_time` e `_ingest_run_id` rastreiam a carga. O pipeline chama `publish_bronze()` logo após a geração, antes da validação — DLQ não apaga o que já chegou no Volume bronze.

**Diagnóstico.** `diagnose()` passou a usar `GET /api/2.0/sql/warehouses/{id}` (plural, endpoint oficial) via `_get`.

**Gerador.** `_adapt_layout` ajusta o leiaute posicional quando o cenário `non_breaking` adiciona coluna ou o `breaking` remove `cd_agencia`, para o Fixed-Width acompanhar o schema evolution.

**Suite.** 325 testes unitários, incluindo `tests/test_bronze.py`.


---

## Sprint `expand-minio` — Storage portavel, governanca no lake e idempotencia por conteudo

**Storage.** `MinIOStorage` ganhou `MINIO_SECURE` (TLS), `MINIO_REGION` (SigV4), `BUCKET_PREFIX`
(nome de bucket e global em S3) e `MINIO_CREATE_BUCKETS` (impede o pipeline de criar bucket em conta
gerenciada). O `secure=False` fixo — que impedia qualquer object storage gerenciado — foi corrigido.
O pipeline foi exercitado em MinIO e em um segundo servidor S3-compativel (Adobe S3Mock) com HTTPS e
regiao, trocando apenas variaveis de ambiente.

**Governanca no mesmo backend do dado.** `collect()` e `generate_report()` deixaram de escrever
direto no filesystem e passaram a usar `storage.write_text`; `show_metrics.py` le via
`storage.list("metrics")`. Antes disso o dado ia para o bucket e a governanca ficava no disco local.

**Falha visivel no Prefect.** Bloqueio de publicacao levanta `GateBlocked`, de modo que a run
aparece como Failed na UI/worker em vez de "Completed" com exit code ignorado. `--no-prefect`, que
era flag morta, passou a executar as funcoes puras (`.fn`) sem subir servidor efemero.

**Idempotencia por conteudo.** `src/ingestion/idempotency.py` calcula o SHA-256 do arquivo de
entrada em blocos de 1 MiB e mantem o ledger `metrics/_ingest_ledger.json` com chave
`(tabela, dat_ref, formato)`. Estados `FIRST_LOAD`, `REPROCESS_IDENTICAL` e `REPROCESS_MODIFIED`;
conteudo divergente registra `previous_sha256` e nao e pulado por `--skip-existing`; carga
bloqueada fica `BLOCKED` e nunca e tratada como concluida.

**Geracao deterministica.** Com `--dat-ref`, a semente vem de `SHA-256(scenario|format|dat_ref)` e
semeia `random`, NumPy, Faker e a geracao de UUID — a mesma carga logica produz o mesmo arquivo byte
a byte, o que torna o caso "reprocessamento identico" demonstravel.

**Correcoes de coerencia.** Modelo `phi4` alinhado entre `config.py`, `.env.example`, compose e
docs; `collect()` passou a receber `fmt` no fluxo Prefect (toda metrica saia como `"format": "csv"`);
score documentado com as dimensoes reais (conformidade 40 / completude 25 / unicidade 20 /
estabilidade 15); `MIGRATION_PLAN` corrigido quanto ao Azure Blob, que nao atende a API S3.

**Suite.** 592 testes unitarios, com os componentes novos cobertos: `test_idempotency.py`,
`test_quality_score.py`, `test_minio_storage.py`, `test_slm_metrics.py`, `test_prefect_flow.py` e
determinismo em `test_data_generator.py`.

---

## Sprint `one-click-security` — Bootstrap, credenciais e governanca de acesso

**One-click.** `scripts/nimbus_up.py` gera as credenciais do MinIO na primeira execucao (`.env` com
permissao 0600, nunca sobrescrito depois), sobe o container, aguarda o healthcheck e cria os buckets
pelo proprio `get_storage()` do pipeline — se o bootstrap funciona, o pipeline funciona pelo mesmo
caminho de codigo. Comandos: `up`, `down`, `demo`, `minio-creds`.

**Credenciais fora do repositorio.** O compose deixou de ter `minioadmin` como default e passou a
exigir `MINIO_ACCESS_KEY`/`MINIO_SECRET_KEY` (`${VAR:?}`); `get_storage()` falha explicitamente com
`USE_MINIO=true` sem credencial, em vez de tentar um default silencioso. Imagens pinadas
(`minio:RELEASE.2025-09-07T16-13-09Z`, `ollama:0.32.15`, `python:3.11.15-slim-bookworm`).

**Ordem gate/Silver.** O Parquet so existe depois do cast, entao a carga reprovada e movida da
Silver para a quarentena (`QUARANTINE_BLOCKED_SILVER`) — nenhum consumidor le carga bloqueada
achando que passou. O exit code 2 e o motivo do bloqueio sao preservados.

**Privacidade na quarentena.** `DATABRICKS_QUARANTINE_UPLOAD` passou a `false` por padrao e
`QUARANTINE_MASK_PII` mascara as colunas sensiveis declaradas no Manifest com o token
`MASK:<hash>` — deterministico para preservar correlacao entre linhas na investigacao do rejeito e,
por isso mesmo, **nao** e anonimizacao irreversivel.

**Do contrato para a permissao.** `python tasks.py emit-grants --file <manifest>` deriva o DDL de
`GRANT`/mask da classificacao de sensibilidade do Manifest e **nao executa nada** no workspace:
artefato revisavel, entregue a quem tem alcada. Classificacao restrita sai com o `GRANT SELECT`
comentado.

**Versionamento do Manifest.** `python tasks.py manifest-version` deriva a versao semantica do
contrato do diff contra o baseline (Git por padrao, lock file em `data/contracts/.lock/` como
fallback para container/tarball): coluna removida, tipo, `nullable` endurecido, PK, ordem de
colunas, formato da origem e tolerancia restringida sao MAJOR; coluna nova opcional, `nullable`
afrouxado e tolerancia relaxada sao MINOR; descricao e metadados sao PATCH. O `--apply` grava
`version_history` no proprio Manifest e devolve um contrato `VALIDATED` alterado para `DRAFT`,
porque a revalidacao continua sendo ato do Steward. O `manifest_validator` passou a recusar a
promocao de contrato alterado sem bump (`--skip-version-check` existe e e explicito).

**Suite.** 661 testes unitarios, com `test_gate_silver.py`, `test_grant_emitter.py`,
`test_pii_masking.py` e `test_manifest_version.py` cobrindo os itens acima.

---

## Contrato ilegivel deixa de degradar em silencio

O contrato e carregado duas vezes por tabela, uma no validador e uma no `run_scenario`. A falha na
segunda leitura era apenas impressa e o processamento seguia com `contract=None`, o que desligava o
cast dirigido pelo Manifest, o gate de governanca e o mascaramento de PII na quarentena enquanto a
tabela aparecia como `[LIBERADA]` no resumo. Agora essa falha produz `BLOCKED` com razao
`CONTRACT_UNREADABLE` e rotulo `[CONTRATO]`: a tabela nao e promovida, profiling e SLM nao rodam, a
publicacao da Silver e registrada como bloqueada, o ledger grava `BLOCKED` e a run sai com exit
code 2. Contrato ausente continua sendo barrado antes, pela validacao estrutural, que devolve
`DLQ`. 675 testes unitarios, com `test_contract_gate.py` cobrindo o bloqueio e a preservacao do
caminho normal.
