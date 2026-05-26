# 🏦 Pipeline Data Masters — PoC Local

Pipeline completa de dados com contratos evolutivos, profiling estatístico e documentação semântica via SLM local.

---

## Stack da PoC

| Componente | Ferramenta | Papel |
|---|---|---|
| Landing Zone | Sistema de arquivos local (ou MinIO) | Recebe CSV + manifesto YAML |
| Validação / DLQ | Python + Pydantic | Contratos, schema evolution, quarentena |
| Profiling | DuckDB | Substitui PySpark localmente |
| SLM Inference | Ollama (local) | Documentação semântica como Data Steward |
| Orquestração | `run_pipeline.py` (ou Prefect) | Substitui Control-M |
| Object Storage | MinIO via Docker (opcional) | Simula S3/buckets do banco |

---

## Pré-requisitos

```bash
python >= 3.11
docker (opcional — apenas para MinIO)
ollama  (opcional — sem ele, SLM é ignorado com graceful fallback)
```

---

## Instalação

```bash
# 1. Clone / copie o projeto
cd data-masters

# 2. Instale dependências
pip install -r requirements.txt

# 3. (Opcional) Suba o MinIO
docker compose up -d
# Console: http://localhost:9001  (usuário: minioadmin / minioadmin)

# 4. (Opcional) Suba o Ollama com o modelo configurado
ollama serve
ollama pull qwen2.5-coder:7b
# Recomendado para documentação de negócio:
# ollama pull phi4   OU   ollama pull llama3.1:8b
```

> **Sem Ollama:** a pipeline roda normalmente. O enriquecimento SLM é ignorado
> e os arquivos de documentação são gerados com stub indicando a ausência.

---

## Execução

```bash
# Roda os 3 cenários em sequência (recomendado para métricas completas)
python run_pipeline.py

# Cenário individual
python run_pipeline.py --scenario baseline
python run_pipeline.py --scenario non_breaking
python run_pipeline.py --scenario breaking
```

---

## Cenários de Teste

### `baseline` — Fluxo feliz
Dados válidos com anomalias controladas (nulos, duplicatas).
Exercita o profiler e o SLM em condições normais.

### `non_breaking` — Evolução de schema permitida
Nova coluna anulável (`cd_gestor_relacionamento`) adicionada à `tb_clientes`.
O pipeline emite `WARNING` mas avança normalmente.
**Equivale a:** time de engenharia do sistema legado adicionou um campo novo sem avisar.

### `breaking` — Breaking change → quarentena
A coluna `cd_cliente` (PK) tem seu tipo alterado de `string` para `integer`.
O arquivo é imediatamente isolado no diretório de quarentena.
**Equivale a:** exportação SAS com configuração incorreta de tipo.

---

## Saídas

```
data/
├── landing/          CSV recebidos aguardando processamento
├── quarantine/       Arquivos com breaking change isolados
├── processed/        Arquivos validados e processados
├── contracts/        Manifestos YAML gerados
├── metrics/          JSON de métricas por tabela e por run
└── reports/
    ├── pipeline_report.md          Relatório consolidado da run
    ├── tb_clientes_documentation.md
    ├── tb_transacoes_documentation.md
    └── tb_contratos_credito_documentation.md
```

---

## Substituindo o Control-M — Prefect (opcional)

O Prefect é a alternativa recomendada para orquestração Python-nativa:

```bash
# Inicia a UI local em http://localhost:4200
prefect server start

# Em outro terminal, registra e executa o flow
prefect deploy  # (requer prefect.yaml — veja documentação Prefect)
```

**Por que Prefect no lugar do Control-M:**
- Python-nativo — zero nova linguagem para o time
- Suporte a triggers por evento (não só schedule)
- UI local gratuita para monitoramento
- Caminho claro para Prefect Cloud em produção
- Retry, alertas e observabilidade out-of-the-box

---

## Configuração (`config.py`)

| Parâmetro | Padrão | Descrição |
|---|---|---|
| `OLLAMA_MODEL` | `qwen2.5-coder:7b` | Troque por `phi4` para melhor documentação de negócio |
| `NULL_TOLERANCE_PCT` | `30.0` | % de nulos acima do qual o SLM relata anomalia |
| `DUPLICATE_TOLERANCE` | `0.02` | 2% de duplicatas toleradas antes de warning |

---

## Arquitetura — Fluxo de dados

```
[CSV + YAML] → Landing Zone
                    │
                    ▼
            Validation Worker (Pydantic)
           ┌────────────────────────────┐
           │  Schema Evolution Check    │
           │  Non-Breaking → WARNING    │
           │  Breaking     → DLQ ──────►  /quarantine/
           └────────────────────────────┘
                    │ (PASS / WARNING)
                    ▼
            DuckDB Profiler
            (min, max, mean, null%, top_values)
                    │
                    ▼
            Ollama SLM (Data Steward)
            → Documentação em Markdown
            → Tag: [AI_METADATA_STATUS: DRAFT]
                    │
                    ▼
            Metrics Collector
            → quality_score, timing, anomalias
                    │
                    ▼
            /reports/pipeline_report.md
```
