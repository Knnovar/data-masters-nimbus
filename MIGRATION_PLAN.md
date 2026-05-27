# Plano de Migração: PoC Local → Azure + Databricks + Control-M

---

## Visão geral da stack de destino

O banco usa Azure como provedor de cloud. O Databricks roda sobre a Azure
nativamente via **Azure Databricks**, o que elimina fricção de integração —
identidade, rede, storage e governança já compartilham o mesmo plano de controle.

```
┌─────────────────────────────────────────────────────────────┐
│                        AZURE TENANT                         │
│                                                             │
│  ┌─────────────────┐     ┌──────────────────────────────┐  │
│  │   ADLS Gen2     │────▶│     Azure Databricks         │  │
│  │  (Bronze/Silver │     │  ┌─────────┐ ┌────────────┐  │  │
│  │   /Gold/DLQ)    │     │  │   DLT   │ │  Workflows │  │  │
│  └─────────────────┘     │  └─────────┘ └────────────┘  │  │
│                           │  ┌──────────────────────┐    │  │
│  ┌─────────────────┐     │  │   Unity Catalog       │    │  │
│  │  Azure OpenAI   │────▶│  │   + Vector Search     │    │  │
│  │  (Private EP)   │     │  └──────────────────────┘    │  │
│  └─────────────────┘     │  ┌──────────────────────┐    │  │
│                           │  │  Model Serving        │    │  │
│  ┌─────────────────┐     │  │  (MLflow)             │    │  │
│  │  Azure Key Vault│     │  └──────────────────────┘    │  │
│  │  (credenciais)  │     └──────────────────────────────┘  │
│  └─────────────────┘                                        │
│                                                             │
│  ┌─────────────────┐     ┌──────────────────────────────┐  │
│  │   Control-M     │────▶│  Databricks Jobs API         │  │
│  │  (BMC Helix)    │     │  REST /api/2.1/jobs/run-now  │  │
│  └─────────────────┘     └──────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

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
  ON ENDED_OK    → lança JOB-DM-002-VALIDATE (para cada tabela, em paralelo)
  ON ENDED_NOTOK → alerta + encerra o grupo

JOB-DM-002-VALIDATE (3 instâncias, uma por tabela)
  ON ENDED_OK          → lança JOB-DM-003-PROFILE
  ON exitcode=1 (WARNING) → lança JOB-DM-003-PROFILE mesmo assim
  ON exitcode=2 (DLQ)  → alerta + encaminha para fila de revisão

JOB-DM-003-PROFILE
JOB-DM-004-ENRICH (timeout: 300s — SLM pode ser lento)
JOB-DM-005-METRICS
  → todos com ON ENDED_OK lançando o seguinte

JOB-DM-006-REPORT (wait condition: aguarda TODOS os JOB-DM-005)
```

**2. O comando de cada job no Control-M**

```bash
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

## Parte 2 — Migração para Azure + Databricks

### Visão geral da estratégia

A migração é incremental em 4 fases. Cada fase é independente e pode ser
validada antes de avançar para a próxima. O código local continua funcionando
durante toda a transição.

```
Fase 1: Storage       → MinIO local     → ADLS Gen2 (Azure)
Fase 2: Processamento → Pandas/DuckDB   → PySpark + Delta Live Tables
Fase 3: SLM           → Ollama local    → Azure OpenAI / Databricks Model Serving
Fase 4: Orquestração  → Prefect local   → Databricks Workflows + Control-M
```

---

### Fase 1 — Storage: MinIO → ADLS Gen2

O MinIO local foi construído como espelho do ADLS Gen2 — mesma semântica de
buckets, mesma API S3-compatível. A camada de abstração `Storage` (a ser
implementada) é o que torna essa troca transparente para o restante do código.

**Mapeamento de camadas no ADLS Gen2:**

```
PoC Local (MinIO)           →   Azure (ADLS Gen2)
────────────────────────────────────────────────────────
data-masters-landing        →   abfss://bronze@<storage>.dfs.core.windows.net
data-masters-processed      →   abfss://silver@<storage>.dfs.core.windows.net
data-masters-gold           →   abfss://gold@<storage>.dfs.core.windows.net
data-masters-quarantine     →   abfss://quarantine@<storage>.dfs.core.windows.net
```

**Autenticação no Azure:**
O Databricks autentica no ADLS Gen2 via **Service Principal** ou **Managed Identity**
— sem credenciais hardcodadas. As chaves ficam no **Azure Key Vault** e são
injetadas como secrets no Databricks Secrets API.

```python
# Em produção, a classe Storage lê assim:
storage_account = dbutils.secrets.get("kv-data-masters", "storage-account-name")
```

**Critério de conclusão:** o pipeline roda localmente apontando para o ADLS Gen2
de staging. Métricas produzidas são idênticas às da PoC.

---

### Fase 2 — Processamento: Pandas/DuckDB → PySpark + DLT

#### 2a. Validação de Contratos → Delta Live Tables

O `validator.py` atual roda sem alteração como Databricks Notebook Python.
A evolução natural é transformar cada regra do contrato YAML em uma
**DLT Expectation**:

```python
# Contrato YAML vira:
@dlt.expect_or_drop("cd_cliente não nulo", "cd_cliente IS NOT NULL")
@dlt.expect("taxa de nulos vl_renda_mensal", "null_pct < 0.25")
def tb_clientes_silver():
    return dlt.read("tb_clientes_bronze")
