# Arquitetura — Projeto Nimbus

Este documento descreve a estrutura técnica do pipeline, as decisões de design que moldaram cada componente e como eles se conectam. Para uma visão geral do projeto e instruções de uso, consulte o [README](../README.md).

---

## O fluxo de dados de ponta a ponta

O dado chega na landing zone no formato que o sistema de origem produz — pode ser CSV, JSON, Fixed-Width ou SAS7BDAT. Antes de qualquer processamento, um módulo de normalização garante que o arquivo está em UTF-8 com terminadores de linha LF, independentemente do sistema operacional que gerou o arquivo. Arquivos em EBCDIC são detectados e sinalizados para tratamento manual, sem que o pipeline trave.

A partir daí, o arquivo entra na camada Bronze e passa pela validação de contrato. Se o schema não bate com o que foi declarado no Manifest — uma coluna obrigatória removida, por exemplo — o arquivo é isolado na quarentena sem interromper o processamento das demais tabelas. Se a mudança é não-quebradora, como uma coluna nova adicionada pela origem, o pipeline avança com um aviso registrado.

As tabelas que passam pela validação seguem para o profiling via DuckDB, são promovidas para Silver e têm sua documentação gerada pela SLM. Por fim, métricas de qualidade são calculadas e consolidadas em um relatório por execução.

```
Arquivo bruto
     |
 Normalização de encoding
     |
  [ BRONZE ]
     |
  Validação de contrato ------ breaking change ------> [ QUARENTENA ]
     |
  Profiling (DuckDB)
     |
  [ SILVER ]
     |
  SLM documenta
     |
  Métricas + Relatório
```

---

## Arquitetura Medallion

O projeto segue a arquitetura medallion com sete camadas mapeadas em diretórios locais ou buckets S3 quando o backend é MinIO:

O **Bronze** é a landing zone — o dado bruto exatamente como chegou. O **Silver** é onde vão os arquivos que passaram pela validação e pelo profiling. O **Gold** está reservado para métricas agregadas em futuras iterações. A **Quarentena** isola arquivos com breaking changes sem descartá-los — eles ficam disponíveis para análise. Os **Contracts** armazenam os Manifests YAML. As **Metrics** guardam os JSONs de métricas por execução. Os **Reports** reúnem a documentação gerada pela SLM e o relatório consolidado da execução.

---

## A camada de Storage

`src/storage/storage.py` é a abstração que impede que o restante do pipeline saiba onde os dados fisicamente residem. Todos os módulos interagem com a mesma interface — `read()`, `write()`, `move()`, `write_text()` — sem importar se estão trabalhando com disco local ou um bucket MinIO.

O `LocalStorage` é o backend padrão, sem nenhuma dependência externa. O `MinIOStorage` é ativado com `USE_MINIO = True` em `config.py` e requer `docker compose up -d`. A troca é transparente para o pipeline inteiro.

Uma decisão importante: o método `read()` detecta o formato pelo sufixo do arquivo e usa o parser correto automaticamente. Um `.json` é lido via `json_normalize`, um `.txt` é lido via `read_fwf` usando os colspecs gravados em um arquivo sidecar `.layout` gerado no momento da escrita. Isso garante que cada formato pode percorrer o pipeline sem tratamento especial nos módulos downstream.

Essa abstração foi projetada para ser o primeiro passo da migração para ADLS Gen2 — uma nova implementação de `StorageBase` é suficiente para trocar o backend sem tocar em nenhum outro módulo. O plano detalhado está em [MIGRATION_PLAN.md](MIGRATION_PLAN.md).

---

## Suporte multi-formato

O projeto trata dados bancários como eles realmente chegam — em formatos heterogêneos de sistemas distintos. CSV com semicolon de sistemas Windows, JSON aninhado de APIs, arquivos posicionais de mainframe, SAS7BDAT do sistema de crédito.

Para a geração dos dados fictícios da PoC, o projeto usa o padrão Strategy: cada formato tem um Writer (`CSVWriter`, `JSONWriter`, `FixedWidthWriter`) que recebe um DataFrame em memória e devolve `(filename, content)`. A lógica de domínio que gera os dados nunca sabe em qual formato o resultado será gravado.

O `FixedWidthWriter` tem um comportamento específico: ao serializar, gera também um arquivo sidecar `.layout` com os colspecs exatos de cada campo. Esse arquivo é lido pelo `LocalStorage.read()` para garantir que a leitura posterior usa as posições corretas — sem esse sidecar, `read_fwf` precisaria inferir as colunas por análise heurística, o que introduziria erros.

---

## Validação e detecção de schema evolution

O `validator.py` compara o arquivo recebido com o contrato declarado no Manifest e classifica o resultado em três categorias. O cenário feliz retorna `PASS` ou `WARNING` — quando há nulos acima da tolerância ou duplicatas dentro de limites aceitáveis. Um breaking change, como uma coluna obrigatória removida ou um tipo incompatível, retorna `DLQ` e move o arquivo para quarentena. Uma mudança não-quebradora, como uma coluna nova adicionada pela origem, retorna `WARNING` com o tipo de evolução registrado.

O Manifest em status `DRAFT` não bloqueia o pipeline, mas gera um aviso em todas as execuções enquanto não for promovido para `VALIDATED`.

---

## Profiling

O profiler usa DuckDB como engine principal pela velocidade — sem servidor, sem overhead. Para arquivos em formatos não suportados diretamente pelo DuckDB (JSON, Fixed-Width) ou quando o DuckDB não está disponível no ambiente, o fallback é Pandas com a mesma lógica de extração de estatísticas.

O profiler gera por coluna: percentual de nulos, contagem de valores únicos, min, max e média para numéricos, e os cinco valores mais frequentes para categóricos. Essas estatísticas são o que a SLM recebe junto com o Manifest.

---

## Orquestração

O projeto oferece dois modos de execução com a mesma lógica de negócio. O `run_pipeline.py` é execução direta, sem dependência de orquestrador — adequado para desenvolvimento e para integração com scripts externos. O `prefect_flow.py` é a mesma pipeline decorada com `@task` e `@flow` do Prefect 2.x, com cada task mapeada para um job Control-M com exit codes padronizados.

| Task Prefect | Job Control-M | Exit codes |
|---|---|---|
| `task_extract_manifest` | JOB-DM-000-EXTRACT (opcional) | 0=OK, 1=SKIPPED, 2=ERROR |
| `task_generate_data` | JOB-DM-001-GENERATE | 0=OK, 2=ERROR |
| `task_validate` | JOB-DM-002-VALIDATE | 0=PASS, 1=WARNING, 2=DLQ |
| `task_profile` | JOB-DM-003-PROFILE | 0=OK, 2=ERROR |
| `task_enrich_slm` | JOB-DM-004-ENRICH | 0=OK, 1=SKIPPED, 2=ERROR |
| `task_collect_metrics` | JOB-DM-005-METRICS | 0=OK |
| `task_report` | JOB-DM-006-REPORT | 0=OK |

O modo `--no-prefect` executa o mesmo fluxo sem registrar nada no servidor Prefect, o que torna a integração com Control-M simples:

```bash
python prefect_flow.py --no-prefect --scenario baseline --run-id %%JOBRUNID%%
```

---

## Métricas e quality score

A cada execução, `metrics_collector.py` calcula um score de 0 a 100 por tabela combinando quatro dimensões: o status da validação (40 pontos), a taxa de nulos em colunas obrigatórias (30 pontos), a taxa de duplicatas (20 pontos) e a cobertura de descrições no schema (10 pontos). Esses scores ficam em JSON em `data/metrics/` e são consultáveis via `python show_metrics.py`.
