# Plano de Migração: PoC Local → Databricks + Control-M

---

## Parte 1 — Migração do Prefect para o Control-M

### Por que a transição é simples

O `prefect_flow.py` foi construído com portabilidade explícita em mente.
Cada `@task` já tem um nome de job Control-M mapeado e o processo emite logs
no formato `JOBNAME|STEP|STATUS|MSG`, que é o padrão de parsing do Control-M.

O fluxo de migração é puramente operacional — **não exige mudança de código**.

### Passo a passo

**1. Criar os jobs no Control-M**

Cada task do Prefect vira um job independente no Control-M, ligados por
condições `ON_DO`:

```
JOB-DM-001-GENERATE
  ON ENDED_OK  → lança JOB-DM-002-VALIDATE (para cada tabela, em paralelo)
  ON ENDED_NOTOK → alerta + encerra o grupo

JOB-DM-002-VALIDATE (3 instâncias, uma por tabela)
  ON ENDED_OK  → lança JOB-DM-003-PROFILE
  ON exitcode=1 (WARNING) → lança JOB-DM-003-PROFILE mesmo assim
  ON exitcode=2 (DLQ)     → alerta + encaminha para fila de revisão

JOB-DM-003-PROFILE
JOB-DM-004-ENRICH (timeout: 300s — SLM pode ser lento)
JOB-DM-005-METRICS
  → todos com ON ENDED_OK lançando o seguinte

JOB-DM-006-REPORT (wait condition: aguarda TODOS os JOB-DM-005)
```

**2. O comando de cada job no Control-M**

```bash
# Exatamente o mesmo executável da PoC, sem alteração
cd /caminho/do/projeto
python prefect_flow.py --no-prefect --scenario %%SCENARIO%% --run-id %%JOBRUNID%%
```

O parâmetro `--run-id` aceita a variável de job do Control-M diretamente,
mantendo rastreabilidade entre logs do Control-M e os JSONs de métricas.

**3. O que o Control-M precisa interpretar**

O processo já emite para stdout o padrão esperado:
```
[2024-01-15T08:30:01] JOB-DM-002|VALIDATE/tb_clientes|ENDED_OK|status=PASS exit_code=0
```

Configure o parser de log do Control-M para capturar o padrão `ENDED_NOTOK`
como condição de falha — nenhuma mudança no código Python.

---

## Parte 2 — Migração para Databricks

### Visão geral da estratégia

A migração é incremental em 3 fases. Cada fase é independente e pode ser
validada antes de avançar para a próxima. O código local continua funcionando
durante toda a transição.

```
Fase 1: Storage          → MinIO local → ADLS Gen2 / S3
Fase 2: Processamento    → Pandas/DuckDB → PySpark nativo no Databricks
Fase 3: Orquestração     → Prefect local → Databricks Workflows (ou Control-M via REST)
```

---

### Fase 1 — Migração de Storage

**O que muda:** os arquivos CSV deixam de ser gravados em `data/landing/` e
passam a ser gravados diretamente no bucket S3 ou ADLS Gen2 configurado no
Databricks.

**O que NÃO muda:** toda a lógica de validação, profiling e SLM — eles só
precisam receber um `Path` ou URI. A única alteração é no `data_generator.py`
e no início do `validator.py`, onde o `pd.read_csv(path)` passa a aceitar
`pd.read_csv("s3://bucket/path/file.csv")` sem mudança de interface.

**Critério de conclusão:** o pipeline roda localmente lendo e escrevendo
no bucket de staging do Databricks. Métricas produzidas são idênticas às da PoC.

---

### Fase 2 — Migração do Processamento

Esta é a fase de maior esforço técnico. Os três módulos são migrados em ordem
de complexidade crescente.

#### 2a. Validação de Contratos (baixo esforço)

O `validator.py` atual usa pandas e YAML puro. Ele pode rodar **sem alteração**
como um Databricks Notebook Python ou como um job de cluster single-node.

A evolução natural é transformá-lo em uma **Delta Live Tables Expectation**:
cada regra do contrato YAML vira uma `@dlt.expect` ou `@dlt.expect_or_drop`,
e a quarentena vira uma tabela `_quarantine` gerenciada pelo DLT.

#### 2b. Profiler estatístico (médio esforço)

O `duckdb_profiler.py` tem sua lógica migrada para `pyspark.sql.functions`.
O mapeamento é direto:

```
DuckDB/Pandas                   →   PySpark
────────────────────────────────────────────────────────────
COUNT(*) WHERE col IS NULL      →   count(when(col.isNull()))
COUNT(DISTINCT col)             →   approxCountDistinct(col) ou countDistinct
MIN / MAX / AVG                 →   min() / max() / avg()
value_counts().head(5)          →   groupBy(col).count().orderBy(desc).limit(5)
```

O payload de saída do profiler permanece idêntico — o módulo SLM não sabe
se o profiling veio do DuckDB ou do Spark.

#### 2c. SLM / Ollama (alto esforço — decisão arquitetural)

Este é o ponto mais sensível da migração. Existem três caminhos:

