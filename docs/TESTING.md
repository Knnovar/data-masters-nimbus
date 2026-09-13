# Testes — Projeto Nimbus

592 testes unitarios usando `unittest` nativo do Python, sem dependencias externas de teste.

```
Ran 592 tests
OK (skipped=1)
```

---

## Como rodar

```bash
python tasks.py test
python tests/run_tests.py -v
python tests/run_tests.py test_idempotency
SKIP_SLM=true python -m unittest discover -s tests -q     # sem Ollama
```

`SKIP_SLM=true` evita depender do Ollama; nenhum teste faz chamada de rede.

---

## Cobertura por modulo

| Arquivo | Testes | Cobre |
|---|---|---|
| `test_contracts.py` | 17 | `DataContract`, `ColumnContract`, validacao de versao |
| `test_manifest.py` | 22 | `ExtractorBase`, `ManifestWriter`, fluxo HITL |
| `test_storage.py` | 31 | `LocalStorage` em todos os formatos + Parquet + contrato |
| `test_minio_storage.py` | 20 | `MinIOStorage`: buckets, prefixo, TLS, regiao, `create_buckets`, paridade de interface |
| `test_validator.py` | 11 | PASS, WARNING, DLQ, schema evolution |
| `test_strict_cast.py` | 116 | Cast dirigido pelo Manifest, rejeito por linha, `DUPLICATE_PK`, tolerancia |
| `test_schema_utils.py` | 42 | Mapeamento de tipos, cast por categoria, metadata Parquet |
| `test_writers.py` | 48 | `CSVWriter`, `JSONWriter`, `FixedWidthWriter`, `WriterFactory`, `_adapt_layout` |
| `test_sprint2.py` | 39 | `normalizer`, `extractor_csv`, `extractor_fixed`, `extractor_json` |
| `test_data_generator.py` | 34 | Geradores por formato + geracao deterministica (`seed_all`, `_uuid4`, hash por `dat_ref`) |
| `test_idempotency.py` | 34 | `resolve_dat_ref`, `file_sha256`, ledger, `classify_load`, `--skip-existing`, ciclo completo |
| `test_quality_score.py` | 26 | Pesos, renormalizacao, DLQ, cast reprovado, PK, duplicatas, limites 0-100 |
| `test_slm_metrics.py` | 24 | `_slm_metrics`, flatten, `SKIPPED`, tag DRAFT, persistencia de metricas e relatorio |
| `test_prefect_flow.py` | 22 | `_exit_code`, `_metric_exit_code`, `GateBlocked`, `--no-prefect`, paridade com o runner direto |
| `test_databricks.py` | 65 | `DatabricksUploader`, diagnose, Files API, CTAS, comentarios, tags, `publish_table` |
| `test_bronze.py` | 26 | `BronzeUploader`, arquivo bruto no Volume, provenance, `publish_bronze` |
| `test_exit_codes.py` | 8 | Contrato de exit code fim a fim |
| `test_steward_tags_quarantine.py` | 7 | Tags de governanca e roteamento de quarentena |
| **Total** | **592** | |

---

## O que os testes garantem

**Parquet e tipagem governada.** Coluna declarada `boolean` com dominio `S/N` chega ao Silver como
`pa.bool_()`. Coluna `date` respeita o formato do Manifest. Cast que falha acima da tolerancia
mantem string e registra WARNING. Metadata no footer indica `manifest_validated` ou
`manifest_draft`.

**Validacao e schema evolution.** Coluna obrigatoria ausente sempre vai para DLQ. Coluna nova da
origem e classificada como NON_BREAKING. Manifest em DRAFT gera aviso sem bloquear (e bloqueia com
`REQUIRE_VALIDATED_MANIFEST`). `_adapt_layout` remove campos do leiaute posicional quando a origem
os omite e acrescenta colunas novas com largura padrao.

**Manifest e governanca.** Manifest com `# TODO` pendente nao pode ser promovido. VALIDATED nunca e
sobrescrito — o writer cria `_draft.yaml` paralelo.

**Idempotencia e SHA-256.** `file_sha256` bate com `hashlib` inclusive em arquivo maior que o bloco
de 1 MiB, e devolve `None` (degradando para controle por `dat_ref`, sem interromper a carga) quando
o caminho nao existe, e diretorio ou e vazio. `classify_load` distingue `FIRST_LOAD`,
`REPROCESS_IDENTICAL` e `REPROCESS_MODIFIED`, preserva `previous_sha256`, incrementa
`reprocess_count`, trata entrada legada sem hash como identica, diferencia por formato e mantem
carga `BLOCKED` fora do `--skip-existing`. Ledger inexistente ou corrompido nao derruba a execucao.

