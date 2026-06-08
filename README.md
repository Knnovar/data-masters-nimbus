# Pipeline Data Masters — PoC Local

Pipeline lakehouse bancaria com arquitetura medallion, contratos evolutivos,
profiling estatistico e documentacao semantica via SLM local. Desenvolvida
para validacao de viabilidade antes de apresentacao a diretoria.

---

## Inicio rapido

```bash
pip install -r requirements.txt
python run_pipeline.py
python show_metrics.py
```

---

## Sumario

1. [Estrutura do projeto](#1-estrutura-do-projeto)
2. [Configuracao](#2-configuracao)
3. [Como executar](#3-como-executar)
4. [Makefile — referencia de comandos](#4-makefile--referencia-de-comandos)
5. [Manifesto de dados](#5-manifesto-de-dados)
6. [Dashboard de metricas](#6-dashboard-de-metricas)
7. [Testes unitarios](#7-testes-unitarios)
8. [Informacoes adicionais](#8-informacoes-adicionais)

---

## 1. Estrutura do projeto

```
data-masters/
|
|-- config.py               Configuracao central (modelos, paths, flags)
|-- run_pipeline.py         Entry point direto (sem Prefect)
|-- prefect_flow.py         DAG com 6 tasks mapeadas ao Control-M
|-- prefect.yaml            Deployments do Prefect
|-- setup_prefect.py        Cria work pool e registra deployments
|-- show_metrics.py         Dashboard de metricas no terminal
|-- Makefile                Atalhos de execucao
|-- docker-compose.yml      MinIO local (opcional)
|-- requirements.txt
|
|-- src/
|   |-- generators/         Dados ficticios bancarios + manifestos YAML
|   |-- manifest/           Extracao, escrita e promocao HITL de manifestos
|   |-- storage/            Abstracao medallion: LocalStorage | MinIOStorage
|   |-- validation/         Contratos YAML, schema evolution, DLQ
|   |-- profiler/           Profiling estatistico (DuckDB / Pandas fallback)
|   |-- slm/                Documentacao semantica via Ollama
|   `-- metrics/            Coleta de metricas e relatorios
|
|-- tests/                  65 testes unitarios (unittest puro)
|
`-- data/
    |-- landing/            BRONZE  — dado bruto recebido
    |-- processed/          SILVER  — validado e promovido
    |-- gold/               GOLD    — agregado (futuro)
    |-- quarantine/         DLQ     — breaking changes isolados
    |-- contracts/          Manifestos YAML
    |-- metrics/            JSON por run
    `-- reports/            Documentacao SLM + relatorio consolidado
```

**Stack principal:**

| Componente | Ferramenta |
|---|---|
| Storage | LocalStorage (disco) ou MinIOStorage (S3) |
| Validacao | Pydantic + contratos YAML |
| Profiling | DuckDB (preferencial) / Pandas (fallback) |
| SLM | Ollama local |
| Orquestracao | Prefect 2.x ou execucao direta |
| Object storage | MinIO via Docker (opcional) |

---

## 2. Configuracao

**Pre-requisitos:**

```
Python >= 3.11
ollama    (opcional — SLM ignorado com fallback se ausente)
docker    (opcional — apenas para MinIO)
```

**Instalacao:**

```bash
cd data-masters
pip install -r requirements.txt

# Opcional: Ollama para documentacao semantica
# Download em https://ollama.com/download
ollama serve
ollama pull phi3.5
```

**Parametros em `config.py`:**

| Parametro | Padrao | Descricao |
|---|---|---|
| `OLLAMA_MODEL` | `qwen2.5-coder:7b` | Troque por `phi3.5` para melhor qualidade em CPU |
| `SKIP_SLM` | `False` | `True` desativa SLM sem quebrar o pipeline |
| `USE_MINIO` | `False` | `True` ativa backend MinIO (requer Docker) |
| `NULL_TOLERANCE_PCT` | `30.0` | % de nulos acima do qual o SLM reporta anomalia |

---

## 3. Como executar

### Execucao direta

```bash
python run_pipeline.py                        # todos os cenarios
python run_pipeline.py --scenario baseline
python run_pipeline.py --scenario non_breaking
python run_pipeline.py --scenario breaking
```

### Execucao com Prefect (UI local)

Requer tres terminais. Execute na ordem:

```bash
# Terminal 1 — servidor (mantenha aberto)
prefect server start

# Terminal 2 — setup (apenas na primeira vez)
set PREFECT_API_URL=http://127.0.0.1:4200/api
python setup_prefect.py

# Terminal 3 — worker (mantenha aberto)
set PREFECT_API_URL=http://127.0.0.1:4200/api
prefect worker start --pool data-masters-local

# Disparar uma run (qualquer terminal)
set PREFECT_API_URL=http://127.0.0.1:4200/api
prefect deployment run 'data-masters-pipeline/baseline-manual'
```

UI disponivel em `http://127.0.0.1:4200`

> **Dica Windows:** use `setx PREFECT_API_URL "http://127.0.0.1:4200/api"` para
> fixar a variavel permanentemente e nao precisar repetir o `set` a cada sessao.

### Cenarios de teste

| Cenario | O que simula | Resultado esperado |
|---|---|---|
| `baseline` | Fluxo feliz com anomalias controladas | PASS / WARNING (duplicatas em transacoes) |
| `non_breaking` | Nova coluna anulavel adicionada pelo legado | WARNING — pipeline avanca normalmente |
| `breaking` | Coluna obrigatoria removida da exportacao | DLQ — arquivo isolado em `data/quarantine/` |

### Fluxo medallion

```
[generator] -> BRONZE -> [validator] --(DLQ)--> QUARANTINE
                               |
                          [profiler] -> SILVER
                               |
                          [SLM]     -> REPORTS
                               |
                          [metrics] -> METRICS + pipeline_report.md
```

### MinIO (quando Docker estiver disponivel)

```bash
docker compose up -d          # sobe MinIO
pip install minio             # instala client Python

# config.py
USE_MINIO = True              # ativa o backend

python run_pipeline.py        # pipeline usa MinIO automaticamente
```

Console em `http://localhost:9001` (usuario: `minioadmin` / senha: `minioadmin`)

---

## 4. Makefile — referencia de comandos

O Makefile centraliza os comandos mais usados. Execute `make help` para
ver todos os targets disponíveis.

### Pipeline

```bash
make run             # executa todos os cenarios em sequencia
make baseline        # executa apenas o cenario baseline
make non-breaking    # executa o cenario non_breaking
make breaking        # executa o cenario breaking (testa DLQ)
```

### Dashboard de metricas

```bash
make metrics         # resumo geral do ultimo run de cada tabela
make metrics-all     # historico completo de todos os runs
make issues          # lista apenas registros com DLQ ou WARNING
make slm             # status do enriquecimento SLM por tabela
make export          # exporta metricas para data/metrics_export.csv
```

### Manifesto

```bash
make check-manifest FILE=data/contracts/tb_clientes.yaml
# verifica pendencias (campos TODO) sem alterar o arquivo

make validate-manifest FILE=data/contracts/tb_clientes.yaml STEWARD="Nome Steward"
# promove o manifesto de DRAFT para VALIDATED
```

### Prefect

```bash
make prefect-setup   # cria work pool e registra todos os deployments
make prefect-run     # dispara run baseline via Prefect
```

### Manutencao

```bash
make setup           # instala dependencias (pip install -r requirements.txt)
make clean           # remove __pycache__ e arquivos .pyc
make clean-data      # remove dados gerados em data/ (cuidado!)
make help            # lista todos os targets com descricao
```

### Mapeamento Control-M

Cada task do Prefect corresponde a um job no Control-M:

| Task Prefect | Job Control-M | Exit codes |
|---|---|---|
| `task_generate_data` | JOB-DM-001-GENERATE | 0=OK, 2=ERROR |
| `task_validate` | JOB-DM-002-VALIDATE | 0=PASS, 1=WARNING, 2=DLQ |
| `task_profile` | JOB-DM-003-PROFILE | 0=OK, 2=ERROR |
| `task_enrich_slm` | JOB-DM-004-ENRICH | 0=OK, 1=SKIPPED, 2=ERROR |
| `task_collect_metrics` | JOB-DM-005-METRICS | 0=OK |
| `task_report` | JOB-DM-006-REPORT | 0=OK |

Modo compativel com Control-M (sem servidor Prefect):

```bash
python prefect_flow.py --no-prefect --scenario baseline --run-id %%JOBRUNID%%
```

---

## 5. Manifesto de dados

O manifesto YAML e o componente central do projeto — e o principal insumo
para a SLM e para o Devin. Todo manifesto nasce como `DRAFT` e so e consumido
plenamente apos validacao humana (`VALIDATED`).

### Estrutura

```yaml
table          : tb_clientes
version        : 1.0.0
manifest_status: DRAFT        # DRAFT | VALIDATED

source:
  system        : CORE_BANCARIO_TOTVS
  format        : sas7bdat    # csv | fixed_width | sas7bdat | json | xlsx | parquet
  encoding      : latin-1
  os            : unix
  update_frequency: daily

regulatory:
  tags              : [LGPD, SCR, BACEN_4658]
  data_classification: confidential

steward:
  name : Joao Silva
  email: joao.silva@banco.com.br

business_context: >
  Tabela mestre de clientes. Segmentacao determina produto e gestor.

schema:
  - name       : nr_cpf_cnpj
    type       : string
    nullable   : false
    description: CPF ou CNPJ sem mascara.
    sas_label  : "CPF SEM MASCARA"
    regulatory_flags: [LGPD_SENSITIVE]
    business_rules  : []

sample_queries:
  - description: "Distribuicao por segmento"
    sql: "SELECT cd_segmento, COUNT(*) FROM tb_clientes GROUP BY cd_segmento"
```

### Extrator SAS7BDAT

Gera o rascunho de manifesto automaticamente a partir dos metadados internos
do arquivo — sem precisar carregar os dados em memoria:

```bash
# Extracao basica
python -m src.manifest.extractor_sas7bdat \
    --file   data/landing/tb_clientes.sas7bdat \
    --table  tb_clientes \
    --output data/contracts/tb_clientes.yaml

# Com enriquecimento SLM (requer ollama serve)
python -m src.manifest.extractor_sas7bdat \
    --file   data/landing/tb_clientes.sas7bdat \
    --table  tb_clientes \
    --output data/contracts/tb_clientes.yaml \
    --enrich

# Sobrescrever rascunho existente
python -m src.manifest.extractor_sas7bdat ... --overwrite
```

Campos extraidos automaticamente: `schema[].name`, `schema[].type`,
`schema[].sas_label`, `schema[].regulatory_flags`, `regulatory.tags`.
Campos que exigem preenchimento manual sao marcados com `# TODO`.

### Fluxo HITL

```
SAS7BDAT na landing
       |
  extractor_sas7bdat.py  (+ --enrich para SLM)
       |
  manifest_status: DRAFT  <-- campos TODO aguardam preenchimento
       |
  Data Steward preenche e valida:
  make check-manifest FILE=...
  make validate-manifest FILE=... STEWARD="Nome"
       |
  manifest_status: VALIDATED
       |
  Pipeline sem warnings / SLM enriquecido / Devin via RAG
```

---

## 6. Dashboard de metricas

```bash
python show_metrics.py                              # resumo geral
python show_metrics.py --all                        # historico completo
python show_metrics.py --issues                     # apenas problemas
python show_metrics.py --slm                        # status SLM
python show_metrics.py --csv metricas.csv           # exporta para Excel
python show_metrics.py --table tb_clientes --all    # filtra por tabela
python show_metrics.py --scenario breaking          # filtra por cenario
```

Atalhos via Makefile: `make metrics`, `make issues`, `make slm`, `make export`

---

## 7. Testes unitarios

65 testes com `unittest` nativo — sem dependencias externas:

```bash
python tests/run_tests.py         # todos os testes
python tests/run_tests.py -v      # verbose
python tests/run_tests.py test_storage    # modulo especifico
python tests/run_tests.py test_manifest
python tests/run_tests.py test_contracts
python tests/run_tests.py test_validator
```

Cobertura: `contracts`, `validator`, `storage`, `extractor_base`,
`manifest_writer`, `manifest_validator` e integracao `storage + validator`.

---

## 8. Informacoes adicionais

| Documento | Conteudo |
|---|---|
| `MIGRATION_PLAN.md` | Plano de migracao Azure + Databricks + Control-M (3 fases) |
| `MANIFEST_ARCHITECTURE.md` | Decisoes de arquitetura do manifesto estendido |
| `context.md` | Historico completo de desenvolvimento, estado atual e proximos passos |
