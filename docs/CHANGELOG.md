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