**Geracao deterministica.** A mesma chave `(scenario, format, dat_ref)` produz a mesma semente, o
mesmo UUID e o mesmo arquivo — verificado comparando o SHA-256 de duas geracoes em CSV, JSON e
fixed. `dat_ref` ou cenario diferente produz hash diferente. Sem `dat_ref`, o comportamento
aleatorio anterior e preservado.

**Quality score.** Os quatro pesos somam 100. Dimensao nao mensuravel vira `None` e o peso e
renormalizado entre as medidas. Score nunca sai de 0-100. DLQ, cast reprovado, PK ausente,
duplicatas, contrato permissivo e ausencia de profiling tem resultado verificado.

**Storage portavel.** `MinIOStorage` e exercitado contra um duplo em memoria: criacao de buckets,
`MINIO_CREATE_BUCKETS=false`, `BUCKET_PREFIX`, TLS, regiao, `write`/`read`/`write_text`/
`write_parquet`/`move`/`promote_to_parquet`/`list`/`exists`, arquivamento, colunas de linhagem e
selecao de backend em `get_storage()`. A paridade de interface com `LocalStorage` e verificada, para
que um backend nao evolua sem o outro.

**Metricas e relatorio.** As metricas gravadas em JSON sao iguais ao registro em memoria, incluem
linhagem, `dat_ref`, score por dimensao, gate, rejeitos e desempenho da SLM, e o relatorio
consolidado carrega o aviso `[AI_METADATA_STATUS: DRAFT]`. Execucao sem metricas nao quebra o
relatorio.

**Prefect e exit codes.** O mapeamento `PASS/WARNING/SKIPPED -> 0`, `DLQ/ERROR -> 2` e a elevacao
para 2 em `gate_status=BLOCKED` sao verificados; `GateBlocked` preserva o resultado da run; o modo
`--no-prefect` executa as funcoes puras e produz o mesmo exit code do runner direto.

**Databricks.** Credenciais vazias levantam `ValueError` antes de qualquer chamada de rede. Upload
usa Files API (`PUT /api/2.0/fs/files`) com `overwrite=true` e particao Hive `dat_ref=YYYY-MM-DD`.
`register_or_refresh` usa `CREATE OR REPLACE TABLE ... AS SELECT * FROM read_files(...)`.
Comentarios de coluna usam `description` do Manifest e ignoram `# TODO`. `publish_table()` e
`publish_bronze()` nunca propagam excecao. O Bronze preserva o nome original do arquivo e forca
`inferColumnTypes => false`, acrescentando `_ingest_file`, `_ingest_time` e `_ingest_run_id`.

**Writers multi-formato.** Fixed-Width respeita exatamente a contagem de bytes do leiaute. JSON de
pipeline e flat. Formato invalido levanta `ValueError` com mensagem clara.

---

## Politica de teste

Storage e Validator usam `LocalStorage` real com `tempfile.mkdtemp()`, nao mocks. `MinIOStorage` usa
um duplo em memoria injetado em `sys.modules` — sem Docker e sem rede. Databricks usa mock total.
A geracao de dados usa os mesmos geradores do pipeline, para que o teste reflita o que o usuario
encontra na execucao. Deteccao de encoding no `normalizer` e mockada quando o critério e o ramo
UTF-8/LF, para nao depender da versao do `chardet`.

O unico teste marcado como `skipped` verifica a transparencia dos decorators do Prefect e e pulado
quando o Prefect esta instalado, porque os decorators reais subiriam um servidor efemero. O caminho
que importa — execucao por `.fn`, que e o que `--no-prefect` faz — continua coberto.

---

## O que nao tem cobertura automatizada

| Area | Como foi verificado |
|---|---|
| Integracao real com Ollama | execucao manual (`SKIP_SLM=false`) |
| MinIO real, S3Mock com TLS/regiao | execucao manual do pipeline nos 3 formatos |
| AWS S3 em conta real | **nao verificado** |
| Servidor Prefect real (UI/worker/deployment) | execucao manual; `--no-prefect` coberto por teste |
| Upload real para Databricks | `python tasks.py test-databricks` quando ha credencial; **nao verificado** em workspace |
| Concorrencia / execucao paralela | fora de escopo: o pipeline e sequencial por escolha |
