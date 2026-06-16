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

---

## 10. Atualização — Sessão 2026-05-27

### Adicionado nesta sessão

| Arquivo | Descrição |
|---|---|
| `src/storage/storage.py` | Camada de abstração Storage com LocalStorage e MinIOStorage |
| `src/storage/__init__.py` | Init do módulo |
| `config.py` | Adicionado USE_MINIO, GOLD_DIR e refatoração de paths |
| `src/generators/data_generator.py` | generate_all() agora recebe storage ao invés de paths |
| `src/validation/validator.py` | validate() agora recebe storage + filenames |
| `run_pipeline.py` | run_scenario() usa get_storage() |
| `prefect_flow.py` | Todos os 4 tasks atualizados para usar get_storage() |
| `MIGRATION_PLAN.md` | Parte 3 adicionada — Medallion + Storage |

### Fluxo medallion confirmado em execução

```
BRONZE  → dado bruto gerado pelo data_generator
SILVER  → promovido pelo task_profile após validação PASS/WARNING
QUARANTINE → isolado pelo task_validate em BREAKING CHANGE
REPORTS → documentação SLM por tabela
METRICS → JSON de métricas por run
```

### Próximos passos

- Testar com MinIO quando Docker estiver disponível (USE_MINIO=True)
- Implementar ADLSStorage (Fase 1 da migração Azure) quando workspace disponível
- Adicionar tabela Gold consolidada de métricas no metrics_collector.py
- Refazer o deploy Prefect após as mudanças (python setup_prefect.py)

---

## 11. Atualizacao - Sprint 1 Manifesto Estendido

### Novos arquivos

| Arquivo | Descricao |
|---|---|
| `src/manifest/__init__.py` | Init do modulo |
| `src/manifest/extractor_base.py` | Interface ABC com deteccao regulatoria por heuristica e normalizacao snake_case |
| `src/manifest/extractor_sas7bdat.py` | Extrator de metadados SAS7BDAT via pyreadstat (metadataonly=True). CLI: `python -m src.manifest.extractor_sas7bdat` |
| `src/manifest/manifest_writer.py` | Serializa dict para YAML. Nunca sobrescreve VALIDATED - cria `_draft.yaml` paralelo |
| `src/manifest/manifest_validator.py` | Verifica campos TODO e promove DRAFT -> VALIDATED. CLI: `python -m src.manifest.manifest_validator` |
| `MANIFEST_ARCHITECTURE.md` | Documento de arquitetura da Sprint 1 (referencia permanente) |

### Arquivos modificados

| Arquivo | O que mudou |
|---|---|
| `src/validation/contracts.py` | Reescrito com SourceInfo, RegulatoryInfo, StewardInfo, SampleQuery, LayoutField. Todos opcionais - backward compatible |
| `src/validation/validator.py` | Adiciona warning quando manifest_status = DRAFT |
| `src/slm/ollama_enrichment.py` | Prompt atualizado: respeita business_context e description do manifesto |
| `src/generators/data_generator.py` | Tres contratos agora geram manifestos estendidos com business_context, regulatory_tags, sas_label e sample_queries |
| `requirements.txt` | pyreadstat>=1.2.0 adicionado |
| `README.md` | Reescrito com estrutura de pastas, secao completa do manifesto e fluxo HITL |

### Correcao aplicada em todos os arquivos

Varredura completa de unicode fora do range ASCII em chamadas de print/raise/append.
Emojis, box-drawing characters (=, -, ╔) e em dashes substituidos por
tags textuais ([PASS], [WARN], [DLQ], [WRITE], [MOVE], [PROFILE], [REPORT]).
Afetou: storage.py, duckdb_profiler.py, metrics_collector.py,
manifest_validator.py, run_pipeline.py, prefect_flow.py.

### Estrutura do modulo manifest

```
src/manifest/
|-- __init__.py
|-- extractor_base.py        Interface + deteccao regulatoria heuristica
|-- extractor_sas7bdat.py    SAS7BDAT -> YAML (CLI + Python API)
|-- manifest_writer.py       Serializacao segura para YAML
`-- manifest_validator.py    HITL: DRAFT -> VALIDATED
```

### Campos novos no DataContract

```
manifest_status    DRAFT | VALIDATED
validated_by       quem promoveu
validated_at       quando promoveu
source             SourceInfo (system, format, encoding, os, frequency, contact)
regulatory         RegulatoryInfo (tags, data_classification, retention_years)
steward            StewardInfo (name, email)
business_context   texto livre para SLM e Devin
dependencies       tabelas referenciadas
sample_queries     exemplos de SQL para o Devin
```

Colunas ganharam: description, sas_label, regulatory_flags, business_rules

### Metodos novos em DataContract

```python
contract.is_validated()           # True se manifest_status == VALIDATED
contract.has_extended_metadata()  # True se source/regulatory/steward preenchidos
contract.lgpd_sensitive_columns() # lista de colunas com LGPD_SENSITIVE
```

### Como usar o extrator SAS7BDAT

```bash
# Extracao basica (metadados do arquivo)
python -m src.manifest.extractor_sas7bdat \
    --file data/landing/tb_clientes.sas7bdat \
    --table tb_clientes \
    --output data/contracts/tb_clientes.yaml

# Com enriquecimento SLM
python -m src.manifest.extractor_sas7bdat ... --enrich

# Verificar pendencias sem promover
python -m src.manifest.manifest_validator \
    --file data/contracts/tb_clientes.yaml \
    --check-only

