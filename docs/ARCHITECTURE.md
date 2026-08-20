# Arquitetura — Projeto Nimbus

Este documento descreve a estrutura técnica do pipeline, as decisões de design que moldaram cada componente e como eles se conectam. Para uma visão geral e instruções de uso, consulte o [README](../README.md).

---

## O fluxo de dados de ponta a ponta

O dado chega na landing zone no formato que o sistema de origem produz — CSV, JSON, Fixed-Width ou SAS7BDAT. Um módulo de normalização garante que o arquivo está em UTF-8 com terminadores LF antes de qualquer processamento. Arquivos em EBCDIC são detectados e sinalizados para tratamento manual sem travar o pipeline.

A partir daí, o arquivo entra na camada Bronze e passa pela validação de contrato. Quebras de schema isolam o arquivo na quarentena sem interromper as demais tabelas. Tabelas que passam seguem para o profiling via DuckDB, são promovidas para o Silver já em formato Parquet com compressão Snappy, e têm sua documentação gerada pela SLM. O arquivo original permanece em `bronze/_archive/` para rastreabilidade. Por fim, o upload opcional para o Databricks envia o Parquet para o DBFS e registra a tabela no metastore.

```
Arquivo bruto
     |
 Normalização de encoding
     |
  [ BRONZE ]  formato original
     |
  Validação de contrato ------ breaking change ------> [ QUARENTENA ]
     |
  Profiling (DuckDB)
     |
  [ SILVER ]  Parquet / Snappy          [ BRONZE/_archive/ ]  original preservado
     |
  SLM documenta
     |
  Métricas + Relatório
     |
  Upload Databricks DBFS (opcional)
```

---

## Arquitetura Medallion

| Camada | Diretório | Formato | Papel |
|---|---|---|---|
| Bronze | `data/landing/` | Original (CSV, JSON, TXT…) | Dado bruto como chegou |
| Bronze Archive | `data/landing/_archive/` | Original | Cópia preservada após promoção |
| Silver | `data/processed/` | Parquet (Snappy) | Dado validado e tipado |
| Gold | `data/gold/` | Parquet | Métricas agregadas (Sprint futura) |
| Quarantine | `data/quarantine/` | Original | Breaking changes isolados |
| Contracts | `data/contracts/` | YAML | Manifests de contrato |
| Metrics | `data/metrics/` | JSON | Métricas por execução |
| Reports | `data/reports/` | Markdown | Documentação SLM + relatório |

---

## Storage e Parquet

`src/storage/storage.py` abstrai onde os dados fisicamente residem. Todos os módulos usam a mesma interface sem saber se estão em disco local ou MinIO.

A interface expõe dois métodos de gravação distintos para Bronze e Silver. O `write()` grava CSV — usado para o dado bruto na landing zone. O `write_parquet()` serializa um DataFrame com `pyarrow` em formato Parquet com compressão Snappy — usado pelo `promote_to_parquet()` ao mover dado validado para o Silver.

O `promote_to_parquet()` é o método central da promoção Bronze → Silver. Ele lê o arquivo no formato original, converte para Parquet, grava no Silver e move o original para `_archive/`. Se `DATABRICKS_AUTO_UPLOAD=true` estiver configurado, dispara o upload para o DBFS na sequência — sem bloquear o pipeline em caso de falha.

O `read()` detecta o formato pela extensão e usa o parser correto: `.parquet` via `pd.read_parquet`, `.json` via `json_normalize`, `.txt` via `read_fwf` com colspecs do sidecar `.layout`, `.csv` via `pd.read_csv`.

Dois backends disponíveis, intercambiáveis sem mudança de código:

`LocalStorage` é o padrão — disco local, sem dependências. `MinIOStorage` é ativado com `USE_MINIO=true` e aponta para o container MinIO do `docker-compose.yml` em ambiente Docker.

---

## Deploy com Docker

O projeto inclui um stack Docker completo com três serviços na mesma rede interna:

**`nimbus`** — o pipeline em si. Constrói a partir do `Dockerfile`, monta `data/` como volume bind-mount para que os arquivos Parquet persistam no host e fiquem visíveis fora do container.

**`ollama`** — serve o modelo de linguagem. O modelo configurado em `OLLAMA_MODEL` é baixado automaticamente no primeiro boot via `ollama pull`. Volumes nomeados persistem os modelos entre reinicializações. GPU NVIDIA e AMD/ROCm são suportadas via configuração comentada no `docker-compose.yml`.

