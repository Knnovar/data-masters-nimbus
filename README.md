# Pipeline Data Masters - PoC Local

Pipeline completa de dados com arquitetura medallion (Bronze -> Silver -> Gold),
contratos evolutivos, profiling estatistico e documentacao semantica via SLM local.

---

## Estrutura de pastas

```
data-masters/
|
|-- config.py                        Configuracao central (modelos, paths, flags)
|-- run_pipeline.py                  Entry point direto (sem Prefect)
|-- prefect_flow.py                  DAG com 6 tasks mapeadas ao Control-M
|-- prefect.yaml                     Configuracao de deployments do Prefect
|-- setup_prefect.py                 Setup do work pool e registro de deployments
|-- show_metrics.py                  Dashboard de metricas no terminal
|-- Makefile                         Atalhos de execucao (make run, make metrics...)
|-- docker-compose.yml               MinIO local (opcional)
|-- requirements.txt                 Dependencias Python
|-- .gitignore
|
|-- README.md                        Este arquivo
|-- MIGRATION_PLAN.md                Plano de migracao Azure + Databricks + Control-M
|-- MANIFEST_ARCHITECTURE.md        Arquitetura do manifesto estendido (Sprint 1)
|-- SPRINT2_SPECS.md                 Especificacoes tecnicas Sprint 2 (multi-formato)
|-- HANDOFF.md                       Contexto de retomada para LLM
|-- context.md                       Historico de desenvolvimento e estado atual
|
|-- src/
|   |
|   |-- generators/
|   |   `-- data_generator.py        Gera dados ficticios bancarios + manifestos YAML
|   |
|   |-- manifest/                    [Sprint 1] Modulo de manifesto
|   |   |-- extractor_base.py        Interface ABC + deteccao regulatoria por heuristica
|   |   |-- extractor_sas7bdat.py    Extrator de metadados SAS7BDAT (CLI + Python)
|   |   |-- manifest_writer.py       Serializa dict para YAML com protecao VALIDATED
|   |   `-- manifest_validator.py    Promocao DRAFT -> VALIDATED (HITL)
|   |
|   |-- storage/
|   |   `-- storage.py               Abstracao medallion: LocalStorage | MinIOStorage
|   |
|   |-- validation/
|   |   |-- contracts.py             Modelos de contrato (base + estendido)
|   |   `-- validator.py             Validacao de schema, nulos, duplicatas e DLQ
|   |
|   |-- profiler/
|   |   `-- duckdb_profiler.py       Profiling estatistico (DuckDB / Pandas fallback)
|   |
|   |-- slm/
|   |   `-- ollama_enrichment.py     Documentacao semantica via Ollama
|   |
|   `-- metrics/
|       `-- metrics_collector.py     Coleta metricas + gera pipeline_report.md
|
|-- tests/
|   |-- run_tests.py                 Runner (sem dependencias externas)
|   |-- test_contracts.py            Testes: contracts.py
|   |-- test_manifest.py             Testes: modulo manifest
|   |-- test_storage.py              Testes: storage + integracao validator
|   `-- test_validator.py            Testes: validator.py
|
`-- data/
    |-- landing/                     Bronze  - CSVs aguardando processamento
    |-- processed/                   Silver  - arquivos validados e promovidos
    |-- gold/                        Gold    - metricas agregadas (futuro)
    |-- quarantine/                  DLQ     - breaking changes isolados
    |-- contracts/                   Manifestos YAML por tabela e cenario
    |-- metrics/                     JSON de metricas por run
    `-- reports/
        |-- pipeline_report.md       Relatorio consolidado da run
        |-- *_documentation.md       Documentacao gerada pelo SLM (DRAFT)
        `-- *_draft.yaml             Rascunho de manifesto quando VALIDATED ja existe
```

---

## Stack

