# Testes — Projeto Nimbus

175 testes unitários usando `unittest` nativo do Python, sem dependências externas. A escolha pelo `unittest` em vez do `pytest` foi deliberada — qualquer pessoa com Python instalado consegue rodar os testes sem instalar mais nada.

---

## Como rodar

```bash
python tasks.py test

# Ou diretamente
python tests/run_tests.py -v
python tests/run_tests.py test_storage
python tests/run_tests.py test_databricks
```

---

## Cobertura por módulo

| Arquivo | Testes | Cobre |
|---|---|---|
| `test_contracts.py` | 17 | `DataContract`, `ColumnContract`, validação de versão |
| `test_manifest.py` | 22 | `ExtractorBase`, `ManifestWriter`, fluxo HITL |
| `test_storage.py` | 25 | `LocalStorage` com todos os formatos + Parquet |
| `test_validator.py` | 11 | Cenários PASS, WARNING e DLQ |
| `test_sprint2.py` | 39 | `normalizer`, `extractor_csv`, `extractor_fixed`, `extractor_json` |
| `test_writers.py` | 44 | `CSVWriter`, `JSONWriter`, `FixedWidthWriter`, `WriterFactory`, `generate_all` |
| `test_databricks.py` | 17 | `DatabricksUploader`, upload, registro de tabela, conectividade |
| `test_schema_utils.py` | 46 | Mapeamento de tipos, cast por categoria, casos de borda, metadata Parquet |
| **Total** | **231** | |

---

## O que os testes garantem

Além de confirmar que o código roda, os testes garantem comportamentos de negócio específicos.

**Parquet e promoção.** O `promote_to_parquet()` grava o Silver em Parquet e move o original para `_archive/` — o arquivo não é deletado. Colunas numéricas preservam seus tipos no Parquet, sem a conversão implícita para string que acontece no CSV. Em datasets de 500 linhas ou mais, o Parquet com Snappy é menor que o CSV equivalente.

**Validação.** Um arquivo com coluna obrigatória ausente sempre vai para DLQ, nunca passa silenciosamente. Uma coluna nova adicionada pela origem é classificada como NON_BREAKING. Um Manifest em DRAFT gera aviso informativo sem bloquear a execução.

**Manifest e governança.** Um Manifest com campos `# TODO` pendentes não pode ser promovido para VALIDATED. Um Manifest VALIDATED nunca é sobrescrito — o writer cria um `_draft.yaml` paralelo.

**Writers multi-formato.** O arquivo Fixed-Width respeita exatamente a contagem de bytes do leiaute, incluindo padding e truncamento. JSON com aninhamento produz estrutura válida sem dicts não-serializáveis. Formato inválido levanta `ValueError` com mensagem clara.

**Tipagem governada pelo Manifest.** Uma coluna declarada como `boolean` com domínio `S/N` chega ao Silver como `pa.bool_()` — o PyArrow jamais inferiria isso sozinho. Uma coluna declarada como `date` com formato `%d/%m/%Y` chega como `pa.date32()`. Quando o cast falha em mais de 5% dos valores, a coluna é mantida como string e o evento é registrado — nunca silencioso. O metadata do Parquet reflete se o schema veio de um Manifest `VALIDATED` ou `DRAFT`. Colunas extras no dado (NON_BREAKING) entram no Silver como `pa.string()` sem bloquear a promoção.

**Databricks uploader.** Credenciais vazias levantam `ValueError` antes de qualquer chamada de rede. O upload envia os dados em blocos base64 válidos via as três etapas da DBFS API (create, add-block, close). O registro de tabela inclui `CREATE SCHEMA`, `CREATE OR REPLACE TABLE` e `LOCATION` apontando para o Parquet. Falha no upload não propaga exceção — o pipeline continua normalmente.

**Encoding e normalização.** CRLF converte para LF sem corromper conteúdo. BOM é removido. EBCDIC é detectado e sinalizado sem conversão. Arquivo original sempre vai para backup antes de qualquer alteração.

---

## O que não tem cobertura automatizada

A integração real com o Ollama é testada manualmente — depende de um serviço externo rodando. O backend `MinIOStorage` requer Docker e está fora do escopo de testes unitários. O `prefect_flow.py` com servidor Prefect real é validado via `--no-prefect`. O upload real para o Databricks é validado manualmente quando as credenciais estão configuradas em `config.py`.

---

## Política de teste do projeto

Os testes de Storage e Validator usam `LocalStorage` real apontando para diretórios temporários criados por `tempfile.mkdtemp()`, não mocks. Isso garante que o comportamento de ponta a ponta é validado, não apenas a lógica interna de cada função. Os testes do `DatabricksUploader` usam mocks de rede via `unittest.mock.patch` — nenhuma chamada real ao Databricks é feita, o que permite rodar os testes sem credenciais configuradas.
