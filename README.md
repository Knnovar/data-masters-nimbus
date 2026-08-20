# Projeto Nimbus

Pipeline de dados bancária com arquitetura medallion, contratos de dados extensíveis e documentação semântica gerada por IA local. Construído para resolver uma dor concreta: a distância entre o time de negócio e o time técnico na hora de entender o que um dado significa.

O projeto roda com um único comando e inclui tudo que precisa — pipeline, modelo de IA, storage S3-compatível e orquestração.

---

## 1. Por que este projeto existe

Com LLMs acelerando a velocidade de escrita de código, o gargalo deixou de ser "quão rápido eu codifico" e passou a ser "quão bem eu entendo o dado antes de codificar". Times técnicos seguem implementando sobre tabelas sem contexto de negócio suficiente, e times de negócio não conseguem validar o que foi construído porque a documentação, quando existe, descreve colunas mas não explica o que elas representam no mundo real.

O Nimbus resolve isso com três peças conectadas:

**Manifest** — um contrato YAML versionado que vai além do schema técnico. Descreve de onde o dado vem, qual regulação se aplica, o que cada coluna significa no negócio e exemplos concretos de uso. É o ponto de partida para tudo que o pipeline faz. Ver [docs/MANIFEST.md](docs/MANIFEST.md).

**SLM** — um modelo de linguagem rodando localmente via Ollama que lê o Manifest e as estatísticas reais dos dados e escreve a documentação técnica da tabela em linguagem de negócio. Ela parte sempre do que o Data Steward declarou — não especula, não inventa. Ver [docs/SLM.md](docs/SLM.md).

**Data Steward** — o elo humano do processo. Toda documentação gerada por IA nasce como `DRAFT`. Só depois de revisão humana ela avança para `VALIDATED` e passa a ser consumida com segurança pelo restante do pipeline e por agentes de codificação como o Devin.

```
Dado bruto -> Extrator gera Manifest DRAFT -> Data Steward revisa -> VALIDATED
                                                                          |
                                               SLM documenta com base no contrato validado
                                                                          |
                                               Pipeline promove para Silver em Parquet
                                                                          |
                                               Databricks consome via DBFS ou SQL Warehouse
```

---

## 2. Estrutura do projeto

```
nimbus/
|-- README.md                 Este arquivo
|-- tasks.py                  Runner de comandos (Windows, Mac e Linux)
|-- Makefile                  Alternativa via make (Mac/Linux/WSL)
|-- Dockerfile                Imagem Docker do pipeline
|-- docker-compose.yml        Orquestra pipeline + Ollama + MinIO
|-- .env.example              Template de configuração (copie para .env)
|-- config.py                 Configuração central (lê variáveis de ambiente)
|-- run_pipeline.py           Execução direta do pipeline
|-- prefect_flow.py           Orquestração via Prefect mapeada para Control-M
|-- show_metrics.py           Dashboard de métricas no terminal
|-- requirements.txt
|
|-- docs/                     Documentação completa
|   |-- ARCHITECTURE.md       Arquitetura técnica, camadas e decisões de design
|   |-- MANIFEST.md           Estrutura do contrato e papel do Data Steward
|   |-- SLM.md                Como o modelo de IA se encaixa no fluxo
|   |-- TESTING.md            Cobertura de testes e critérios de aceite
|   |-- CHANGELOG.md          Histórico de evolução do projeto
|   |-- NEXT_STEPS.md         Pendências e planejamento
|   `-- MIGRATION_PLAN.md     Plano de migração para Azure Databricks
|
|-- scripts/
|   `-- entrypoint.sh         Orquestra a inicialização do container
|
|-- src/
|   |-- generators/           Geração de dados fictícios (CSV, JSON, Fixed-Width)
|   |-- ingestion/            Normalização de encoding
|   |-- manifest/             Extratores automáticos e validação HITL
|   |-- storage/              Abstração medallion com suporte a Parquet
|   |-- validation/           Contratos de dados e schema evolution
|   |-- profiler/             Profiling estatístico via DuckDB
|   |-- slm/                  Integração com Ollama
|   |-- metrics/              Coleta de métricas e relatórios
|   `-- connectors/           Integração com sistemas externos (Databricks)
|
|-- tests/                    175 testes unitários
`-- data/                     Camadas medallion (persistem no host via Docker volume)
```

O fluxo de dados segue a arquitetura medallion: o arquivo bruto entra no Bronze no formato original, passa pela validação de contrato e pelo profiling DuckDB, e é promovido para o Silver já em formato Parquet com compressão Snappy. O Bronze preserva o original em `_archive/` para rastreabilidade. Arquivos com quebra de contrato são isolados na quarentena sem interromper o restante.