```

A quarentena vira a tabela `_quarantine` gerenciada automaticamente pelo DLT.

#### 2b. Profiler → PySpark

Mapeamento direto das funções do `duckdb_profiler.py`:

```
DuckDB/Pandas                   →   PySpark
──────────────────────────────────────────────────────────
COUNT(*) WHERE col IS NULL      →   count(when(col.isNull()))
COUNT(DISTINCT col)             →   approxCountDistinct(col)
MIN / MAX / AVG                 →   min() / max() / avg()
value_counts().head(5)          →   groupBy(col).count().orderBy(desc).limit(5)
```

O payload de saída permanece idêntico — o módulo SLM não sabe se o profiling
veio do DuckDB ou do Spark.

#### 2c. Camada Gold no Delta Lake

A tabela Gold de métricas de qualidade, hoje um CSV local, vira uma tabela
Delta com Change Data Feed habilitado — o que permite ao Devin e ao Unity
Catalog receberem notificações de mudança sem polling:

```sql
CREATE TABLE main.data_masters.quality_metrics
USING DELTA
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true')
AS SELECT * FROM silver.pipeline_metrics;
```

---

### Fase 3 — SLM: Ollama → Azure OpenAI / Databricks Model Serving

Este é o ponto mais sensível da migração por envolver decisão de compliance.
Sendo Azure o provedor, as opções se ordenam da mais simples à mais robusta:

**Opção A — Azure OpenAI com Private Endpoint (recomendado para primeiro go-live)**

É a opção com menor esforço de infraestrutura. O Azure OpenAI é provisionado
dentro do tenant do banco com um Private Endpoint — nenhum dado trafega pela
internet pública, tudo fica dentro da VNet corporativa.

```python
# ollama_enrichment.py: troca de 4 linhas
OLLAMA_HOST  = "https://<resource>.openai.azure.com"
OLLAMA_MODEL = "gpt-4o-mini"   # ou gpt-4o, dependendo do budget
# Header adicional: api-key via Azure Key Vault
```

Vantagem decisiva para o banco: a Microsoft assina DPA específico para
serviços financeiros regulados no Brasil (BACEN/LGPD), e o Azure OpenAI
tem certificações SOC 2, ISO 27001 e PCI-DSS — argumento pronto para
o comitê de segurança.

**Opção B — Databricks Model Serving (MLflow)**

Registra o Phi-3.5 ou Llama 3.1 como modelo MLflow e publica como endpoint
REST interno no Databricks. Inferência 100% dentro do perímetro, sem
dependência de serviço externo.

```python
# Endpoint interno — mesma interface do ollama_enrichment.py
OLLAMA_HOST  = "https://<workspace>.azuredatabricks.net/serving-endpoints"
OLLAMA_MODEL = "llama-3-1-8b-instruct"
```

Requer trabalho de MLOps para empacotar o modelo GGUF no formato MLflow,
mas elimina qualquer custo por token — você paga só pelo compute do cluster.

**Opção C — Azure NC-series VM com Ollama (mínima mudança de código)**

Sobe uma VM com GPU (NC4as T4 v3 ou NC6s v3) dentro da VNet do banco.
O `ollama_enrichment.py` aponta para o IP privado da VM via `OLLAMA_HOST`.
Zero mudança de código. Custo previsível e controlado.

Melhor para: primeiro go-live rápido quando compliance ainda está avaliando
as opções A e B.

**Para a apresentação:** apresente a Opção C como caminho inicial (menor risco,
menor prazo), a Opção A como destino natural (menor custo operacional, maior
suporte regulatório), e a Opção B como evolução futura (soberania total sobre
o modelo após acúmulo de dados de fine-tuning).

---

### Fase 4 — Orquestração: Prefect → Control-M + Databricks Workflows

#### Integração Control-M + Azure Databricks

O Control-M possui integração nativa com Azure Databricks via **BMC Helix
for Databricks**. O job Python que hoje roda localmente passa a ser um
Databricks Job acionado via REST API:

```
Control-M Job
  → POST https://<workspace>.azuredatabricks.net/api/2.1/jobs/run-now
  ← polling via GET /api/2.1/runs/get
  → captura exit code → condições ON_DO
