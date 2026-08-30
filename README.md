# Projeto Nimbus

Pipeline de dados bancária com arquitetura medallion, contratos de dados extensíveis e documentação semântica gerada por IA local. Construído para resolver uma dor concreta: a distância entre o time de negócio e o time técnico na hora de entender o que um dado significa.

O projeto roda com um único comando e inclui tudo que precisa: pipeline, modelo de IA, storage S3-compatível, orquestração e integração com Databricks.

---

## 1. A ideia central

O **Manifest** é um arquivo YAML versionado que vai além do schema técnico. Descreve de onde o dado vem, qual regulação se aplica, o que cada coluna significa no negócio bancário e exemplos concretos de uso. É o ponto de partida para tudo que o pipeline faz.

A **SLM** roda localmente via Ollama e, depois que o dado passa pela validação e pelo profiling, lê o Manifest junto com as estatísticas reais e escreve a documentação técnica em linguagem de negócio. Ela parte sempre do que o Data Steward declarou — não especula, não inventa.

O **Data Steward** é quem fecha o ciclo. Toda documentação gerada por IA nasce como `DRAFT`. Só depois de revisão humana ela avança para `VALIDATED` e passa a ser consumida com segurança pelo restante do pipeline e por agentes de codificação como o Devin.

O **Silver** armazena os dados em Parquet com os tipos declarados no Manifest — não os inferidos pelo PyArrow. Uma coluna `fl_ativo: boolean` chega ao Silver como `pa.bool_()` porque o Steward disse que é boolean, não porque o PyArrow adivinhou. O footer do arquivo carrega metadata rastreável indicando se o schema veio de um Manifest `VALIDATED` ou `DRAFT`.

O **Databricks** recebe os dados via REST API: Parquet sobe para o DBFS em pasta por tabela, é convertido para Delta Lake (com histórico de execuções via `DESCRIBE HISTORY`), a tabela é registrada no metastore e os comentários das colunas são populados automaticamente a partir do Manifest.

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
|-- config.py                 Lê todas as configs via variaveis de ambiente
|-- run_pipeline.py           Execucao direta
|-- prefect_flow.py           Orquestracao Prefect mapeada para Control-M
|-- show_metrics.py           Dashboard no terminal
|
|-- docs/
|   |-- ARCHITECTURE.md
|   |-- MANIFEST.md
|   |-- SLM.md
|   |-- TESTING.md
|   |-- CHANGELOG.md
|   |-- NEXT_STEPS.md
|   `-- MIGRATION_PLAN.md
|
|-- scripts/
|   `-- entrypoint.sh
|
|-- src/
|   |-- generators/           Dados ficticios (CSV, JSON, Fixed-Width)
|   |-- ingestion/            Normalizacao de encoding
|   |-- manifest/             Extratores automaticos e validacao HITL
|   |-- storage/              Abstracoes medallion + Parquet governado
|   |-- validation/           Contratos e schema evolution
|   |-- profiler/             Profiling via DuckDB
|   |-- slm/                  Integracao com Ollama
|   |-- metrics/              Metricas e relatorios
|   `-- connectors/           Integracao Databricks via REST API
|
|-- tests/                    242 testes unitarios
`-- data/                     Camadas medallion (persiste no host via Docker volume)
```

---

## 3. Inicio rapido

### Com Docker (recomendado)

```bash
cp .env.example .env
# Se for a primeira vez e quiser evitar timeout do Ollama:
docker run --rm -v ollama_models:/root/.ollama ollama/ollama pull phi3.5
docker compose up --build
```

Prefect UI: `http://localhost:4200` | MinIO UI: `http://localhost:9001`

### Sem Docker

```bash
pip install -r requirements.txt
python tasks.py baseline
python tasks.py metrics
```

---

## 4. Configuracao

O unico arquivo que o usuario precisa editar e o `.env`. O `config.py` le tudo via variaveis de ambiente.

| Variavel | Padrao | O que controla |
|---|---|---|
| `OLLAMA_MODEL` | `phi3.5` | Modelo baixado no primeiro boot |
| `SKIP_SLM` | `false` | Desativa enriquecimento semantico |
| `DATABRICKS_HOST` | (vazio) | URL do workspace |
| `DATABRICKS_TOKEN` | (vazio) | Token de acesso pessoal |
| `DATABRICKS_WAREHOUSE_ID` | (vazio) | ID do SQL Warehouse |
| `DATABRICKS_AUTO_UPLOAD` | `false` | Upload automatico apos cada run |

GPU NVIDIA: descomente `deploy.resources` no `docker-compose.yml`.
GPU AMD/ROCm: descomente o bloco de devices e adicione `AMD_GFX_VERSION` no `.env`.

---

## 5. Comandos principais

| Comando | O que faz |
|---|---|
| `python tasks.py run` | Todos os cenarios nos tres formatos |
| `python tasks.py baseline` | Cenario padrao, todos os formatos |
| `python tasks.py breaking` | Simula quebra de contrato e testa DLQ |
| `python tasks.py metrics` | Resumo do ultimo run |
| `python tasks.py test` | 242 testes unitarios |
| `python tasks.py test-databricks` | Diagnostico em 4 niveis |
| `python tasks.py upload-silver` | Upload -> DBFS -> Delta -> metastore |
| `python tasks.py upload-silver --dry-run` | Valida sem enviar dados |
| `python tasks.py validate-manifest --file <path> --steward "Nome"` | Promove DRAFT->VALIDATED |
| `python tasks.py help` | Lista todos os comandos |

---

## 6. Onde encontrar mais

| Para entender... | Consulte |
|---|---|
| Arquitetura tecnica completa | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| Manifest e papel do Data Steward | [docs/MANIFEST.md](docs/MANIFEST.md) |
| Como a SLM funciona | [docs/SLM.md](docs/SLM.md) |
| Testes e criterios de aceite | [docs/TESTING.md](docs/TESTING.md) |
| Evolucao do projeto | [docs/CHANGELOG.md](docs/CHANGELOG.md) |
| Pendencias e planejamento | [docs/NEXT_STEPS.md](docs/NEXT_STEPS.md) |
| Plano de migracao Azure Databricks | [docs/MIGRATION_PLAN.md](docs/MIGRATION_PLAN.md) |
