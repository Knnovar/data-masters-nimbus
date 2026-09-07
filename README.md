# Projeto Nimbus

Pipeline de dados bancária com arquitetura medallion, contratos de dados extensíveis e documentação semântica gerada por IA local. Construído para resolver uma dor concreta: a distância entre o time de negócio e o time técnico na hora de entender o que um dado significa.

O projeto roda com um único comando e inclui tudo que precisa: pipeline, modelo de IA, storage S3-compatível, orquestração e integração com Databricks via Unity Catalog.

---

## 1. A ideia central

O **Manifest** é um arquivo YAML versionado que vai além do schema técnico. Descreve de onde o dado vem, qual regulação se aplica, o que cada coluna significa no negócio bancário e exemplos concretos de uso. É o ponto de partida para tudo que o pipeline faz.

A **SLM** roda localmente via Ollama e, depois que o dado passa pela validação e pelo profiling, lê o Manifest junto com as estatísticas reais e escreve a documentação técnica em linguagem de negócio. Ela parte sempre do que o Data Steward declarou — não especula, não inventa.

O **Data Steward** é quem fecha o ciclo. Toda documentação gerada por IA nasce como `DRAFT`. Só depois de revisão humana ela avança para `VALIDATED` e passa a ser consumida com segurança pelo restante do pipeline e por agentes de codificação como o Devin.

O **Silver** armazena os dados em Parquet com os tipos declarados no Manifest — não os inferidos pelo PyArrow. Uma coluna `fl_ativo: boolean` chega ao Silver como `pa.bool_()` porque o Steward disse que é boolean, não porque o PyArrow adivinhou. O footer do arquivo carrega metadata rastreável indicando se o schema veio de um Manifest `VALIDATED` ou `DRAFT`.

O **Databricks** recebe duas camadas via Files API (Unity Catalog Volumes). O Bronze copia o arquivo bruto para `nimbus.bronze` (todas as colunas STRING, mais provenance de ingestão). O Silver grava o Parquet tipado em `nimbus.silver`, registra a managed Delta table via `CREATE OR REPLACE TABLE ... AS SELECT * FROM read_files(...)` e popula tags de governança (LGPD, SCR) a partir do Manifest.

```
Dado bruto -> Extrator gera Manifest DRAFT -> Data Steward valida -> VALIDATED
                                                                          |
                                               SLM documenta com base no contrato validado
                                                                          |
                                               Silver em Parquet com tipos do Manifest
                                                                          |
                                               Databricks Bronze (bruto) + Silver (Delta + tags)
```

---

## 2. Estrutura do projeto

```
nimbus/
|-- README.md
|-- tasks.py                  Runner cross-platform (Windows, Mac, Linux)
|-- Makefile                  Atalhos via make (Mac/Linux/WSL)
|-- Dockerfile                Imagem Docker do pipeline
|-- docker-compose.yml        Pipeline + Ollama + MinIO
|-- .env.example              Template de configuracao
|-- config.py                 Le todas as configs via variaveis de ambiente
|-- run_pipeline.py           Execucao direta
|-- prefect_flow.py           Orquestracao Prefect mapeada para Control-M
|-- show_metrics.py           Dashboard no terminal
|
|-- docs/
|   |-- ARCHITECTURE.md       Arquitetura tecnica e integracao Databricks
|   |-- MANIFEST.md           Estrutura do contrato e papel do Data Steward
|   |-- SLM.md                Como o modelo de IA se encaixa no fluxo
|   |-- TESTING.md            Cobertura de testes e criterios de aceite
|   |-- CHANGELOG.md          Historico de evolucao por sprint
|   |-- NEXT_STEPS.md         Pendencias e planejamento
|   `-- MIGRATION_PLAN.md     Plano de migracao para Azure Databricks
|
|-- scripts/
|   `-- entrypoint.sh         Orquestra inicializacao do container
|
|-- src/
|   |-- generators/           Dados ficticios (CSV, JSON, Fixed-Width)
|   |-- ingestion/            Normalizacao de encoding
|   |-- manifest/             Extratores automaticos e validacao HITL
|   |-- storage/              Abstracoes medallion + Parquet governado pelo Manifest
|   |-- validation/           Contratos e schema evolution
|   |-- profiler/             Profiling via DuckDB
|   |-- slm/                  Integracao com Ollama
|   |-- metrics/              Metricas e relatorios
|   `-- connectors/           Integracao Databricks via Files API + Unity Catalog
|
|-- tests/                    325 testes unitarios
`-- data/                     Camadas medallion (persiste no host via Docker volume)
```

O fluxo de dados: arquivo bruto entra no Bronze no formato original, passa pela validação de contrato e profiling DuckDB, é promovido para o Silver já em Parquet com os tipos do Manifest. Bronze preserva o original em `_archive/`. Arquivos com quebra de contrato vão para quarentena sem interromper o restante.