**`minio`** — storage S3-compatível. Buckets são criados automaticamente no startup. Console web disponível em `http://localhost:9001`.

O `scripts/entrypoint.sh` coordena a sequência de inicialização: aguarda MinIO e Ollama ficarem saudáveis via healthcheck, baixa o modelo se necessário, inicia o servidor Prefect, registra os deployments, sobe o worker e então executa o pipeline com o cenário configurado em `.env`. Após a execução, o container permanece vivo para comandos manuais.

---

## Suporte multi-formato

O projeto trata dados bancários como eles realmente chegam — em formatos heterogêneos de sistemas distintos.

Para a geração de dados fictícios da PoC, o projeto usa o padrão Strategy: `CSVWriter`, `JSONWriter` e `FixedWidthWriter` recebem um DataFrame em memória e devolvem `(filename, content)`. O gerador de domínio nunca sabe em qual formato o resultado será gravado. O `FixedWidthWriter` gera também um sidecar `.layout` com os colspecs exatos, que o `LocalStorage.read()` usa para garantir a leitura correta.

---

## Validação e schema evolution

O `validator.py` classifica cada arquivo em três resultados. `PASS` ou `WARNING` quando os dados são conformes ao contrato, com eventuais anomalias dentro da tolerância configurada. `DLQ` quando há uma quebra de schema — coluna obrigatória ausente ou tipo incompatível — e o arquivo vai para quarentena. `WARNING NON_BREAKING` quando uma coluna nova é adicionada pela origem, e o pipeline avança normalmente.

---

## Profiling

O profiler usa DuckDB como engine principal pela velocidade, sem servidor nem overhead. Para formatos não suportados diretamente pelo DuckDB — JSON e Fixed-Width — o fallback é Pandas com a mesma lógica de extração de estatísticas. O profiler gera por coluna: percentual de nulos, contagem de valores únicos, min/max para numéricos e os cinco valores mais frequentes para categóricos. Essas estatísticas são o que a SLM recebe junto com o Manifest.

---

## Integração com Databricks

`src/connectors/databricks_uploader.py` integra o pipeline com o Databricks via REST API, sem necessidade de cluster Spark — compatível com Databricks for Students (Community Edition) que disponibiliza apenas SQL Warehouse.

O upload usa a DBFS API em três etapas: abre um handle de escrita, envia o arquivo em blocos de 1MB em base64 e fecha o handle. Após o upload, a tabela é registrada no metastore via Statement Execution API, tornando-a consultável diretamente no SQL Editor com `SELECT * FROM nimbus.tb_clientes LIMIT 100`.

A integração é configurada em `config.py` via variáveis de ambiente e nunca bloqueia o pipeline — falhas no upload são logadas e ignoradas.

---

## Orquestração

Dois modos de execução com a mesma lógica de negócio. O `run_pipeline.py` é execução direta, sem dependência de orquestrador. O `prefect_flow.py` é a mesma pipeline decorada com `@task` e `@flow` do Prefect 2.x, com cada task mapeada para um job Control-M com exit codes padronizados.

| Task Prefect | Job Control-M | Exit codes |
|---|---|---|
| `task_extract_manifest` | JOB-DM-000-EXTRACT (opcional) | 0=OK, 1=SKIPPED, 2=ERROR |
| `task_generate_data` | JOB-DM-001-GENERATE | 0=OK, 2=ERROR |
| `task_validate` | JOB-DM-002-VALIDATE | 0=PASS, 1=WARNING, 2=DLQ |
| `task_profile` | JOB-DM-003-PROFILE | 0=OK, 2=ERROR |
| `task_enrich_slm` | JOB-DM-004-ENRICH | 0=OK, 1=SKIPPED, 2=ERROR |
| `task_collect_metrics` | JOB-DM-005-METRICS | 0=OK |
| `task_report` | JOB-DM-006-REPORT | 0=OK |

Em ambiente Docker, o Prefect server, os deployments e o worker sobem automaticamente via `entrypoint.sh`. O modo `--no-prefect` executa o fluxo sem registrar nada no servidor, útil para integração direta com Control-M.

---

## Métricas e quality score

A cada execução, `metrics_collector.py` calcula um score de 0 a 100 por tabela combinando quatro dimensões: status da validação (40 pontos), taxa de nulos em colunas obrigatórias (30 pontos), taxa de duplicatas (20 pontos) e cobertura de descrições no schema (10 pontos). Scores ficam em JSON em `data/metrics/` e são consultáveis via `python show_metrics.py`.
