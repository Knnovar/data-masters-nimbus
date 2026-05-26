# context.md — Pipeline Data Masters
> Gerado automaticamente em 2026-05-25. Use este arquivo para retomar o desenvolvimento
> em uma nova sessão caso os tokens se esgotem novamente.

---

## 1. Contexto do Projeto

Pipeline completa de dados para PoC local em contexto bancário (banco brasileiro).
O objetivo é validar a viabilidade antes de apresentar para a diretoria, coletando
métricas reais com dados fictícios em um ambiente sem custo.

**Origem:** Arquivo `Projeto-data-masters.xml` fornecido pelo usuário contendo
o planejamento completo do projeto.

---

## 2. Decisões Arquiteturais Tomadas na Conversa

| Componente | Original (XML) | Decisão Final | Motivo |
|---|---|---|---|
| Orquestrador | Control-M | **Prefect** (opcional na PoC) | Control-M é schedule-driven; Prefect é event-driven, Python-nativo e gratuito localmente |
| Vector Store | ChromaDB | **ChromaDB apenas na PoC** | Usuário confirmou: ChromaDB é só para uso local, sem intenção de levar para produção |
| Agente consumidor | Devin | **Devin mantido** | Já contratado junto com Windsurf — reaproveitamento de licença existente |
| Profiler | PySpark | **DuckDB (PoC) → PySpark (produção)** | DuckDB substitui Spark localmente sem custo; migração clara para Databricks |
| SLM | Qwen2.5-Coder | **Qwen2.5-Coder (mantido, com ressalva)** | Recomendado trocar por `phi4` ou `llama3.1:8b` para documentação de negócio |

**Ressalva crítica para apresentação:** O Qwen2.5 é da Alibaba — levantar flag de
compliance com BCB Res. 4.658. Contra-argumento preparado: inferência 100% local,
nenhum dado trafega para fora do perímetro.

---

## 3. Estrutura de Arquivos Criados

```
data-masters/
├── config.py                          ✅ Configuração central (modelos, paths, tolerâncias)
├── run_pipeline.py                    ✅ Entry point — roda os 3 cenários
├── requirements.txt                   ✅ Dependências Python
├── docker-compose.yml                 ✅ MinIO local (opcional)
├── README.md                          ✅ Instruções completas de setup e uso
│
├── src/
│   ├── generators/
│   │   └── data_generator.py          ✅ Gera dados fictícios bancários + manifestos YAML
│   ├── validation/
│   │   ├── contracts.py               ✅ Modelo de contrato de dados (sem Pydantic obrigatório)
│   │   └── validator.py               ✅ Validação + detecção de schema evolution + DLQ
│   ├── profiler/
│   │   └── duckdb_profiler.py         ✅ Profiling estatístico (DuckDB preferencial, Pandas fallback)
│   ├── slm/
│   │   └── ollama_enrichment.py       ✅ Enriquecimento semântico via Ollama + graceful fallback
│   └── metrics/
│       └── metrics_collector.py       ✅ Coleta métricas + gera pipeline_report.md
│
└── data/
    ├── landing/                        CSV recebidos
    ├── quarantine/                     DLQ — arquivos com breaking change
    ├── processed/                      Arquivos validados
    ├── contracts/                      Manifestos YAML (gerados automaticamente)
    ├── metrics/                        JSON por run + summary
    └── reports/
        ├── pipeline_report.md          Relatório consolidado da run
        └── *_documentation.md         Documentação SLM por tabela (DRAFT)
```

---

## 4. Estado Atual de Desenvolvimento

### ✅ Concluído e Testado

| Módulo | Status | Observação |
|---|---|---|
| `data_generator.py` | ✅ Funcionando | Faker opcional (fallback stdlib); gera 3 tabelas + YAMLs |
| `contracts.py` | ✅ Funcionando | Pydantic opcional (fallback dataclasses puras) |
| `validator.py` | ✅ Funcionando | Todos os 3 cenários validados e corretos |
| `duckdb_profiler.py` | ✅ Funcionando | DuckDB preferencial, Pandas fallback automático |
| `ollama_enrichment.py` | ✅ Funcionando | Graceful fallback quando Ollama indisponível |
| `metrics_collector.py` | ✅ Funcionando | Score calculado, JSON e MD gerados |
| `run_pipeline.py` | ✅ Funcionando | Todos os 3 cenários end-to-end |

### Resultados dos Testes (última execução)

| Cenário | Tabela | Status | Score |
|---|---|---|---|
| baseline | tb_clientes | 🟢 PASS | 97.7 |
| baseline | tb_transacoes | 🟡 WARNING | 69.4 |
| baseline | tb_contratos_credito | 🟢 PASS | 100.0 |
| non_breaking | tb_clientes | 🟡 WARNING (nova coluna detectada) | 67.0 |
| non_breaking | tb_transacoes | 🟡 WARNING | 69.6 |
| non_breaking | tb_contratos_credito | 🟢 PASS | 100.0 |
| breaking | tb_clientes | 🔴 DLQ (cd_agencia ausente) | 20.0 |
| breaking | tb_transacoes | 🟡 WARNING | 69.4 |
| breaking | tb_contratos_credito | 🟢 PASS | 100.0 |