| Componente | Ferramenta | Papel |
|---|---|---|
| Storage abstrato | `src/storage/storage.py` | Medallion - LocalStorage ou MinIOStorage |
| Manifesto | `src/manifest/` | Extracao, escrita e promocao HITL |
| Validacao / DLQ | `src/validation/` | Contratos YAML, schema evolution, quarentena |
| Profiler | DuckDB (preferencial) / Pandas (fallback) | Estatisticas por coluna |
| SLM | Ollama (local) | Documentacao semantica como Data Steward |
| Orquestracao | Prefect 2.x (ou execucao direta) | DAG com 6 jobs mapeados ao Control-M |
| Object Storage | MinIO via Docker (opcional) | Simula ADLS Gen2 / S3 |

---

## Pre-requisitos

```
Python >= 3.11
ollama   (opcional - sem ele, SLM e ignorado com fallback)
docker   (opcional - apenas para MinIO)
```

---

## Instalacao

```bash
# 1. Entre na pasta do projeto
cd data-masters

# 2. Instale as dependencias
pip install -r requirements.txt

# 3. (Opcional) Instale e inicie o Ollama
#    Download: https://ollama.com/download
ollama serve           # em um terminal separado
ollama pull phi3.5     # modelo recomendado para CPU
```

---

## Configuracao - config.py

| Parametro | Padrao | Descricao |
|---|---|---|
| `OLLAMA_MODEL` | `qwen2.5-coder:7b` | Troque por `phi3.5` para melhor documentacao |
| `SKIP_SLM` | `False` | `True` desativa o SLM sem quebrar o pipeline |
| `USE_MINIO` | `False` | `True` ativa o backend MinIO (requer Docker) |
| `NULL_TOLERANCE_PCT` | `30.0` | % de nulos acima do qual o SLM reporta anomalia |

---

## Execucao direta (sem Prefect)

```bash
# Todos os cenarios em sequencia
python run_pipeline.py

# Cenario individual
python run_pipeline.py --scenario baseline
python run_pipeline.py --scenario non_breaking
python run_pipeline.py --scenario breaking
```

---

## Execucao com Prefect

O Prefect oferece UI local, historico de runs e observabilidade por task.
Requer tres terminais abertos simultaneamente.

### Passo 1 - Variavel de ambiente (uma vez por sessao)

```bash
set PREFECT_API_URL=http://127.0.0.1:4200/api
```

Para fixar permanentemente (recomendado):

```bash
setx PREFECT_API_URL "http://127.0.0.1:4200/api"
# Feche e reabra o terminal apos o setx
```

### Passo 2 - Terminal 1: servidor Prefect

```bash
prefect server start
# Aguarde aparecer: Prefect UI available at http://127.0.0.1:4200
```

### Passo 3 - Terminal 2: setup (apenas na primeira vez)

```bash
set PREFECT_API_URL=http://127.0.0.1:4200/api
python setup_prefect.py
```

Isso cria o work pool e registra todos os deployments. Saida esperada:

```
-- 1. Criando work pool local --
-- 2. Registrando deployments --
Successfully created/updated all deployments!
  baseline-manual        deployed
  non-breaking-watch     deployed
  breaking-watch         deployed
  scheduled-daily        deployed
  all-manual             deployed
```

### Passo 4 - Terminal 3: worker

```bash
set PREFECT_API_URL=http://127.0.0.1:4200/api
prefect worker start --pool data-masters-local
```

### Passo 5 - Disparar runs (Terminal 2 ou novo terminal)

```bash
set PREFECT_API_URL=http://127.0.0.1:4200/api

prefect deployment run 'data-masters-pipeline/baseline-manual'
prefect deployment run 'data-masters-pipeline/non-breaking-watch'
prefect deployment run 'data-masters-pipeline/breaking-watch'
```

Acompanhe em tempo real: http://127.0.0.1:4200

---

## Ativar MinIO (quando Docker estiver disponivel)