```

O `--run-id` injetado pelo Control-M garante rastreabilidade fim a fim
entre o log do Control-M, os jobs do Databricks e os metadados no Unity Catalog.

#### Identidade e segurança na integração

O Control-M autentica no Databricks via **Service Principal** registrado no
Azure Active Directory (Entra ID). As permissões são gerenciadas pelo Unity
Catalog RBAC — o Service Principal do Control-M tem acesso apenas aos
recursos do `data_masters` schema, sem permissão de escrita em outros catálogos.

---

### Unity Catalog — Documentação e Governança

**Tabela de metadados validados:**

```sql
CREATE TABLE main.data_masters.table_documentation (
  table_name         STRING    NOT NULL,
  run_id             STRING    NOT NULL,
  scenario           STRING,
  documentation      STRING,   -- markdown gerado pelo SLM
  ai_metadata_status STRING    DEFAULT 'DRAFT',
  validated_by       STRING,   -- Data Steward que promoveu para VALIDATED
  validated_at       TIMESTAMP,
  quality_score      DOUBLE,
  created_at         TIMESTAMP DEFAULT current_timestamp()
)
USING DELTA
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true');
```

**Databricks Vector Search** substitui o ChromaDB — embeddings ficam
versionados junto com os dados, com controle de acesso pelo mesmo RBAC
das tabelas Delta. O Devin consulta o Vector Search via API REST interna,
sem sair do perímetro Azure.

**Política HITL:**
- Registros `DRAFT` há mais de 5 dias úteis disparam alerta via
  Azure Logic Apps → email/Teams para o Data Steward owner da tabela.
- O Devin consulta apenas registros `VALIDATED`. Registros `DRAFT`
  são retornados com aviso explícito no contexto RAG.

---

### MLflow Tracing — Auditoria de Outputs SLM

Toda chamada ao modelo em produção é rastreada automaticamente via
**MLflow Tracing**, nativo no Azure Databricks:

```python
import mlflow
with mlflow.start_run():
    mlflow.log_param("model", OLLAMA_MODEL)
    mlflow.log_param("table", table_name)
    mlflow.log_text(prompt, "prompt.txt")
    mlflow.log_text(documentation, "output.txt")
    mlflow.log_metric("inference_ms", elapsed_ms)