# Promover para VALIDATED
python -m src.manifest.manifest_validator \
    --file data/contracts/tb_clientes.yaml \
    --steward "Nome do Steward"
```

### Proximos passos (Sprint 2)

- extractor_csv.py: inferencia de schema por amostragem
- extractor_fixed.py: arquivos posicionais com layout no manifesto
- extractor_json.py: normalizacao e inferencia de schema JSON
- Modulo de normalizacao de encoding na landing (EBCDIC, CP1252, CRLF/LF)
- Integracao do extrator como task opcional no prefect_flow.py

---

## 12. Atualizacao - Sessao atual

### Arquivos adicionados

| Arquivo | Descricao |
|---|---|
| `show_metrics.py` | Dashboard de metricas no terminal com 4 views: resumo, evolucao, problemas e SLM. Export CSV via --csv |
| `Makefile` | Atalhos de execucao: make run, make metrics, make issues, make slm, make export, make check-manifest, make clean |
| `tests/__init__.py` | Init do modulo de testes |
| `tests/run_tests.py` | Runner unittest sem dependencias externas |
| `tests/test_contracts.py` | 14 testes para contracts.py |
| `tests/test_manifest.py` | 22 testes para extractor_base, manifest_writer e manifest_validator |
| `tests/test_storage.py` | 18 testes para LocalStorage + integracao com validator |
| `tests/test_validator.py` | 11 testes para validator.py com LocalStorage real |

### Arquivos modificados

| Arquivo | O que mudou |
|---|---|
| `prefect_flow.py` | Reescrito completo: sem type hints Python 3.10+ (str \| None), sem unicode em prints, sem emojis, logica limpa por task |
| `run_pipeline.py` | Acentos e unicode removidos de strings de runtime |
| `src/metrics/metrics_collector.py` | Acentos removidos de strings de runtime |
| `README.md` | Estrutura de pastas atualizada com tests/ e show_metrics.py; secoes Dashboard e Testes adicionadas |

### Estado atual dos testes

```
65 testes unitarios - 0 falhas
  test_contracts : 14 testes
  test_manifest  : 22 testes
  test_storage   : 18 testes (inclui integracao com validator)
  test_validator : 11 testes

Executar: python tests/run_tests.py -v
```

### Unicode - auditoria final

Varredura completa executada. Zero ocorrencias de unicode fora do range
ASCII em chamadas de print/raise/append em todos os arquivos .py.
Acentos permitidos apenas em comentarios e docstrings.

### Como retomar em nova sessao

```
1. Verificar estado: python tests/run_tests.py -v
2. Smoke test:       python prefect_flow.py --no-prefect --scenario baseline
3. Dashboard:        python show_metrics.py
4. Proximos passos:  Sprint 2 (ver secao 11 - Proximos passos)
```

---

## 13. Sprint 2 — Multi-formato, Encoding e Integracao Prefect

### Arquivos criados

| Arquivo | Descricao |
|---|---|
| `src/ingestion/__init__.py` | Init do modulo |
| `src/ingestion/normalizer.py` | Pre-processador de encoding: UTF-8, CRLF->LF, BOM, EBCDIC avisa |
| `src/manifest/extractor_csv.py` | Inferencia de schema por amostragem (chardet + csv.Sniffer) |
| `src/manifest/extractor_fixed.py` | Leiaute posicional TXT/CSV/XLSX + modo inferencia experimental |
| `src/manifest/extractor_json.py` | JSON/JSONL com json_normalize, preserva __ como separador de nivel |
| `tests/test_sprint2.py` | 39 testes (todos passando apos fixes) |
| `SPRINT2_SPECS.md` | Especificacoes tecnicas da sprint |
| `HANDOFF.md` | Documento de retomada para LLM |

### Arquivos modificados

| Arquivo | O que mudou |
|---|---|
| `prefect_flow.py` | task_extract_manifest adicionada (JOB-DM-000, opcional) |
| `requirements.txt` | chardet>=5.0.0 e openpyxl>=3.1.0 adicionados |

### Decisoes de negocio registradas

| Decisao | Resolucao |
|---|---|
| Formato padrao de leiaute | Nenhum institucional — suporta TXT, CSV, XLSX |
| Repositorio de leiautes | Local em `data/layouts/` para a PoC |
| EBCDIC | Fora do escopo — detecta e avisa, middleware converte |

### Bugs corrigidos nesta sprint

1. `_detect_line_endings`: CRLF puro detectado como "mixed" — fix: checar LF somente fora dos CRLF
2. `_make_column` em extractor_fixed: nao instanciar ABC diretamente — _norm inline
3. `extractor_json` dupla normalizacao de `__`: usar _norm_part por segmento
4. `_find_collapsed`: dict nao e hashable — fix: str(p) no join
5. `_load_json`: root_key detectado nao era retornado — fix: tupla com 3 elementos
6. `test_deep_nesting_collapsed`: series com dicts quebra nunique() — fix: detectar has_complex antes

### Estado final dos testes

```
104 testes — 104 passando — 0 falhas
python3 tests/run_tests.py -v
```

### Proximos passos (Sprint 3 candidatos)

- Tabela Gold consolidada de metricas no metrics_collector.py
- Interface CLI unificada: `python -m src.manifest.extract --file X --format auto`
- Deteccao automatica de formato pelo extrator (auto-routing)
- Integracao do extrator no Prefect com parametro `auto_extract: true`
