# Projeto Nimbus

Quando times de dados passam a usar IA para acelerar o desenvolvimento, surge uma tensão nova: o código sai mais rápido, mas o entendimento sobre o dado não acompanha o ritmo. Times técnicos implementam sobre tabelas sem contexto de negócio suficiente. Times de negócio não conseguem validar o que foi entregue porque a documentação, quando existe, descreve colunas mas não explica o que elas representam no mundo real.

O Projeto Nimbus foi construído como resposta direta a essa dor, conectando três peças que no dia a dia ficam separadas: o contrato formal do dado, a inteligência que o documenta e o julgamento humano que valida tudo antes que chegue a produção.

---

## 1. A ideia central

O **Manifest** é um arquivo YAML versionado que vai além do schema técnico. Ele descreve de onde o dado vem, qual regulação se aplica, o que cada coluna significa no contexto do negócio bancário e exemplos concretos de como usar a tabela. É o ponto de partida para tudo o que o pipeline faz.

A **SLM** (Small Language Model) roda localmente via Ollama e, depois que o dado passa pela validação e pelo profiling estatístico, lê o Manifest junto com as estatísticas reais e escreve a documentação técnica da tabela em linguagem de negócio. Ela parte sempre do que já foi declarado no contrato — não especula, não inventa, só expande o que o Data Steward definiu.

O **Data Steward** é quem fecha o ciclo. Toda documentação gerada por IA nasce como `DRAFT` — visível, mas sinalizada como não confiável. Só depois da revisão humana ela avança para `VALIDATED` e passa a ser consumida com segurança pelo restante do pipeline e por agentes de codificação como o Devin.

```
Dado bruto -> Extrator gera Manifest DRAFT -> Data Steward revisa -> VALIDATED
                                                                          |
                                               SLM documenta usando o contrato validado
                                                                          |
                                               Devin codifica com contexto real do negócio
```

A documentação detalhada de cada uma dessas peças está em [docs/MANIFEST.md](docs/MANIFEST.md) e [docs/SLM.md](docs/SLM.md).

---

## 2. Como o projeto está organizado

```
nimbus/
|-- README.md                 Este arquivo
|-- tasks.py                  Runner de comandos para Windows, Mac e Linux
|-- Makefile                  Alternativa via make (Mac/Linux/WSL)
|-- config.py                 Configuração central (modelos, storage, flags)
|-- run_pipeline.py           Execução direta do pipeline
|-- prefect_flow.py           Orquestração via Prefect, mapeada para Control-M
|-- show_metrics.py           Dashboard de métricas no terminal
|-- requirements.txt
|
|-- docs/                     Toda a documentação técnica do projeto
|   |-- ARCHITECTURE.md       Arquitetura detalhada, camadas e orquestração
|   |-- MANIFEST.md           Como o contrato funciona e o papel do Data Steward
|   |-- SLM.md                O que a IA faz, o que ela recebe e o que produz
|   |-- TESTING.md            Cobertura de testes e critérios de aceite
|   |-- CHANGELOG.md          Histórico de evolução do projeto
|   |-- NEXT_STEPS.md         O que ficou pendente e o que está planejado
|   `-- MIGRATION_PLAN.md     Plano de migração para Azure Databricks
|
|-- src/
|   |-- generators/           Geração de dados fictícios em CSV, JSON e Fixed-Width
|   |-- ingestion/            Normalização de encoding antes da ingestão
|   |-- manifest/             Extratores automáticos e validação HITL
|   |-- storage/              Abstração medallion — LocalStorage ou MinIO
|   |-- validation/           Contratos de dados e detecção de schema evolution
|   |-- profiler/             Profiling estatístico via DuckDB
|   |-- slm/                  Integração com Ollama
|   `-- metrics/              Coleta de métricas e geração de relatórios
|
|-- tests/                    148 testes unitários sem dependências externas
`-- data/                     Camadas medallion em disco (landing, processed, etc.)
```

O fluxo de dados segue a arquitetura medallion: o arquivo bruto entra no Bronze, passa pela validação de contrato, pelo profiling e segue para o Silver. Arquivos com quebras de contrato são isolados em quarentena sem interromper o restante. A SLM documenta o que passou e as métricas consolidam tudo em um relatório por execução.

```
Arquivo bruto (CSV / JSON / Fixed-Width / SAS7BDAT)
        |
  Normaliza encoding (UTF-8, LF)
        |
   [ BRONZE ]  dado bruto recebido
        |
  Validação de contrato ---- breaking change ----> QUARENTENA
        |
  Profiling (DuckDB)
        |
   [ SILVER ]  dado validado
        |
  SLM documenta (Manifest + estatísticas)
        |
  Métricas + Relatório consolidado