```bash
# 1. Suba o MinIO
docker compose up -d
# Console: http://localhost:9001  (usuario: minioadmin / senha: minioadmin)

# 2. Instale o client Python
pip install minio

# 3. Ative em config.py
USE_MINIO = True

# 4. Execute normalmente
python run_pipeline.py --scenario baseline
```

Para desativar, volte `USE_MINIO = False`. O pipeline usa disco local imediatamente.

---

## Cenarios de teste

| Cenario | O que simula | Resultado esperado |
|---|---|---|
| `baseline` | Fluxo feliz com anomalias controladas | tb_clientes PASS, tb_transacoes WARNING (duplicatas), tb_contratos PASS |
| `non_breaking` | Nova coluna anulavel adicionada pelo legado | WARNING - pipeline avanca, coluna registrada |
| `breaking` | Coluna obrigatoria removida da exportacao SAS | tb_clientes DLQ - arquivo isolado em `data/quarantine/` |

---

## Arquitetura medallion - fluxo de dados

```
[data_generator]  ->  BRONZE (data/landing/)
                            |
                    [validator] -- breaking? --> QUARANTINE (data/quarantine/)
                            |
                    [profiler]  -->  BRONZE promovido para SILVER (data/processed/)
                            |
                    [SLM/Ollama] --> REPORTS (*_documentation.md)
                            |
                    [metrics]   --> METRICS (*.json)
                            |
                    [report]    --> REPORTS/pipeline_report.md
```

---

## O Manifesto de Dados

O manifesto YAML e o componente central do projeto. E o principal insumo
para a SLM gerar documentacao e para o Devin consultar o contexto das tabelas.

### Estrutura do manifesto estendido

```yaml
table          : tb_clientes
version        : 1.0.0
manifest_status: DRAFT           # DRAFT | VALIDATED

source:
  system        : CORE_BANCARIO_TOTVS
  format        : sas7bdat        # csv|fixed_width|sas7bdat|json|xlsx|xml|parquet
  encoding      : latin-1
  os            : unix            # windows|unix|mainframe
  update_frequency: daily
  contact       : squad@banco.com.br

regulatory:
  tags              : [LGPD, SCR, BACEN_4658]
  data_classification: confidential
  retention_years   : 10

steward:
  name : Joao Silva
  email: joao.silva@banco.com.br

business_context: >
  Tabela mestre de clientes utilizada por todos os produtos de credito.
  Segmentacao determina o produto ofertado e o gestor responsavel.

tolerance:
  max_null_pct    : 25
  allow_duplicates: false

dependencies:
  - tb_agencias
  - tb_segmentos

sample_queries:
  - description: "Distribuicao por segmento"
    sql: "SELECT cd_segmento, COUNT(*) FROM tb_clientes GROUP BY cd_segmento"

schema:
  - name       : cd_cliente
    type       : string
    nullable   : false
    primary_key: true
    description: Codigo unico do cliente no sistema legado.
    sas_label  : "CODIGO CLIENTE"
    regulatory_flags: []
    business_rules  : []

  - name       : nr_cpf_cnpj
    type       : string
    nullable   : false
    description: CPF ou CNPJ sem mascara. Campo sensivel LGPD.
    regulatory_flags: [LGPD_SENSITIVE]
```

### Extrator SAS7BDAT

Arquivos `.sas7bdat` carregam metadados internos (nome, label, formato).
O extrator gera o rascunho do manifesto automaticamente:

```bash
# Extracao basica
python -m src.manifest.extractor_sas7bdat \
    --file data/landing/tb_clientes.sas7bdat \
    --table tb_clientes \
    --output data/contracts/tb_clientes.yaml

# Com enriquecimento SLM (requer ollama serve)
python -m src.manifest.extractor_sas7bdat \
    --file data/landing/tb_clientes.sas7bdat \
    --table tb_clientes \
    --output data/contracts/tb_clientes.yaml \
    --enrich

# Sobrescrever rascunho existente
python -m src.manifest.extractor_sas7bdat ... --overwrite
```