```

Isso resolve o requisito de auditoria do comitê de segurança e é um argumento
direto para o BACEN: cada documentação gerada tem rastreabilidade completa
de input, output, modelo usado, versão e timestamp.

---

### Checklist de Pré-requisitos para Iniciar a Migração

**Azure / Infraestrutura:**
- [ ] Subscription Azure com cota para Azure Databricks aprovada
- [ ] ADLS Gen2 provisionado com containers Bronze/Silver/Gold/Quarantine
- [ ] Azure Key Vault configurado para secrets do projeto
- [ ] Service Principal criado para o projeto (Databricks + Storage + Key Vault)
- [ ] VNet e Private Endpoints configurados (ADLS, Azure OpenAI se Opção A)

**Databricks:**
- [ ] Workspace Azure Databricks (dev/homolog/prod) provisionado
- [ ] Unity Catalog habilitado no workspace
- [ ] Catálogo `data_masters` e schema criados
- [ ] Cluster policy definida (tamanho, autoscaling, Spark version)

**Compliance e Segurança:**
- [ ] Aprovação do comitê de segurança para a opção SLM escolhida (A, B ou C)
- [ ] DPA (Data Processing Agreement) assinado se Opção A (Azure OpenAI)
- [ ] LGPD: confirmar que dados fictícios não incluem CPF/CNPJ reais em produção
- [ ] Análise de impacto BACEN Res. 4.658 para inferência de IA em produção

**Operações:**
- [ ] Alinhamento com time Control-M para integração via BMC Helix
- [ ] SLA de validação HITL definido (ex: 5 dias úteis) e escalation path
- [ ] Definir Data Stewards owners por tabela no Unity Catalog
- [ ] Registrar projeto no catálogo de iniciativas de dados do banco

---

### Estimativa de Esforço por Fase

| Fase | Componente | Esforço | Pré-requisito |
|---|---|---|---|
| 1 | Storage → ADLS Gen2 | 1 sprint | Workspace + ADLS provisionados |
| 2a | Validação → DLT | 1 sprint | Fase 1 concluída |
| 2b | Profiler → PySpark | 1 sprint | Fase 1 concluída |
| 2c | Gold layer (Delta) | 1 sprint | Fases 2a e 2b concluídas |
| 3 | SLM → Azure OpenAI / Model Serving | 2–3 sprints | Aprovação compliance |
| 4 | Orquestração → Control-M + Workflows | 1 sprint | Fases 2 e 3 concluídas |
| — | Unity Catalog + Vector Search (HITL) | 1 sprint | Fase 4 concluída |
| — | MLflow Tracing (auditoria) | 0.5 sprint | Fase 3 concluída |

**Total estimado:** 8–10 sprints (sprints de 2 semanas, time de 2 engenheiros).

O critério de aceite de cada fase é a execução do pipeline produzindo
resultados idênticos aos da PoC local, com dados lidos e escritos
no ambiente Azure de destino.

---

### Compatibilidade da estrutura atual com Azure

| Componente PoC | Equivalente Azure | Compatível sem reescrita? |
|---|---|---|
| MinIO (S3 API) | ADLS Gen2 (S3-compatible) | ✅ Sim — mesma API via camada Storage |
| DuckDB / Pandas | PySpark no Databricks | ⚠️ Migração de lógica, interface idêntica |
| Ollama (REST API) | Azure OpenAI / Model Serving | ✅ Sim — só troca URL e header auth |
| ChromaDB | Databricks Vector Search | ⚠️ Migração de embeddings necessária |
| Prefect (decoradores) | Databricks Workflows | ✅ Sim — `--no-prefect` já é o modo produção |
| YAML contracts | Delta Live Tables Expectations | ⚠️ Requer reescrita das regras em Python DLT |
| JSON metrics local | Delta table Gold | ✅ Sim — mesmo schema, destino diferente |
| pipeline_report.md | Unity Catalog lineage | ✅ Complementar — MD continua existindo |


---

## Parte 3 — Arquitetura Medallion e Camada de Abstração Storage

### O que foi implementado na PoC

A PoC agora implementa a arquitetura medallion completa com uma camada de
abstração `Storage` que torna o backend intercambiável sem alteração de código.

```
src/storage/storage.py
├── StorageBase         interface comum (ABC)
├── LocalStorage        backend disco local  (USE_MINIO=False, padrão)
└── MinIOStorage        backend MinIO/S3     (USE_MINIO=True, requer Docker)
```

**Mapeamento de camadas:**

```
Camada       Local (PoC)           MinIO (PoC c/ Docker)    Azure (Produção)
──────────────────────────────────────────────────────────────────────────────
bronze       data/landing/         data-masters-bronze      abfss://bronze@...
silver       data/processed/       data-masters-silver      abfss://silver@...
gold         data/gold/            data-masters-gold        abfss://gold@...
quarantine   data/quarantine/      data-masters-quarantine  abfss://quarantine@...
contracts    data/contracts/       data-masters-contracts   abfss://contracts@...
metrics      data/metrics/         data-masters-metrics     abfss://metrics@...
reports      data/reports/         data-masters-reports     abfss://reports@...
```

**Fluxo de promoção entre camadas (confirmado em produção da PoC):**

```
[JOB-DM-001] Geração   → escreve em BRONZE
[JOB-DM-002] Validação → DLQ  → move para QUARANTINE
                       → PASS/WARNING → permanece em BRONZE
