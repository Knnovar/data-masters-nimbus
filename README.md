# Projeto Nimbus

Pipeline de dados bancaria com arquitetura medallion, contratos de dados
extensiveis e documentacao semantica gerada por IA local — construido para
resolver uma dor concreta: a distancia entre o time de negocio e o time
tecnico na hora de entender o que um dado significa.

---

## 1. Por que este projeto existe

Com LLMs acelerando a velocidade de escrita de codigo, o gargalo deixou de
ser "quao rapido eu codifico" e passou a ser **"quao bem eu entendo o dado
antes de codificar"**. Times tecnicos seguem implementando sobre tabelas
sem contexto de negocio suficiente, e times de negocio nao conseguem validar
o que foi construido porque a documentacao, quando existe, fica desatualizada
ou tecnica demais para quem nao programa.

O **Projeto Nimbus** resolve isso com tres pecas que se conectam:

**Manifest** — um contrato de dados YAML versionado que descreve nao so o
schema tecnico (nome, tipo, nulidade), mas o contexto de negocio, tags
regulatorias (LGPD, SCR), dependencias e exemplos de uso. Ver
[docs/MANIFEST.md](docs/MANIFEST.md).

**SLM (Small Language Model local)** — um modelo de IA rodando localmente
via Ollama que le o Manifest e as estatisticas reais dos dados, e gera
documentacao legivel tanto por analistas de negocio quanto por agentes de
codificacao como o Devin. A SLM nunca inventa — ela parte do que ja foi
declarado pelo Data Steward e expande. Ver [docs/SLM.md](docs/SLM.md).

**Data Steward** — o elo humano do processo. Toda documentacao gerada por
IA nasce com status `DRAFT` e so vira fonte de verdade confiavel (`VALIDATED`)
depois que uma pessoa revisa. Isso elimina o risco de "alucinacao" virar
contrato de producao, mantendo a velocidade que a IA proporciona.

```
Dado bruto -> Extrator gera Manifest DRAFT -> Data Steward valida -> VALIDATED
                                                                       |
                                                    SLM documenta com seguranca
                                                                       |
                                                    Devin codifica com contexto real
```

---

## 2. Estrutura do Projeto

### 2.1 Arvore de pastas

```
nimbus/
|-- README.md                 Este arquivo
|-- tasks.py                  Runner cross-platform (Windows/Mac/Linux)
|-- Makefile                  Atalhos via `make` (Mac/Linux/WSL)
|-- config.py                 Configuracao central
|-- run_pipeline.py           Execucao direta do pipeline
|-- prefect_flow.py           Orquestracao via Prefect (mapeado para Control-M)
|-- show_metrics.py           Dashboard de metricas no terminal
|-- requirements.txt
|
|-- docs/                     Documentacao completa do projeto
|   |-- ARCHITECTURE.md       Arquitetura tecnica detalhada
|   |-- MANIFEST.md           Estrutura do contrato + papel do Data Steward
|   |-- SLM.md                Como a IA se encaixa no fluxo
|   |-- TESTING.md            Testes, cobertura, criterios de aceite
|   |-- CHANGELOG.md          Historico de evolucao (Sprints 1 e 2)
|   |-- NEXT_STEPS.md         Pendencias e planejamento (vivo, atualizado por sessao)
|   `-- MIGRATION_PLAN.md     Plano de migracao para Azure Databricks
|
|-- src/
|   |-- generators/           Dados ficticios + writers multi-formato (CSV/JSON/Fixed)
|   |-- ingestion/            Normalizacao de encoding
|   |-- manifest/             Extratores de manifest + validacao HITL
|   |-- storage/              Abstracao medallion (Local | MinIO)
|   |-- validation/           Contratos de dados + schema evolution
|   |-- profiler/             Profiling estatistico (DuckDB)
|   |-- slm/                  Integracao com Ollama
|   `-- metrics/              Coleta de metricas e relatorios
|
|-- tests/                    148 testes unitarios (unittest nativo)
`-- data/                     Camadas medallion (landing, processed, contracts...)
```

### 2.2 Desenho da Arquitetura

```
Arquivo bruto (CSV / JSON / Fixed-Width / SAS7BDAT)
        |
        v
  Normaliza encoding (UTF-8, LF)
        |
        v
   +---------+
   | BRONZE  |  dado bruto recebido
   +---------+
        |
        v
   Validacao de contrato ---- breaking change ---> QUARENTENA (DLQ)
        | ok
        v
   Profiling (DuckDB)
        |
        v
   +---------+
   | SILVER  |  dado validado
   +---------+
        |
        v
   SLM documenta (le o Manifest + estatisticas)
        |
        v
   Metricas + Relatorio consolidado
```

Detalhamento completo de cada camada: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## 3. Manual Rapido

### Pre-requisitos

```
Python >= 3.11
ollama   (opcional — sem ele, a documentacao fica pendente, pipeline nao trava)
docker   (opcional — apenas para o backend MinIO)
```

### Instalacao

```bash
pip install -r requirements.txt
```

### Executar o pipeline (3 comandos)

```bash
# 1. Roda o cenario padrao
python tasks.py baseline

# 2. Veja o resultado
python tasks.py metrics

# 3. (Opcional) Teste o cenario de quebra de contrato
python tasks.py breaking
```

> **Windows:** use sempre `python tasks.py <comando>` — funciona nativamente,
> sem precisar instalar `make`. A tabela completa de comandos esta em
> `python tasks.py help`.

### Comandos mais usados

| Comando | O que faz |
|---|---|
| `python tasks.py baseline` | Roda o pipeline com dados de exemplo validos |
| `python tasks.py breaking` | Simula uma quebra de contrato (testa DLQ) |
| `python tasks.py metrics` | Mostra o resultado da ultima execucao |
| `python tasks.py issues` | Lista apenas o que deu problema |
| `python tasks.py test` | Roda os 148 testes unitarios |
| `python tasks.py check-manifest --file <path>` | Verifica pendencias de um manifest |
| `python tasks.py validate-manifest --file <path> --steward "Nome"` | Promove DRAFT -> VALIDATED |
| `python tasks.py help` | Lista todos os comandos disponiveis |

### Ativar a SLM (opcional)

```bash
ollama serve              # em um terminal separado
ollama pull phi3.5        # modelo recomendado para CPU
```

Sem isso, o pipeline roda normalmente — a documentacao semantica fica
marcada como `SKIPPED` ate o Ollama estar disponivel.

### Ativar MinIO (opcional, requer Docker)

```bash
docker compose up -d
# Em config.py: USE_MINIO = True
```

---

## 4. Onde encontrar mais

| Preciso entender... | Va para |
|---|---|
| A arquitetura tecnica completa (camadas, storage, orquestracao) | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| Como o Manifest funciona e o papel do Data Steward | [docs/MANIFEST.md](docs/MANIFEST.md) |
| Como a IA (SLM) se encaixa e por que ela nao "inventa" | [docs/SLM.md](docs/SLM.md) |
| Quais testes existem e o que eles garantem | [docs/TESTING.md](docs/TESTING.md) |
| A evolucao do projeto ate aqui | [docs/CHANGELOG.md](docs/CHANGELOG.md) |
| O que esta pendente e planejado agora | [docs/NEXT_STEPS.md](docs/NEXT_STEPS.md) |
| O plano de migracao para Azure Databricks | [docs/MIGRATION_PLAN.md](docs/MIGRATION_PLAN.md) |