**SLM:** SKIPPED em todos (Ollama não disponível no container de geração).
Na máquina do usuário, com `ollama serve` ativo, o SLM entra automaticamente.

---

## 5. O Que Falta Fazer

### 🔴 Pendente — Essencial para entrega

| Item | Arquivo a criar/modificar | Estimativa |
|---|---|---|
| **Empacotar projeto em ZIP** | bash: `zip -r data-masters.zip data-masters/` | ~1 min |
| **Testar `pip install -r requirements.txt`** na máquina do usuário | README | — |

### 🟡 Pendente — Recomendado antes da apresentação

| Item | Descrição | Estimativa de tokens |
|---|---|---|
| **Prefect flow** | Criar `prefect_flow.py` com o pipeline como Prefect flow registrável na UI | ~300 tokens |
| **Dashboard de métricas** | Script `show_metrics.py` que lê os JSONs de `/metrics/` e imprime evolução entre runs | ~400 tokens |
| **Política HITL** | Adicionar campo `steward_deadline_days: 5` no contrato + lógica de escalação no validator | ~200 tokens |
| **Teste com Ollama real** | Usuário roda `ollama pull phi4` e executa — valida o módulo SLM de ponta a ponta | Não consome tokens |

### 🟢 Opcional / Nice to have

| Item | Descrição |
|---|---|
| Exportar métricas para CSV | Para análise no Excel / apresentação |
| `Makefile` com targets `make run`, `make clean` | Conveniência de execução |
| Testes unitários (`pytest`) | Cobertura dos cenários de validação |

---

## 6. Como Retomar o Desenvolvimento

### Se os tokens acabarem novamente, diga ao próximo Claude:

> "Retome o desenvolvimento do projeto data-masters. Leia o context.md em
> `/home/claude/data-masters/context.md` (ou no ZIP entregue ao usuário).
> O projeto está em `~/data-masters/`. Todos os módulos principais estão
> funcionando. O próximo passo é: [escolha um item da seção 5 acima]."

### Comandos para verificar o estado rapidamente:

```bash
cd data-masters
python run_pipeline.py --scenario all   # roda tudo e imprime resumo
ls data/metrics/                         # lista runs anteriores
ls data/reports/                         # lista relatórios gerados
```

---

## 7. Instruções de Setup para o Usuário

```bash
# 1. Descompactar e entrar no projeto
unzip data-masters.zip && cd data-masters

# 2. Instalar dependências
pip install -r requirements.txt

# 3. (Recomendado) Instalar e iniciar Ollama
#    https://ollama.com/download
ollama serve
ollama pull phi4   # recomendado sobre qwen2.5-coder para documentação de negócio

# 4. (Opcional) Subir MinIO
docker compose up -d

# 5. Rodar a pipeline completa
python run_pipeline.py

# 6. Ver os resultados
cat data/reports/pipeline_report.md
cat data/reports/tb_clientes_documentation.md   # documentação gerada pelo SLM
```

---

## 8. Notas Técnicas Importantes

### Compatibilidade de pacotes
- Testado com **pandas 3.0.2** (pandas 2.x usa `StringDtype` — o validador foi adaptado)
- **Pydantic e Faker são opcionais** — o projeto roda sem eles (fallback stdlib/dataclasses)
- **DuckDB é opcional** — profiler faz fallback automático para pandas puro
- **Ollama é opcional** — SLM é ignorado com graceful fallback se indisponível

### Sobre o cenário `breaking`
O cenário simula a remoção da coluna obrigatória `cd_agencia` da exportação SAS.
O validator detecta `Colunas obrigatórias ausentes: ['cd_agencia']` e roteia
o arquivo para `/data/quarantine/` sem processar.

### Score de qualidade
Calculado em `metrics_collector.py`:
- **40 pts** — status de validação (PASS=40, WARNING=25, DLQ=0)
- **30 pts** — taxa de nulos global (30 se nulos=0, decremental)
- **20 pts** — taxa de duplicatas (decremental)
- **10 pts** — schema coverage (sem evolution detectada)

---

## 9. Atualização — Sessão 2026-05-26

### Adicionado nesta sessão

| Arquivo | Descrição |
|---|---|
| `prefect_flow.py` | Flow completo com decoradores Prefect + modo `--no-prefect` para Control-M |
| `MIGRATION_PLAN.md` | Plano de migração em texto: Prefect → Control-M e PoC → Databricks |

### Como retomar se os tokens acabarem

```bash
# Verificar que tudo ainda funciona
cd data-masters
python prefect_flow.py --no-prefect --scenario all

# Próximos passos pendentes (se necessário):
# - Testar com Ollama real: ollama serve && ollama pull phi4
# - Adicionar Prefect server: prefect server start
# - Exportar métricas para CSV para análise Excel
```

### Estado do prefect_flow.py
- Roda sem Prefect instalado (decoradores viram no-ops)
- Cada task tem nome de job Control-M documentado (JOB-DM-001 a 006)
- Log no formato `JOBNAME|STEP|STATUS|MSG` — parseável pelo Control-M
- Aceita `--run-id` externo para injeção do ID de job do Control-M
- Exit code global via `sys.exit()` — 0=OK, 1=WARNING, 2=ERROR
- DAG de dependências documentado no docstring do `pipeline_flow()`