**Opção A — Manter Ollama em VM dedicada (recomendado para primeiro go-live)**
Sobe uma VM com GPU (ex: Azure NC-series ou EC2 g4dn) dentro do perímetro
do banco. O `ollama_enrichment.py` aponta para essa VM via `OLLAMA_HOST`.
Zero mudança de código. Custo previsível e controlado.

**Opção B — Databricks Model Serving**
O modelo é empacotado via MLflow e servido como endpoint REST interno no
Databricks. O `ollama_enrichment.py` tem a URL substituída pelo endpoint
do Model Serving. Requer trabalho de MLOps para empacotar o modelo GGUF
no formato MLflow, mas mantém toda a inferência dentro do ambiente do banco.

**Opção C — Azure OpenAI com VNet privada (se compliance aprovar)**
Substitui o Ollama por chamadas ao Azure OpenAI via Private Endpoint.
Nenhum dado sai do tenant Azure do banco. Requer aprovação do comitê de
segurança e análise do DPA — mas elimina o custo de GPU dedicada.

Para a apresentação à diretoria, apresente a Opção A como caminho inicial
e a Opção B como evolução natural após o primeiro ciclo de produção.

---

### Fase 3 — Migração da Orquestração

#### Se o Control-M for o destino final

O Control-M possui integração nativa com Databricks via plugin oficial
(BMC Helix for Databricks). O job Python que hoje roda localmente passa a
ser um **Databricks Job** acionado pelo Control-M via REST API:

```
Control-M Job → POST /api/2.1/jobs/run-now (Databricks Jobs API)
             ← pooling de status via GET /api/2.1/runs/get
             → captura exit code e loga resultado
```

O `--run-id` já injetado pelo Control-M garante rastreabilidade fim a fim
entre o log do Control-M e os metadados gravados no Unity Catalog.

#### Se Databricks Workflows for o destino

Cada `@task` do `prefect_flow.py` vira uma **task** dentro de um Databricks
Workflow multi-task. O DAG de dependências já está documentado no docstring
do `pipeline_flow()` e é reproduzido 1:1 no Workflow. O Control-M passa a
orquestrar apenas o gatilho do Workflow (um único job externo), e o
paralelismo por tabela é gerenciado internamente pelo Databricks.

---

### Unity Catalog — Substituição do ChromaDB

Na PoC, o ChromaDB armazena os embeddings de documentação localmente.
Em produção, o Unity Catalog assume esse papel com duas estruturas:

**Tabela de metadados validados:**
```sql
CREATE TABLE main.data_masters.table_documentation (
  table_name        STRING NOT NULL,
  run_id            STRING NOT NULL,
  scenario          STRING,
  documentation     STRING,   -- markdown gerado pelo SLM
  ai_metadata_status STRING DEFAULT 'DRAFT',
  validated_by      STRING,   -- Data Steward que promoveu para VALIDATED
  validated_at      TIMESTAMP,
  quality_score     DOUBLE,
  created_at        TIMESTAMP DEFAULT current_timestamp()
)
USING DELTA
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true');
```

O Change Data Feed do Delta permite que qualquer consumidor (incluindo o
Devin via RAG) receba notificações quando um registro muda de `DRAFT` para
`VALIDATED` — sem polling.

**Política HITL no Unity Catalog:**
- Registros com `ai_metadata_status = 'DRAFT'` há mais de 5 dias úteis
  disparam alerta automático para o Data Steward owner da tabela.
- O Devin/agente consumidor consulta apenas registros `VALIDATED`.
  Registros `DRAFT` são retornados com aviso explícito na resposta.

---

### Checklist de Pré-requisitos para Iniciar a Migração

Antes de começar qualquer fase, estes itens precisam estar resolvidos:

- [ ] Definir o workspace Databricks de destino (dev/homolog/prod)
- [ ] Confirmar o storage backend (ADLS Gen2 ou S3 — depende do cloud do banco)
- [ ] Obter aprovação do comitê de segurança para o modelo SLM (Opção A, B ou C)
- [ ] Mapear o cluster de Unity Catalog e definir o catálogo/schema de destino
- [ ] Alinhar com o time de Control-M o formato de integração (plugin nativo vs REST)
- [ ] Definir o SLA de validação HITL (ex: 5 dias úteis) e o escalation path
- [ ] Registrar o projeto no catálogo de iniciativas de dados do banco

---

### Estimativa de Esforço por Fase

| Fase | Componente | Esforço estimado | Pré-requisito |
|---|---|---|---|
| 1 | Storage (ADLS/S3) | 1 sprint | Workspace Databricks disponível |
| 2a | Validação → DLT | 1 sprint | Fase 1 concluída |
| 2b | Profiler → PySpark | 1 sprint | Fase 1 concluída |
| 2c | SLM → VM/Model Serving | 2–3 sprints | Aprovação compliance |
| 3 | Orquestração → Control-M | 1 sprint | Fases 2a e 2b concluídas |
| — | Unity Catalog (HITL) | 1 sprint | Fase 3 concluída |

**Total estimado:** 7–9 sprints (assumindo sprints de 2 semanas e time de 2 engenheiros).

O critério de aceite de cada fase é a execução do `python prefect_flow.py --scenario all`
produzindo resultados idênticos aos da PoC local, com os dados lidos e escritos
no ambiente de destino.