```
Arquivo bruto (CSV / JSON / Fixed-Width / SAS7BDAT)
        |
  Normaliza encoding (UTF-8, LF)
        |
   [ BRONZE ]  formato original preservado
        |
  Validação de contrato ---- breaking change ----> [ QUARENTENA ]
        |
  Profiling (DuckDB)
        |
   [ SILVER ]  Parquet com compressão Snappy
        |
  SLM documenta (Manifest + estatísticas)       [ BRONZE/_archive/ ]  original arquivado
        |
  Métricas + Relatório consolidado
        |
  Upload para Databricks DBFS (opcional)
```

Detalhamento técnico em [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## 3. Início rápido

### Com Docker (recomendado — one-click)

Requer Docker Desktop instalado. Tudo mais é automático.

```bash
cp .env.example .env
docker compose up --build
```

Na primeira execução o Docker faz o build da imagem, o MinIO e o Ollama sobem, o modelo configurado em `.env` é baixado automaticamente, o Prefect inicia com os deployments registrados e o pipeline roda. Nas execuções seguintes, `docker compose up` é suficiente.

Após subir, a Prefect UI fica disponível em `http://localhost:4200` e o console do MinIO em `http://localhost:9001` (usuário e senha: `minioadmin`).

Para rodar comandos enquanto o container está em execução:

```bash
docker compose exec nimbus python tasks.py metrics
docker compose exec nimbus python tasks.py baseline
docker compose exec nimbus python tasks.py upload-silver
```

### Sem Docker (ambiente local)

```bash
pip install -r requirements.txt
python tasks.py baseline
python tasks.py metrics
```

Para ativar a SLM, o Ollama precisa estar rodando em segundo plano:

```bash
ollama serve
ollama pull phi3.5
```

---

## 4. Configuração

O único arquivo que o usuário precisa editar é o `.env`. O `config.py` lê automaticamente todas as variáveis de ambiente — em Docker elas vêm do `docker-compose.yml`, localmente vêm do `.env`.

| Variável | Padrão | O que controla |
|---|---|---|
| `DEFAULT_SCENARIO` | `baseline` | Cenário executado ao subir o container |
| `DEFAULT_FORMAT` | `all` | Formato dos dados — csv, json, fixed ou all |
| `OLLAMA_MODEL` | `phi3.5` | Modelo baixado automaticamente no primeiro boot |
| `SKIP_SLM` | `false` | Desativa o enriquecimento semântico |
| `MINIO_ACCESS_KEY` | `minioadmin` | Credencial do MinIO |
| `DATABRICKS_HOST` | (vazio) | URL do workspace Databricks |
| `DATABRICKS_TOKEN` | (vazio) | Token de acesso pessoal |
| `DATABRICKS_AUTO_UPLOAD` | `false` | Upload automático após cada promoção Silver |

**GPU NVIDIA:** descomente o bloco `deploy.resources` no `docker-compose.yml`.

**GPU AMD/ROCm:** descomente o bloco de devices no `docker-compose.yml` e adicione `AMD_GFX_VERSION=11.0.0` no `.env`.

**Modelos alternativos:** troque `OLLAMA_MODEL` no `.env` por qualquer modelo disponível no Ollama — `phi4`, `qwen2.5-coder:7b`, `llama3.2`. O download acontece automaticamente no próximo boot.

---

## 5. Comandos disponíveis

| Comando | O que faz |
|---|---|
| `python tasks.py run` | Executa todos os cenários nos três formatos |
| `python tasks.py baseline` | Cenário com dados válidos, todos os formatos |
| `python tasks.py breaking` | Simula quebra de contrato e testa o DLQ |
| `python tasks.py metrics` | Resumo do último run |
| `python tasks.py issues` | Lista apenas registros com problema |
| `python tasks.py test` | Roda os 175 testes unitários |
| `python tasks.py upload-silver` | Envia Parquet do Silver para o Databricks DBFS |
| `python tasks.py test-databricks` | Verifica conectividade com o workspace |
| `python tasks.py check-manifest --file <path>` | Verifica pendências de um manifest |
| `python tasks.py validate-manifest --file <path> --steward "Nome"` | Promove DRAFT para VALIDATED |
| `python tasks.py help` | Lista todos os comandos |

---

## 6. Onde encontrar mais

| Para entender... | Consulte |
|---|---|
| A arquitetura técnica completa | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| O Manifest e o papel do Data Steward | [docs/MANIFEST.md](docs/MANIFEST.md) |
| Como a SLM funciona e por que não inventa | [docs/SLM.md](docs/SLM.md) |
| Os testes e o que eles garantem | [docs/TESTING.md](docs/TESTING.md) |
| A evolução do projeto ao longo das sprints | [docs/CHANGELOG.md](docs/CHANGELOG.md) |
| O que está pendente e planejado | [docs/NEXT_STEPS.md](docs/NEXT_STEPS.md) |
| O plano de migração para Azure Databricks | [docs/MIGRATION_PLAN.md](docs/MIGRATION_PLAN.md) |