---

## 3. Inicio rapido

### Com Docker (recomendado)

```bash
cp .env.example .env
# Evita timeout do Ollama na primeira execucao:
docker run --rm -v ollama_models:/root/.ollama ollama/ollama pull phi3.5
docker compose up --build
```

Prefect UI: `http://localhost:4200` | MinIO UI: `http://localhost:9001`

Para rodar comandos com o container em execucao:

```bash
docker compose exec nimbus python tasks.py metrics
docker compose exec nimbus python tasks.py upload-bronze
docker compose exec nimbus python tasks.py upload-silver
```

### Sem Docker

```bash
pip install -r requirements.txt
python tasks.py baseline
python tasks.py metrics
```

---

## 4. Configuracao

O unico arquivo que o usuario precisa editar e o `.env`. O `config.py` le tudo via variaveis de ambiente — em Docker elas vem do `docker-compose.yml`, localmente vem do `.env`.

| Variavel | Padrao | O que controla |
|---|---|---|
| `OLLAMA_MODEL` | `phi3.5` | Modelo baixado automaticamente no primeiro boot |
| `SKIP_SLM` | `false` | Desativa enriquecimento semantico |
| `DATABRICKS_HOST` | (vazio) | URL do workspace |
| `DATABRICKS_TOKEN` | (vazio) | PAT ou vazio para OAuth |
| `DATABRICKS_WAREHOUSE_ID` | (vazio) | SQL Editor > nome do warehouse > copy ID |
| `DATABRICKS_CATALOG` | `nimbus` | Catalog UC |
| `DATABRICKS_SILVER_SCHEMA` | `silver` | Schema das tabelas Silver |
| `DATABRICKS_BRONZE_SCHEMA` | `bronze` | Schema das tabelas Bronze |
| `DATABRICKS_VOLUME` | `landing` | Volume UC do Silver |
| `DATABRICKS_BRONZE_VOLUME` | `landing` | Volume UC do Bronze |
| `DATABRICKS_AUTO_UPLOAD` | `true` | Publica Silver apos cada run |
| `DATABRICKS_BRONZE_UPLOAD` | `true` | Publica o arquivo bruto apos a geracao |

GPU NVIDIA: descomente `deploy.resources` no `docker-compose.yml`.
GPU AMD/ROCm: descomente o bloco de devices e adicione `AMD_GFX_VERSION` no `.env`.
Modelo alternativo: troque `OLLAMA_MODEL` no `.env` — o download acontece no proximo boot.

### Pre-requisito Databricks (executar uma vez no SQL Editor)

```sql
CREATE SCHEMA IF NOT EXISTS nimbus.bronze;
CREATE SCHEMA IF NOT EXISTS nimbus.silver;
CREATE VOLUME IF NOT EXISTS nimbus.bronze.landing;
CREATE VOLUME IF NOT EXISTS nimbus.silver.landing;
```

---

## 5. Comandos principais

| Comando | O que faz |
|---|---|
| `python tasks.py run` | Todos os cenarios nos tres formatos |
| `python tasks.py baseline` | Cenario padrao, todos os formatos |
| `python tasks.py breaking` | Simula quebra de contrato e testa DLQ |
| `python tasks.py metrics` | Resumo do ultimo run |
| `python tasks.py test` | 325 testes unitarios |
| `python tasks.py test-databricks` | Diagnostico de conectividade em 4 niveis |
| `python tasks.py upload-bronze` | Upload do arquivo bruto -> Volume bronze |
| `python tasks.py upload-silver` | Upload Parquet -> Volume silver -> Delta -> metastore |
| `python tasks.py upload-silver --dry-run` | Valida configuracao sem enviar dados |
| `python tasks.py upload-silver --table tb_clientes` | Envia apenas uma tabela |
| `python tasks.py validate-manifest --file <path> --steward "Nome"` | Promove DRAFT para VALIDATED |
| `python tasks.py help` | Lista todos os comandos |

---

## 6. Onde encontrar mais

| Para entender... | Consulte |
|---|---|
| Arquitetura tecnica completa e integracao Databricks | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| Manifest e papel do Data Steward | [docs/MANIFEST.md](docs/MANIFEST.md) |
| Como a SLM funciona e por que nao inventa | [docs/SLM.md](docs/SLM.md) |
| Testes e criterios de aceite | [docs/TESTING.md](docs/TESTING.md) |
| Evolucao do projeto sprint a sprint | [docs/CHANGELOG.md](docs/CHANGELOG.md) |
| O que esta pendente e planejado | [docs/NEXT_STEPS.md](docs/NEXT_STEPS.md) |
| Plano de migracao para Azure Databricks | [docs/MIGRATION_PLAN.md](docs/MIGRATION_PLAN.md) |