O extrator nunca sobrescreve um manifesto com status VALIDATED.
Se o destino ja e VALIDATED, cria um arquivo `_draft.yaml` paralelo.
Esse comportamento de protecao e o mesmo para todos os extratores abaixo.

### Extrator CSV

Infere o schema lendo uma amostra do arquivo (`--sample`, padrao 500 linhas).
Detecta automaticamente encoding (`chardet`) e delimitador (`csv.Sniffer`).

```bash
python -m src.manifest.extractor_csv \
    --file   data/landing/tb_cobranca.csv \
    --table  tb_cobranca \
    --output data/contracts/tb_cobranca.yaml \
    --sample 500 \
    --enrich
```

Hierarquia de inferencia de tipo: `date` -> `integer` -> `float` -> `boolean`
-> `string`. Colunas com prefixo `id_`/`cd_`/`nr_` e 100% unicas na amostra
sao marcadas como `primary_key`. Sem header (primeira linha 100% numerica),
gera nomes `col_001`, `col_002`...

### Extrator Fixed-Width (posicional)

Arquivos posicionais nao tem delimitador — exigem um leiaute externo.
Por convencao, o extrator busca `data/layouts/<table>_layout.{txt,csv,xlsx}`.

```bash
# Modo A — com leiaute (recomendado)
python -m src.manifest.extractor_fixed \
    --file   data/landing/tb_posicional.txt \
    --layout data/layouts/tb_posicional_layout.txt \
    --table  tb_posicional \
    --output data/contracts/tb_posicional.yaml

# Modo B — inferencia experimental (sem leiaute)
python -m src.manifest.extractor_fixed \
    --file   data/landing/tb_posicional.txt \
    --table  tb_posicional \
    --output data/contracts/tb_posicional.yaml \
    --infer
```

Formatos de leiaute aceitos (TXT, CSV ou XLSX), colunas: `campo`, `inicio`,
`fim`, `tipo`, `descricao` (opcional). O extrator valida sobreposicoes e
lacunas entre campos. O modo `--infer` marca o manifesto como
`DRAFT_EXPERIMENTAL` — requer revisao obrigatoria do Data Steward.

### Extrator JSON

Normaliza estruturas aninhadas via `pandas.json_normalize`. Campos alem de
`--max-level` sao colapsados em string com aviso no `business_rules`.

```bash
python -m src.manifest.extractor_json \
    --file      data/landing/tb_clientes.json \
    --table     tb_clientes \
    --output    data/contracts/tb_clientes.yaml \
    --root-key  data \
    --max-level 2 \
    --enrich
```

Suporta `.json` (objeto unico ou lista), `.jsonl`/`.ndjson` (um objeto por
linha). Se `--root-key` nao for informado, detecta automaticamente a primeira
chave do JSON que contem uma lista. Campos aninhados ficam com notacao
`pai__filho` (ex: `endereco__cidade`).

### Normalizacao de encoding (pre-processamento)

Antes de qualquer extrator, o `normalizer.py` garante UTF-8 + LF:

```python
from src.ingestion.normalizer import normalize
result = normalize(Path("data/landing/tb_cobranca.csv"))
# {"status": "ok", "original_encoding": "latin-1",
#  "line_endings": "CRLF->LF", "bom_removed": False, ...}
```

Trata `latin-1`, `cp1252`, `iso-8859-1`, BOM e CRLF/CR automaticamente.
Para `EBCDIC`, apenas detecta e avisa — nao converte (o middleware de
transferencia normalmente ja faz essa conversao). O arquivo original e
preservado em `data/landing/_originals/` antes de qualquer alteracao.

### Fluxo HITL do manifesto

