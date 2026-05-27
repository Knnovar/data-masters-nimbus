# Pipeline Data Masters — PoC Local

Pipeline completa de dados com arquitetura medallion (Bronze → Silver → Gold),
contratos evolutivos, profiling estatístico e documentação semântica via SLM local.

---

## Stack

| Componente | Ferramenta | Papel |
|---|---|---|
| Storage abstrato | `src/storage/storage.py` | Medallion — LocalStorage ou MinIO |
| Validação / DLQ | Python + Pydantic | Contratos YAML, schema evolution, quarentena |
| Profiler | DuckDB (preferencial) / Pandas (fallback) | Estatísticas por coluna |
| SLM | Ollama (local) | Documentação semântica como Data Steward |
| Orquestração | Prefect 2.x (ou execução direta) | DAG com 6 jobs mapeados ao Control-M |
| Object Storage | MinIO via Docker (opcional) | Simula ADLS Gen2 / S3 do banco |

---

## Pré-requisitos

```
Python >= 3.11
ollama   (opcional — sem ele, SLM é ignorado com fallback)
docker   (opcional — apenas para MinIO)
```

---

## Instalação

```bash
# 1. Entre na pasta do projeto
cd data-masters

# 2. Instale as dependências Python
pip install -r requirements.txt

# 3. (Opcional) Instale e inicie o Ollama
#    Download: https://ollama.com/download
ollama serve           # em um terminal separado
ollama pull phi3.5     # modelo recomendado para CPU
```

---

## Configuração — config.py

| Parâmetro | Padrão | Descrição |
|---|---|---|
| `OLLAMA_MODEL` | `qwen2.5-coder:7b` | Troque por `phi3.5` para melhor documentação |
| `SKIP_SLM` | `False` | `True` desativa o SLM sem quebrar o pipeline |
| `USE_MINIO` | `False` | `True` ativa o backend MinIO (requer Docker) |
| `NULL_TOLERANCE_PCT` | `30.0` | % de nulos acima do qual o SLM reporta anomalia |

---

## Execução direta (sem Prefect)

```bash
# Todos os cenários em sequência
python run_pipeline.py

# Cenário individual
python run_pipeline.py --scenario baseline
python run_pipeline.py --scenario non_breaking
python run_pipeline.py --scenario breaking
```

---

## Execução com Prefect

O Prefect oferece UI local, histórico de runs e observabilidade por task.
Requer três terminais abertos simultaneamente.

### Passo 1 — Variável de ambiente (uma vez por sessão)

```bash
set PREFECT_API_URL=http://127.0.0.1:4200/api
```

Para fixar permanentemente (recomendado):

```bash
setx PREFECT_API_URL "http://127.0.0.1:4200/api"
# Feche e reabra o terminal após o setx
```

### Passo 2 — Terminal 1: servidor Prefect

```bash
prefect server start
# Aguarde aparecer: Prefect UI available at http://127.0.0.1:4200
```

### Passo 3 — Terminal 2: setup (apenas na primeira vez)

```bash
set PREFECT_API_URL=http://127.0.0.1:4200/api
python setup_prefect.py
```

Isso cria o work pool e registra todos os deployments. Saída esperada:

```
── 1. Criando work pool local ──
── 2. Registrando deployments ──
Successfully created/updated all deployments!
  baseline-manual        deployed
  non-breaking-watch     deployed
  breaking-watch         deployed
  scheduled-daily        deployed
  all-manual             deployed
```

### Passo 4 — Terminal 3: worker

```bash
set PREFECT_API_URL=http://127.0.0.1:4200/api
prefect worker start --pool data-masters-local
```

### Passo 5 — Disparar runs (Terminal 2 ou novo terminal)

```bash
set PREFECT_API_URL=http://127.0.0.1:4200/api

# Cenário baseline
prefect deployment run 'data-masters-pipeline/baseline-manual'

# Cenário non-breaking (schema evolution)
prefect deployment run 'data-masters-pipeline/non-breaking-watch'

# Cenário breaking (DLQ / quarentena)
prefect deployment run 'data-masters-pipeline/breaking-watch'
```

Acompanhe em tempo real: **http://127.0.0.1:4200**

---

## Ativar MinIO (quando Docker estiver disponível)

```bash
# 1. Suba o MinIO
docker compose up -d
# Console: http://localhost:9001  (usuário: minioadmin / senha: minioadmin)

# 2. Instale o client Python
pip install minio

# 3. Ative em config.py
USE_MINIO = True

# 4. Execute normalmente — nenhuma outra mudança necessária
python run_pipeline.py --scenario baseline
```

Para desativar, volte `USE_MINIO = False`. O pipeline usa disco local imediatamente.

---

## Cenários de teste

| Cenário | O que simula | Resultado esperado |
|---|---|---|
| `baseline` | Fluxo feliz — dados válidos com anomalias controladas | tb_clientes PASS, tb_transacoes WARNING (duplicatas), tb_contratos PASS |
| `non_breaking` | Nova coluna anulável adicionada pelo sistema legado | WARNING — pipeline avança, coluna registrada no log |
| `breaking` | Coluna obrigatória removida da exportação SAS | tb_clientes DLQ — arquivo isolado em `data/quarantine/` |

---

## Arquitetura medallion — fluxo de dados

```
[data_generator]  →  BRONZE (data/landing/)
                          │
                  [validator] ──── breaking? ──→  QUARANTINE (data/quarantine/)
                          │
                  [profiler]  →  BRONZE promovido para SILVER (data/processed/)
                          │
                  [SLM/Ollama] →  REPORTS (data/reports/*_documentation.md)
                          │
                  [metrics]   →  METRICS (data/metrics/*.json)
                          │
                  [report]    →  REPORTS/pipeline_report.md
```

