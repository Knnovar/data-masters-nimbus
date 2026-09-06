# Testes — Projeto Nimbus

300 testes unitários usando `unittest` nativo do Python, sem dependências externas.

---

## Como rodar

```bash
python tasks.py test
python tests/run_tests.py -v
python tests/run_tests.py test_storage
python tests/run_tests.py test_bronze
```

---

## Cobertura por módulo

| Arquivo | Testes | Cobre |
|---|---|---|
| `test_contracts.py` | 17 | `DataContract`, `ColumnContract`, validação de versão |
| `test_manifest.py` | 22 | `ExtractorBase`, `ManifestWriter`, fluxo HITL |
| `test_storage.py` | 31 | `LocalStorage` todos os formatos + Parquet + contrato |
| `test_validator.py` | 11 | Cenários PASS, WARNING, DLQ, schema evolution |
| `test_sprint2.py` | 39 | `normalizer`, `extractor_csv`, `extractor_fixed`, `extractor_json` |
| `test_writers.py` | 48 | `CSVWriter`, `JSONWriter`, `FixedWidthWriter`, `WriterFactory`, `_adapt_layout` |
| `test_schema_utils.py` | 42 | Mapeamento de tipos, cast por categoria, metadata Parquet |
| `test_databricks.py` | 65 | `DatabricksUploader`, diagnose, Files API, CTAS, comentários, tags, `publish_table` |
| `test_bronze.py` | 25 | `BronzeUploader`, arquivo bruto no Volume, provenance, `publish_bronze` |
| **Total** | **300** | |

---

## O que os testes garantem

**Parquet e tipagem governada.** Coluna declarada como `boolean` com domínio `S/N` chega ao Silver como `pa.bool_()`. Coluna `date` respeita o formato do Manifest. Cast que falha em mais de 5% dos valores mantém string e registra WARNING. Metadata no footer indica `manifest_validated` ou `manifest_draft`.

**Validação e schema evolution.** Coluna obrigatória ausente sempre vai para DLQ. Coluna nova adicionada pela origem é classificada como NON_BREAKING. Manifest em DRAFT gera aviso sem bloquear. No gerador, `_adapt_layout` remove campos do leiaute posicional quando a origem os omite e acrescenta colunas novas com largura padrão.

**Manifest e governança.** Manifest com `# TODO` pendente não pode ser promovido. VALIDATED nunca é sobrescrito — writer cria `_draft.yaml` paralelo.

**Databricks Silver.** Credenciais vazias levantam `ValueError` antes de qualquer chamada de rede. Upload usa Files API (`PUT /api/2.0/fs/files`) com `overwrite=true` e partição Hive `dat_ref=YYYY-MM-DD`. `register_or_refresh` usa `CREATE OR REPLACE TABLE ... AS SELECT * FROM read_files(...)`. Comentários de colunas usam `description` do Manifest e ignoram `# TODO`. `publish_table()` nunca propaga exceção para o pipeline. `diagnose()` consulta `/api/2.0/sql/warehouses/{id}` e para no primeiro nível autenticado com 401.

**Databricks Bronze.** O arquivo bruto preserva o nome original no Volume. CTAS força `inferColumnTypes => false` e adiciona `_ingest_file`, `_ingest_time`, `_ingest_run_id`. Formatos sem `read_files` (ex.: `.layout`) sobem o arquivo e devolvem status `UPLOADED` sem criar tabela. `publish_bronze()` nunca propaga exceção.

**Writers multi-formato.** Fixed-Width respeita exatamente a contagem de bytes do leiaute. JSON de pipeline é flat (sem aninhamento). Formato inválido levanta `ValueError` com mensagem clara.

---

## Política de teste

Storage e Validator usam `LocalStorage` real com `tempfile.mkdtemp()`, não mocks. Databricks (Silver e Bronze) usa mock total — nenhuma chamada real à API. A geração de dados usa os mesmos geradores do pipeline para que os testes reflitam o que o usuário encontrará em produção. Detecção de encoding no `normalizer` é mockada quando o critério é o ramo UTF-8/LF, para não depender da versão do `chardet`.

---

## O que não tem cobertura automatizada

Integração real com Ollama (testada manualmente). Backend `MinIOStorage` (requer Docker). `prefect_flow.py` com servidor Prefect real (validado via `--no-prefect`). Upload real para Databricks (validado com `python tasks.py test-databricks` quando credenciais estão disponíveis).