```

O detalhamento técnico de cada componente está em [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## 3. Rodando pela primeira vez

O único pré-requisito obrigatório é Python 3.11 ou superior. O Ollama (para documentação semântica) e o Docker (para o backend MinIO) são opcionais — sem eles o pipeline funciona normalmente, apenas sem essas funcionalidades ativas.
Obs.: Instalação do Docker e Ollama deve ser feita através dos sites de cada empresa, segue link de referência:
Docker: https://docs.docker.com/desktop/setup/install/windows-install/
Ollama: https://ollama.com/download/windows

```bash
pip install -r requirements.txt
```

Com isso, três comandos são suficientes para ver o projeto funcionando:

```bash
python tasks.py baseline   # gera dados fictícios e roda o pipeline completo
python tasks.py metrics    # mostra o resultado da execução
python tasks.py breaking   # simula uma quebra de contrato e testa o isolamento em quarentena
```

No Windows, use sempre `python tasks.py` — funciona nativamente sem precisar instalar nada adicional. No Mac e Linux, o `make` também funciona como atalho. Para ver todos os comandos disponíveis, `python tasks.py help`.

Para ativar a documentação semântica via SLM, basta ter o Ollama rodando em segundo plano:

```bash
ollama serve
ollama pull phi3.5
```

Sem isso, o enriquecimento fica marcado como `SKIPPED` e o pipeline segue normalmente. Para ativar o backend MinIO em vez de disco local, `docker compose up -d` e mude `USE_MINIO = True` em `config.py`.

A referência completa de comandos está na tabela abaixo:

| Comando | O que faz |
|---|---|
| `python tasks.py run` | Executa todos os cenários nos três formatos de arquivo |
| `python tasks.py baseline` | Cenário com dados válidos, todos os formatos |
| `python tasks.py breaking` | Simula quebra de contrato e testa o DLQ |
| `python tasks.py metrics` | Resumo do último run |
| `python tasks.py issues` | Mostra apenas registros com problema |
| `python tasks.py test` | Roda a suite de 148 testes unitários |
| `python tasks.py check-manifest --file <path>` | Verifica pendências antes de validar |
| `python tasks.py validate-manifest --file <path> --steward "Nome"` | Promove DRAFT para VALIDATED |
| `python tasks.py help` | Lista todos os comandos |

---

## 4. Onde encontrar mais

| Para entender... | Consulte |
|---|---|
| A arquitetura técnica completa | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| O Manifest e o papel do Data Steward | [docs/MANIFEST.md](docs/MANIFEST.md) |
| Como a SLM funciona e por que não inventa | [docs/SLM.md](docs/SLM.md) |
| Os testes e o que eles garantem | [docs/TESTING.md](docs/TESTING.md) |
| A evolução do projeto ao longo das sprints | [docs/CHANGELOG.md](docs/CHANGELOG.md) |
| O que está pendente e planejado | [docs/NEXT_STEPS.md](docs/NEXT_STEPS.md) |
| O plano de migração para Azure Databricks | [docs/MIGRATION_PLAN.md](docs/MIGRATION_PLAN.md) |