[JOB-DM-003] Profiling → promove BRONZE → SILVER
[JOB-DM-004] SLM       → escreve documentação em REPORTS
[JOB-DM-005] Métricas  → escreve JSON em METRICS (futuro: tabela GOLD)
[JOB-DM-006] Relatório → consolida REPORTS + METRICS
```

### Como ativar o MinIO quando Docker estiver disponível

O Docker é opcional na PoC. Quando seu ambiente suportar virtualização:

```python
# config.py — única linha a alterar
USE_MINIO = True

# Subir o MinIO
docker compose up -d

# Pipeline usa MinIO automaticamente — sem alteração de código
python prefect_flow.py --no-prefect --scenario baseline
```

O backend é selecionado pela factory `get_storage()` em tempo de execução.
A UI do MinIO em `http://localhost:9001` mostrará os buckets sendo populados
em tempo real — útil para demonstração visual na apresentação.

### Migração MinIO → ADLS Gen2 (Azure)

Quando o ambiente Azure estiver disponível, a migração é uma extensão natural
da classe `MinIOStorage`. O ADLS Gen2 expõe API S3-compatível — a mudança
é de configuração, não de código:

**Opção A — Manter o client MinIO apontando para ADLS Gen2:**
```python
# config.py
MINIO_ENDPOINT   = "<storage-account>.blob.core.windows.net"
MINIO_ACCESS_KEY = "<storage-account>"         # via Azure Key Vault
MINIO_SECRET_KEY = "<access-key>"              # via Azure Key Vault
USE_MINIO        = True
```

**Opção B — Adicionar backend `ADLSStorage` estendendo `StorageBase`:**
Cria uma terceira implementação usando o SDK `azure-storage-file-datalake`.
Mais verboso, mas permite usar features exclusivas do ADLS Gen2 como
hierarquia de diretórios, ACLs por diretório e integração com Entra ID.
Recomendado para produção, onde o controle de acesso granular é requisito.

Em ambas as opções, o restante do pipeline — generator, validator, profiler,
SLM, metrics — não tem nenhuma linha alterada.

### Impacto no plano de estimativas

A implementação da camada Storage antecipa parte do trabalho da Fase 1
(Storage → ADLS Gen2). A estimativa original de 1 sprint para essa fase
reduz para aproximadamente **0.5 sprint**, já que:

- A interface `StorageBase` está definida e testada
- O mapeamento Bronze/Silver/Gold/Quarantine está operacional
- O comportamento de promoção entre camadas está implementado e validado
- A única tarefa remanescente é adicionar o backend `ADLSStorage` e
  configurar a autenticação via Service Principal no Azure Key Vault

### Tabela de compatibilidade atualizada

| Componente PoC | Equivalente Azure | Compatível sem reescrita? |
|---|---|---|
| LocalStorage (disco) | ADLSStorage (ADLS Gen2) | ✅ Sim — nova impl. de StorageBase |
| MinIOStorage (S3 API) | ADLS Gen2 (S3-compat.) | ✅ Sim — só troca endpoint/credenciais |
| Promoção Bronze→Silver | Delta Live Tables | ⚠️ DLT gerencia promoção automaticamente |
| Quarantine local | ADLS quarantine layer | ✅ Sim — já mapeado na camada Storage |
| DuckDB / Pandas | PySpark no Databricks | ⚠️ Migração de lógica, interface idêntica |
| Ollama (REST API) | Azure OpenAI / Model Serving | ✅ Sim — só troca URL e header auth |
| ChromaDB | Databricks Vector Search | ⚠️ Migração de embeddings necessária |
| Prefect (decoradores) | Databricks Workflows | ✅ Sim — --no-prefect já é o modo produção |
| YAML contracts | Delta Live Tables Expectations | ⚠️ Requer reescrita das regras em Python DLT |
| JSON metrics local | Delta table Gold | ✅ Sim — mesmo schema, destino diferente |
| pipeline_report.md | Unity Catalog lineage | ✅ Complementar — MD continua existindo |