---

## Saídas geradas

```
data/
├── landing/          Bronze — CSVs aguardando processamento
├── processed/        Silver — arquivos validados e promovidos
├── gold/             Gold   — reservado para métricas agregadas (futuro)
├── quarantine/       DLQ    — arquivos com breaking change isolados
├── contracts/        Manifestos YAML por tabela e por cenário
├── metrics/          JSON de métricas por tabela por run
└── reports/
    ├── pipeline_report.md              Relatório consolidado da run
    ├── tb_clientes_documentation.md    Documentação gerada pelo SLM
    ├── tb_transacoes_documentation.md
    └── tb_contratos_credito_documentation.md
```

---

## Mapeamento Control-M

Cada task do Prefect corresponde a um job no Control-M:

| Prefect Task | Job Control-M | Exit codes |
|---|---|---|
| `task_generate_data` | JOB-DM-001-GENERATE | 0=OK, 2=ERROR |
| `task_validate` | JOB-DM-002-VALIDATE | 0=PASS, 1=WARNING, 2=DLQ |
| `task_profile` | JOB-DM-003-PROFILE | 0=OK, 2=ERROR |
| `task_enrich_slm` | JOB-DM-004-ENRICH | 0=OK, 1=SKIPPED, 2=ERROR |
| `task_collect_metrics` | JOB-DM-005-METRICS | 0=OK |
| `task_report` | JOB-DM-006-REPORT | 0=OK |

Para rodar sem Prefect (modo compatível com Control-M):

```bash
python prefect_flow.py --no-prefect --scenario baseline --run-id %%JOBRUNID%%
```

---

## Plano de migração

Consulte `MIGRATION_PLAN.md` para o plano completo de migração para
Azure Databricks, incluindo mapeamento de camadas para ADLS Gen2,
opções de SLM em produção e integração com Control-M via BMC Helix.

---

## O Manifesto de Dados

O manifesto YAML é o componente central do projeto — é ele que define o contrato
entre o sistema de origem e o pipeline, e é o principal insumo para a SLM gerar
documentação e para o Devin consultar o contexto das tabelas.

### Estrutura atual

```yaml
table       : tb_clientes
description : Cadastro mestre de clientes pessoa física e jurídica.
owner       : squad-dados-cadastrais
version     : 1.0.0
tolerance   :
  max_null_pct    : 25
  allow_duplicates: false
schema      :
  - name       : cd_cliente
    type       : string
    nullable   : false
    primary_key: true
  - name       : vl_renda_mensal
    type       : float
    nullable   : true
```

### Evolução planejada — campos a adicionar

```yaml
# Contexto de origem
source_format    : csv              # csv | fixed_width | sas7bdat | json | xlsx | xml
source_encoding  : latin-1          # utf-8 | latin-1 | ebcdic | cp1252
source_system    : CORE_BANCARIO    # nome do sistema de origem
source_os        : windows          # windows | unix | mainframe
update_frequency : daily            # daily | weekly | monthly | event_driven

# Contexto de negócio — insumo direto para SLM e Devin
business_context : >
  Tabela mestre de clientes utilizada por todos os produtos de crédito.
  Segmentação baseada em renda e relacionamento determina o produto ofertado.
regulatory_tags  :
  - LGPD
  - SCR
  - BACEN_4658

# Governança
steward          :
  name : João Silva
  email: joao.silva@banco.com.br
dependencies     :
  - tb_agencias
  - tb_segmentos

# Sugestões de uso — consumidas pelo Devin via RAG
sample_queries   :
  - "SELECT cd_segmento, COUNT(*) FROM tb_clientes GROUP BY cd_segmento"
  - "SELECT * FROM tb_clientes WHERE fl_ativo = true AND vl_renda_mensal > 10000"

# Layout posicional — apenas para source_format: fixed_width
layout           :
  - field: cd_cliente    start: 1   end: 12  dtype: string
  - field: nr_cpf_cnpj   start: 13  end: 23  dtype: string
  - field: nm_cliente    start: 24  end: 73  dtype: string
```

### Estratégias de geração automática

**SAS7BDAT → manifesto automático**
Arquivos `.sas7bdat` carregam metadados internos (nome de variável, label, formato).
Um módulo `manifest_extractor.py` lê esses metadados e gera o rascunho YAML
automaticamente — sem preenchimento manual.

**CSV / JSON → inferência por amostragem**
Para formatos sem metadados internos, o pipeline lê as primeiras N linhas,
infere tipos, conta nulos e detecta domínios categóricos, gerando um rascunho
que o Data Steward revisa e valida.

**SLM gerando o manifesto (inversão do fluxo)**
Em vez de usar o manifesto como insumo para a SLM, a SLM recebe as estatísticas
do profiler e gera o rascunho do manifesto — incluindo `business_context` e
`regulatory_tags`. O Data Steward valida a documentação e o contrato juntos.

### Fluxo HITL do manifesto

```
Extrator automático / SLM
        │
        ▼
  [MANIFEST_STATUS: DRAFT]   ← nunca consumido pelo Devin
        │
  Revisão do Data Steward
        │
        ▼
  [MANIFEST_STATUS: VALIDATED] ← liberado para consumo
```

O mesmo mecanismo de governança da documentação se aplica ao manifesto.
O Devin só consome manifestos com status `VALIDATED`.