# Testes — Projeto Nimbus

242 testes unitários usando `unittest` nativo do Python, sem dependências externas.

---

## Como rodar

```bash
python tasks.py test
python tests/run_tests.py -v
python tests/run_tests.py test_storage
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
| `test_writers.py` | 44 | `CSVWriter`, `JSONWriter`, `FixedWidthWriter`, `WriterFactory` |
| `test_schema_utils.py` | 42 | Mapeamento de tipos, cast por categoria, metadata Parquet |
| `test_databricks.py` | 36 | `DatabricksUploader`, diagnose, upload, Delta, comentários |
| **Total** | **242** | |

---

## O que os testes garantem

**Parquet e tipagem governada.** Coluna declarada como `boolean` com domínio `S/N` chega ao Silver como `pa.bool_()`. Coluna `date` respeita o formato do Manifest. Cast que falha em mais de 5% dos valores mantém string e registra WARNING. Metadata no footer indica `manifest_validated` ou `manifest_draft`.

**Validação e schema evolution.** Coluna obrigatória ausente sempre vai para DLQ. Coluna nova adicionada pela origem é classificada como NON_BREAKING. Manifest em DRAFT gera aviso sem bloquear.

**Manifest e governança.** Manifest com `# TODO` pendente não pode ser promovido. VALIDATED nunca é sobrescrito — writer cria `_draft.yaml` paralelo.

**Databricks uploader.** Credenciais vazias levantam `ValueError` antes de qualquer chamada de rede. Upload usa blocos base64 válidos. `convert_to_delta` é idempotente — "already delta" retorna True sem erro. `register_or_refresh` usa `CREATE TABLE USING DELTA` na primeira vez e `REFRESH TABLE` nas seguintes. Comentários de colunas usam `description` do Manifest e ignoram `# TODO`. Falha no upload nunca propaga exceção para o pipeline.

**Writers multi-formato.** Fixed-Width respeita exatamente a contagem de bytes do leiaute. JSON com aninhamento produz estrutura válida. Formato inválido levanta `ValueError` com mensagem clara.

---

## Política de teste

Storage e Validator usam `LocalStorage` real com `tempfile.mkdtemp()`, não mocks. Databricks usa mock total — nenhuma chamada real à API. A geração de dados usa os mesmos geradores do pipeline para que os testes reflitam o que o usuário encontrará em produção.

---

## O que não tem cobertura automatizada

Integração real com Ollama (testada manualmente). Backend `MinIOStorage` (requer Docker). `prefect_flow.py` com servidor Prefect real (validado via `--no-prefect`). Upload real para Databricks (validado manualmente quando credenciais disponíveis).