```
Arquivo SAS7BDAT chega na landing
              |
    extractor_sas7bdat.py
    (metadados + SLM opcional)
              |
    manifest_status: DRAFT
    Campos nao inferidos marcados com "# TODO"
              |
    Data Steward preenche os TODOs
              |
    python -m src.manifest.manifest_validator \
        --file contracts/tb_clientes.yaml \
        --steward "Nome Steward"
              |
    manifest_status: VALIDATED
              |
    Pipeline usa o manifesto sem warning
    SLM gera documentacao enriquecida
    Devin consome via RAG
```

### Verificar pendencias sem promover

```bash
python -m src.manifest.manifest_validator \
    --file data/contracts/tb_clientes.yaml \
    --check-only
```

### Campos detectados automaticamente pelo extrator

| Campo | Automatico? | Como |
|---|---|---|
| `schema[].name` | Sim | Normalizado do nome SAS (snake_case) |
| `schema[].type` | Sim | Mapeamento de formato SAS |
| `schema[].sas_label` | Sim | Label original do SAS7BDAT |
| `schema[].regulatory_flags` | Sim (heuristica) | Padroes no nome/label da coluna |
| `regulatory.tags` | Sim (heuristica) | Agregado das colunas |
| `business_context` | Sim (SLM, flag --enrich) | Gerado pelo Ollama |
| `sample_queries` | Sim (SLM, flag --enrich) | Gerado pelo Ollama |
| `source.*` | Nao - manual | Depende do sistema de origem |
| `steward.*` | Nao - manual | Depende da estrutura organizacional |

---

## Mapeamento Control-M

| Prefect Task | Job Control-M | Exit codes |
|---|---|---|
| `task_generate_data` | JOB-DM-001-GENERATE | 0=OK, 2=ERROR |
| `task_validate` | JOB-DM-002-VALIDATE | 0=PASS, 1=WARNING, 2=DLQ |
| `task_profile` | JOB-DM-003-PROFILE | 0=OK, 2=ERROR |
| `task_enrich_slm` | JOB-DM-004-ENRICH | 0=OK, 1=SKIPPED, 2=ERROR |
| `task_collect_metrics` | JOB-DM-005-METRICS | 0=OK |
| `task_report` | JOB-DM-006-REPORT | 0=OK |

Modo compativel com Control-M (sem Prefect):

```bash
python prefect_flow.py --no-prefect --scenario baseline --run-id %%JOBRUNID%%
```

---

## Dashboard de metricas

```bash
# Resumo geral do ultimo run
python show_metrics.py

# Historico completo de todos os runs
python show_metrics.py --all

# Apenas registros com problemas (DLQ e WARNING)
python show_metrics.py --issues

# Status do enriquecimento SLM por tabela
python show_metrics.py --slm

# Exportar para CSV (analise no Excel)
python show_metrics.py --csv data/metricas_export.csv

# Filtrar por tabela ou cenario
python show_metrics.py --table tb_clientes --all
```

Via Makefile: `make metrics`, `make issues`, `make slm`, `make export`

---

## Testes unitarios

65 testes cobrindo contracts, validator, storage, extractor_base,
manifest_writer, manifest_validator e integracao storage+validator.
Usa unittest nativo do Python — sem dependencias externas.

```bash
# Todos os testes
python tests/run_tests.py

# Verbose
python tests/run_tests.py -v

# Modulo especifico
python tests/run_tests.py test_storage
python tests/run_tests.py test_manifest
python tests/run_tests.py test_contracts
python tests/run_tests.py test_validator
```

---

## Documentacao adicional

| Arquivo | Conteudo |
|---|---|
| `MIGRATION_PLAN.md` | Plano completo Azure + Databricks + Control-M |
| `MANIFEST_ARCHITECTURE.md` | Decisoes de arquitetura do manifesto estendido (Sprint 1) |
| `SPRINT2_SPECS.md` | Especificacoes tecnicas da Sprint 2 (multi-formato + encoding) |
| `HANDOFF.md` | Contexto de retomada para LLM: bugs corrigidos, fixes aplicados, checklist |
| `context.md` | Historico de desenvolvimento, estado atual e proximos passos |
