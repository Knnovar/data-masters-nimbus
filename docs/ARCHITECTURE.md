# Arquitetura — Projeto Nimbus

Documento técnico de referência para a arquitetura do pipeline. Para uma
visão geral e início rápido, consulte o [README](../README.md).

---

## 1. Visão Geral do Fluxo

```
Arquivo bruto (CSV/JSON/Fixed-Width/SAS7BDAT)
        │
        ▼
┌───────────────────┐
│  NORMALIZER        │  encoding, CRLF→LF, BOM, EBCDIC (detecta e avisa)
└───────────────────┘
        │
        ▼
┌───────────────────┐
│  BRONZE             │  dado bruto, recém-chegado
└───────────────────┘
        │
        ▼
┌───────────────────┐      breaking change
│  VALIDATOR          │ ────────────────────► QUARANTINE (DLQ)
└───────────────────┘
        │ pass / warning
        ▼
┌───────────────────┐
│  PROFILER (DuckDB)  │  estatísticas por coluna
└───────────────────┘
        │
        ▼
┌───────────────────┐
│  SILVER             │  dado validado e promovido
└───────────────────┘
        │
        ▼
┌───────────────────┐
│  SLM (Ollama)        │  documentação semântica usando o Manifest VALIDATED
└───────────────────┘
        │
        ▼
┌───────────────────┐
│  METRICS + REPORTS  │  quality score, pipeline_report.md
└───────────────────┘
```

---

## 2. Arquitetura Medallion

| Camada | Diretório local | Papel |
|---|---|---|
| **Bronze** | `data/landing/` | Dado bruto, como chegou da origem |
| **Silver** | `data/processed/` | Dado validado e promovido pelo profiler |
| **Gold** | `data/gold/` | Métricas agregadas (reservado para evolução futura) |
| **Quarantine** | `data/quarantine/` | Arquivos com breaking change isolados (DLQ) |
| **Contracts** | `data/contracts/` | Manifestos YAML — um por tabela |
| **Metrics** | `data/metrics/` | JSON de métricas por execução |
| **Reports** | `data/reports/` | Documentação SLM + relatório consolidado |

---

## 3. Camada de Storage

`src/storage/storage.py` abstrai onde os dados fisicamente residem. O resto
do pipeline nunca acessa disco ou bucket diretamente — sempre via `storage`.

```python
storage.write("bronze", "tb_clientes.csv", df)
storage.read("bronze", "tb_clientes.csv")
storage.move("tb_clientes.csv", "bronze", "silver")
storage.write_text("contracts", "tb_clientes.yaml", yaml_str)
```

Dois backends implementados:

- **`LocalStorage`** — disco local, padrão da PoC, sem dependência externa
- **`MinIOStorage`** — object storage S3-compatível, ativado com `USE_MINIO=True`
  em `config.py` (requer `docker compose up -d`)

A troca de backend é transparente — nenhum outro módulo do pipeline sabe
qual está em uso. Isso antecipa a migração para ADLS Gen2 em produção
(ver [MIGRATION_PLAN.md](MIGRATION_PLAN.md)).

`storage.read()` detecta o formato pela extensão do arquivo e usa o parser
correto: `.csv` via pandas, `.json` via `json_normalize`, `.txt`/`.dat`
(fixed-width) via `read_fwf` com colspecs lidos de um arquivo sidecar
`.layout` gerado automaticamente na escrita.

---

## 4. Suporte Multi-formato

O projeto não trata apenas CSV — reflete a realidade de um banco, onde
dados chegam em formatos heterogêneos vindos de sistemas distintos.

| Formato | Geração (PoC) | Leitura (Storage) | Extração de Manifest |
|---|---|---|---|
| CSV | `CSVWriter` | `pd.read_csv` | `extractor_csv.py` (inferência por amostragem) |
| JSON | `JSONWriter` | `pd.json_normalize` | `extractor_json.py` (suporta aninhamento) |
| Fixed-Width | `FixedWidthWriter` | `pd.read_fwf` + sidecar | `extractor_fixed.py` (leiaute TXT/CSV/XLSX) |
| SAS7BDAT | — (apenas leitura) | — | `extractor_sas7bdat.py` (metadados internos) |

A geração de dados fictícios (`src/generators/`) usa o padrão **Strategy**:
cada formato tem um `Writer` (`src/generators/writers.py`) que recebe um
DataFrame em memória e devolve `(filename, content)` — a lógica de domínio
que inventa os dados nunca conhece o formato de saída.

---

## 5. Validação e Schema Evolution

`src/validation/validator.py` compara o arquivo recebido contra o contrato
declarado no manifest. Três cenários:

| Cenário | O que detecta | Resultado |
|---|---|---|
| **Baseline** | Dados conformes ao contrato | `PASS` ou `WARNING` (nulos/duplicatas dentro da tolerância) |
| **Non-breaking** | Coluna nova adicionada pela origem | `WARNING` — pipeline segue normalmente |
| **Breaking** | Coluna obrigatória removida ou tipo incompatível | `DLQ` — arquivo isolado em quarentena |

---

## 6. Profiling

`src/profiler/duckdb_profiler.py` usa DuckDB como engine principal (rápido,
sem servidor) com fallback automático para Pandas quando o formato não é
CSV/TSV ou quando o DuckDB não está disponível no ambiente.

Estatísticas geradas por coluna: contagem de nulos, valores únicos, min/max
(numéricos), top-N valores mais frequentes (categóricos).

---

## 7. Documentação Semântica (SLM)

Ver documento dedicado: [SLM.md](SLM.md).

---

## 8. Orquestração

Dois modos de execução, mesma lógica de negócio:

- **`run_pipeline.py`** — execução direta, sem dependências de orquestrador
- **`prefect_flow.py`** — mesma pipeline decorada com `@task`/`@flow` do
  Prefect 2.x, com mapeamento explícito para jobs Control-M

| Prefect Task | Job Control-M | Exit codes |
|---|---|---|
| `task_extract_manifest` | JOB-DM-000-EXTRACT (opcional) | 0=OK, 1=SKIPPED, 2=ERROR |
| `task_generate_data` | JOB-DM-001-GENERATE | 0=OK, 2=ERROR |
| `task_validate` | JOB-DM-002-VALIDATE | 0=PASS, 1=WARNING, 2=DLQ |
| `task_profile` | JOB-DM-003-PROFILE | 0=OK, 2=ERROR |
| `task_enrich_slm` | JOB-DM-004-ENRICH | 0=OK, 1=SKIPPED, 2=ERROR |
| `task_collect_metrics` | JOB-DM-005-METRICS | 0=OK |
| `task_report` | JOB-DM-006-REPORT | 0=OK |

Modo compatível com Control-M (sem servidor Prefect):

```bash
python prefect_flow.py --no-prefect --scenario baseline --run-id %%JOBRUNID%%
```

---

## 9. Métricas e Quality Score

`src/metrics/metrics_collector.py` calcula um score de 0-100 por tabela
a cada execução:

| Dimensão | Peso | Critério |
|---|---|---|
| Status de validação | 40 pts | PASS / WARNING / DLQ |
| Taxa de nulos | 30 pts | % de nulos em colunas obrigatórias |
| Taxa de duplicatas | 20 pts | % de chaves duplicadas |
| Cobertura de schema | 10 pts | % de colunas com `description` preenchida |

Dashboard de consulta: `python show_metrics.py` (ver [README](../README.md)).
