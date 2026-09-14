# %% [markdown]
# (arquivo em formato jupytext 'percent': o VS Code/Jupyter abre como notebook)

# %% [markdown]
# # Projeto Nimbus — Roteiro operacional de teste e apresentacao
#
# Notebook de **ensaio e demonstracao** da branch `feature/one-click-security`.
#
# **Como usar**
# - Abra este notebook **na raiz do repositorio** (o mesmo diretorio de `run_pipeline.py` e `tasks.py`), com o venv do projeto como kernel.
# - As celulas usam `!` (shell) e rodam tanto no Windows quanto no Linux/macOS, exceto onde indicado.
# - Rode **na ordem**. Cada secao prova uma coisa especifica e depende do estado deixada pela anterior.
#
# **Estrutura**
#
# | Parte | Conteudo | Roda automatico? |
# |---|---|---|
# | 0 | Pre-voo: ambiente, arquivos, sintaxe | sim |
# | 1 | Limpeza local (`data/`) | sim (confirmacao explicita na celula) |
# | 2 | Suite de testes | sim |
# | 3 | Cenario baseline (exit 0) | sim |
# | 4 | Cenario type_drift (exit 2) + quarentena | sim |
# | 5 | Metricas e quality score | sim |
# | 6 | Idempotencia / SHA-256 | sim |
# | 7 | MinIO one-click (object storage S3) | sim (precisa Docker) |
# | 8 | Container completo | sim (precisa Docker) |
# | 9 | `emit-grants` (DDL offline) | sim |
# | 10 | Publicacao no Databricks | sim (precisa `.env` com PAT) |
# | **11** | **Limpeza das tabelas no Databricks** | **NAO — SQL para copiar e colar** |
# | 12 | Ordem sugerida para a apresentacao | leitura |
#
# > **Antes de comecar:** faca um backup do `.env` (`cp .env .env.bak` / `copy .env .env.bak`). Nada aqui apaga o `.env`, mas o `nimbus_up.py` reescreve o arquivo com permissao `0600` quando falta credencial do MinIO.

# %% [markdown]
# ---
# ## Parte 0 — Pre-voo
#
# Checa se o ambiente esta no estado que o resto do notebook assume. Se algo aqui falhar, os passos seguintes falham por consequencia.

# %%
# 0.1 — Onde estou e com qual Python
import sys, os, platform, pathlib
print("cwd        :", pathlib.Path.cwd())
print("python     :", sys.version.split()[0], "|", sys.executable)
print("plataforma :", platform.system(), platform.release())
esperados = ["run_pipeline.py", "tasks.py", "config.py", "requirements.txt", "docker-compose.yml"]
faltando  = [f for f in esperados if not pathlib.Path(f).exists()]
print("faltando   :", faltando or "nenhum (raiz correta)")

# %%
# 0.2 — Dependencias criticas presentes no venv
import importlib
for mod in ["pandas", "yaml", "pyarrow", "duckdb", "minio", "requests"]:
    try:
        m = importlib.import_module(mod)
        print(f"  OK   {mod:<10} {getattr(m, '__version__', '')}")
    except ImportError as e:
        print(f"  FALTA {mod:<10} -> {e}")
# Se faltar algo: python -m pip install -r requirements.txt

# %%
# 0.3 — Estado do Git (esperado: arvore limpa, manifests versionados)
!git status --short
!git ls-files data/contracts/

# %%
# 0.4 — Sintaxe do entrypoint e do compose (o que quebrava o container na branch)
# Linux/macOS/Git Bash:
!bash -n scripts/entrypoint.sh && echo "entrypoint OK"
# Credenciais ficticias so para validar a interpolacao do compose:
!MINIO_ACCESS_KEY=x MINIO_SECRET_KEY=y docker compose config > /dev/null && echo "compose OK"

# %% [markdown]
# No **Windows sem Git Bash**, troque a celula acima por:
#
# ```powershell
# $env:MINIO_ACCESS_KEY="x"; $env:MINIO_SECRET_KEY="y"; docker compose config | Out-Null; if ($?) { "compose OK" }
# ```
#
# O `bash -n` nao tem equivalente nativo — rode dentro do Git Bash ou do WSL.

# %% [markdown]
# ---
# ## Parte 1 — Limpeza local (`data/`)
#
# Comeca a demo do zero: apaga dados gerados, metricas, relatorios e quarentena, e **preserva `data/contracts/`** (Manifest e artefato de governanca, nao dado gerado).
#
# O comando de CLI equivalente e `python tasks.py clean-data` — ele **pede confirmacao interativa** (`input()`), o que travaria o notebook. A celula abaixo faz o mesmo sem prompt, com o flag explicito logo acima.

# %%
# 1.1 — Limpeza local. Mude para True para executar de fato.
CONFIRMO_LIMPEZA_LOCAL = False

import pathlib
subdirs = ["landing", "processed", "quarantine", "gold", "metrics", "reports"]  # contracts fica de fora
if not CONFIRMO_LIMPEZA_LOCAL:
    print("Nada removido. Defina CONFIRMO_LIMPEZA_LOCAL = True para limpar.")
    for s in subdirs:
        d = pathlib.Path("data") / s
        n = len(list(d.glob("*"))) if d.exists() else 0
        print(f"  seria limpo: data/{s:<11} ({n} itens)")
else:
    total = 0
    for s in subdirs:
        d = pathlib.Path("data") / s
        if d.exists():
            for f in d.glob("*"):
                if f.is_file():
                    f.unlink(); total += 1
    print(f"{total} arquivos removidos. data/contracts/ preservado.")

# %% [markdown]
# > Se quiser mesmo apagar os Manifests (raramente): `python tasks.py clean-data --contracts` no terminal. Isso derruba manifests **ja promovidos a VALIDATED** e voce precisa promover de novo antes da demo.

# %% [markdown]
# ---
# ## Parte 2 — Suite de testes
#
# Prova que nada quebrou. Esperado: **`Ran 627 tests` / `OK (skipped=1)`**, ~40s.
#
# Sinais de patch mal aplicado: `ImportError: cannot import name 'seed_all'` ou `collect() got an unexpected keyword argument 'dat_ref'`.

# %%
!python -m unittest discover -s tests -p "test_*.py" 2>&1 | tail -20

# %%
# Equivalente pelo task runner (roda tests/run_tests.py -v, saida mais verbosa)
# !python tasks.py test

# %%
# 2.1 — Guarda contra o erro de digitacao que ja aconteceu: teste que nunca roda
import pathlib
mortos = [p.name for p in pathlib.Path("tests").glob("*.py") if not p.name.startswith(("test_", "run_", "__"))]
print("arquivos em tests/ fora do padrao test_*.py:", mortos or "nenhum")

# %% [markdown]
# ---
# ## Parte 3 — Cenario baseline (caminho feliz)
#
# Carga conforme o contrato: gate aprova, Silver tipada e publicada. **Exit code esperado: 0.**

# %%
# 3.1 — Executa e captura o exit code (o log completo sai acima da ultima linha)
import subprocess, sys
p = subprocess.run([sys.executable, "run_pipeline.py", "--scenario", "baseline", "--format", "csv"])
print("exit code =", p.returncode, "(esperado 0)")

# %%
# 3.2 — O que ficou em disco: Bronze preserva o original, Silver e Parquet tipado
import pathlib
for layer in ["landing", "processed", "quarantine", "metrics", "reports"]:
    d = pathlib.Path("data") / layer
    itens = sorted(p.name for p in d.glob("*")) if d.exists() else []
    print(f"data/{layer:<11}: {itens}")

# %%
# 3.3 — Prova de tipagem da Silver: o schema do Parquet vem do Manifest, nao do inferido
import pyarrow.parquet as pq, pathlib
alvo = next(pathlib.Path("data/processed").glob("tb_clientes*.parquet"), None)
print(pq.read_schema(alvo) if alvo else "nenhum parquet de tb_clientes encontrado")

# %% [markdown]
# ---
# ## Parte 4 — Cenario type_drift (gate bloqueando)
#
# Valor fora do tipo declarado no Manifest. O gate reprova, a carga vai para **quarentena** e **nao** fica legivel na Silver. **Exit code esperado: 2.**
#
# Exit 2 nao e erro de execucao: e o pipeline dizendo "bloqueei de proposito". O CI trata 0 e 2 como sucesso e qualquer outro codigo como falha real.

# %%
import subprocess, sys
p = subprocess.run([sys.executable, "run_pipeline.py", "--scenario", "type_drift", "--format", "csv"])
print("exit code =", p.returncode, "(esperado 2 = bloqueio de gate)")

# %%
# 4.1 — A prova visual do gate: o parquet reprovado esta na quarentena, nao na Silver
import pathlib
q = sorted(p.name for p in pathlib.Path("data/quarantine").glob("*"))
s = sorted(p.name for p in pathlib.Path("data/processed").glob("*"))
print("quarantine :", q)
print("processed  :", s)
alvo = "tb_clientes.parquet"
print(f"\n{alvo} em quarantine? {alvo in q}   (esperado True)")
print(f"{alvo} em processed?  {alvo in s}   (esperado False)")

# %%
# 4.2 — Rastreabilidade do rejeito: motivo, colunas e valores mascarados
import pathlib, pandas as pd
rej = next(pathlib.Path("data/quarantine").glob("reject_*.csv"), None)
if rej:
    df = pd.read_csv(rej)
    cols = [c for c in df.columns if c.startswith("_reject")]
    print(rej.name, "|", len(df), "linhas rejeitadas")
    print(df[cols].head(5).to_string())
    pii = [c for c in df.columns if df[c].astype(str).str.startswith("MASK:").any()]
    print("\ncolunas mascaradas:", pii or "nenhuma nesta amostra")
else:
    print("sem CSV de rejeito nesta run")

# %% [markdown]
# O token `MASK:<hash>` do mascaramento e **deterministico de proposito** (preserva correlacao entre linhas na investigacao) e por isso **nao e anonimizacao juridica** — quem tem o valor original recomputa o token. Diga isso antes de a banca perguntar.

# %% [markdown]
# ---
# ## Parte 5 — Metricas e quality score

# %%
!python tasks.py metrics

# %%
!python tasks.py score

# %%
# 5.1 — Somente os problemas (DLQ/WARNING)
!python tasks.py issues

# %%
# 5.2 — Historico completo de runs
# !python tasks.py metrics-all

# %% [markdown]
# ---
# ## Parte 6 — Idempotencia e SHA-256
#
# A identidade logica da carga e `(tabela, dat_ref, formato)` — nao o `run_id`, que muda a cada execucao. Cada carga registra o SHA-256 do arquivo de entrada no ledger `data/metrics/_ingest_ledger.json`, e a classificacao e uma de tres:
#
# - `FIRST_LOAD` — nao havia carga dessa chave;
# - `REPROCESS_IDENTICAL` — mesma janela, arquivo byte a byte igual;
# - `REPROCESS_MODIFIED` — mesma janela, **arquivo diferente** (o caso perigoso: partição auditada sendo substituida por outro conteudo).
#
# Rode a **mesma `dat_ref` duas vezes**. A 2a run deve logar `REPROCESS_IDENTICAL`.

# %%
!python run_pipeline.py --scenario baseline --format csv --dat-ref 2025-08-01

# %%
!python run_pipeline.py --scenario baseline --format csv --dat-ref 2025-08-01

# %%
# 6.1 — O ledger: hash, situacao e contador de reprocessamento
import json, pathlib
led = pathlib.Path("data/metrics/_ingest_ledger.json")
if led.exists():
    data = json.loads(led.read_text(encoding="utf-8"))
    for chave, ent in data.items():
        if isinstance(ent, dict):
            print(f"{chave}")
            for k in ("status", "rows", "run_id", "reprocess_count",
                      "input_sha256", "previous_sha256", "input_situation"):
                if k in ent:
                    v = ent[k]
                    if k.endswith("sha256") and isinstance(v, str):
                        v = v[:12] + "..."
                    print(f"    {k:<17} {v}")
else:
    print("ledger ainda nao existe — rode a Parte 3 primeiro")

# %%
# 6.2 — Carga incremental: --skip-existing pula o que ja passou com o MESMO arquivo
!python run_pipeline.py --scenario baseline --format csv --dat-ref 2025-08-01 --skip-existing

# %% [markdown]
# **Limite honesto, e a banca pode perguntar:** o ledger e um JSON reescrito inteiro, sem lock e sem estado `RUNNING`. Serve para execucao sequencial, nao para duas runs concorrentes da mesma chave.
#
# E com `REPROCESS_MODIFIED` o `--skip-existing` e **ignorado de proposito**: pular ali seria afirmar "ja ingerido" sobre um conteudo que nunca foi ingerido.

# %% [markdown]
# ---
# ## Parte 7 — MinIO one-click (object storage compativel com S3)
#
# Prova que o pipeline nao depende de filesystem local: as mesmas 7 camadas (`bronze`, `silver`, `gold`, `quarantine`, `contracts`, `metrics`, `reports`) viram buckets S3.
#
# O bootstrap gera credencial se faltar, **preserva a que existe** (e as suas variaveis do Databricks), sobe o MinIO, espera o healthcheck e cria os buckets usando o **proprio `get_storage()` do pipeline** — se o bootstrap funciona, o pipeline funciona pelo mesmo caminho de codigo.
#
# Precisa de Docker rodando.

# %%
# 7.1 — up + pipeline + score contra o MinIO, sem exportar variavel no shell
!python tasks.py demo --scenario baseline --format csv

# %%
# 7.2 — Credencial para abrir o console em http://localhost:9001
!python tasks.py minio-creds

# %% [markdown]
# Abra `http://localhost:9001`, faca login com a saida acima e mostre:
# - os 7 buckets criados;
# - o arquivo **original** no `bronze` (Bronze preserva o recebido, sem cast e sem validacao);
# - o Parquet tipado no `silver`.
#
# Comandos separados, se preferir controlar a stack na mao:
#
# ```bash
# python tasks.py up            # sobe o MinIO e cria buckets (--reset recria o volume)
# python tasks.py down          # derruba containers, mantem volume e credencial
# ```
#
# Se der `SignatureDoesNotMatch` ou `InvalidAccessKeyId`, e volume com credencial antiga: `python tasks.py up --reset`.

# %%
# 7.3 — (opcional) derruba a stack ao final da demo
# !python tasks.py down

# %% [markdown]
# ---
# ## Parte 8 — Container completo
#
# Era o passo que **morria na largada** na branch, por erro de sintaxe no `scripts/entrypoint.sh`. Depois da correcao deve subir e logar "Pipeline concluida".
#
# Roda em foreground — execute no terminal, nao no notebook, se quiser acompanhar o log ao vivo.

# %%
# !docker compose up --build

# %%
# 8.1 — Confere os defaults de seguranca dentro do container
!MINIO_ACCESS_KEY=x MINIO_SECRET_KEY=y docker compose config | grep -i -E "QUARANTINE|image:"

# %% [markdown]
# Esperado: `DATABRICKS_QUARANTINE_UPLOAD=false`, `QUARANTINE_MASK_PII=true`, `QUARANTINE_BLOCKED_SILVER=true` e imagens **pinadas por digest/tag fixa** (sem `:latest`, sem `minioadmin` como default).

# %% [markdown]
# ---
# ## Parte 9 — `emit-grants`: do contrato para a permissao
#
# Le a classificacao de sensibilidade do Manifest e **imprime o DDL** de `GRANT` e das mascaras de coluna. Nao abre conexao, nao autentica, nao executa, nao cria service principal, nao altera permissao.
#
# A frase para a banca: *o pipeline nao concede permissao; ele deriva a permissao do contrato e entrega para quem tem a alcada.*

# %%
!python tasks.py emit-grants --file data/contracts/tb_clientes.yaml

# %%
# 9.1 — Contrato com classificacao mais alta, para mostrar o GRANT SELECT comentado
# !python tasks.py emit-grants --file data/contracts/tb_transacoes.yaml

# %% [markdown]
# Dois pontos que valem ser ditos em voz alta:
# - a mascara e **uma funcao por tipo** (`mask_pii_string` devolve `'***'`, `mask_pii_date` devolve `NULL`), porque o Unity Catalog exige que a funcao devolva o tipo da coluna;
# - com classificacao `restricted`/`secret`/`confidential_restricted` o `GRANT SELECT` sai **comentado**: quem libera leitura e o dono do dado, nao o pipeline.

# %% [markdown]
# ---
# ## Parte 10 — Publicacao no Databricks
#
# Precisa de `.env` com `DATABRICKS_HOST`, `DATABRICKS_TOKEN` e `DATABRICKS_WAREHOUSE_ID`. **Nunca** cole token aqui dentro — o notebook vai para o repositorio.
#
# Objetos usados (defaults do `config.py`, sobrescreviveis por variavel de ambiente):
#
# | Variavel | Default |
# |---|---|
# | `DATABRICKS_CATALOG` | `nimbus` |
# | `DATABRICKS_SCHEMA` / `DATABRICKS_SILVER_SCHEMA` | `silver` |
# | `DATABRICKS_BRONZE_SCHEMA` | `bronze` |
# | `DATABRICKS_VOLUME` / `DATABRICKS_BRONZE_VOLUME` | `landing` |

# %%
# 10.1 — Diagnostico em 4 niveis: token, warehouse, schema no metastore, Volumes
!python tasks.py test-databricks

# %%
# 10.2 — Bronze: arquivo bruto -> Volume -> tabela no schema bronze
!python tasks.py upload-bronze --table tb_clientes

# %%
# 10.3 — Silver: parquet tipado -> Volume -> Delta -> metastore (com comentarios de coluna)
!python tasks.py upload-silver --table tb_clientes

# %%
# 10.4 — Ensaio sem efeito colateral
# !python tasks.py upload-silver --table tb_clientes --dry-run

# %% [markdown]
# Nomes de tabela que o Nimbus cria, para voce saber o que olhar no Catalog Explorer:
#
# - **Silver**: `nimbus.silver.<tabela>` (ex.: `nimbus.silver.tb_clientes`)
# - **Bronze**: uma tabela **por formato de origem** — `nimbus.bronze.<tabela>` (CSV), `<tabela>_json`, `<tabela>_txt`
# - **Quarentena**: mesmo padrao com prefixo — `nimbus.bronze.quarantine_<tabela>[_json|_txt]`
# - **Volume**: `/Volumes/nimbus/<schema>/landing/<tabela>/dat_ref=YYYY-MM-DD/...`, e o rejeito em `.../<tabela>/_quarantine/dat_ref=.../`
#
# A publicacao da quarentena vem **desligada por default** (`DATABRICKS_QUARANTINE_UPLOAD=false`): subir rejeito com PII e decisao de governanca, nao default de ferramenta.

# %% [markdown]
# ---
# # Parte 11 — LIMPEZA DAS TABELAS NO DATABRICKS
#
# > **Esta parte nao executa nada.** As celulas abaixo sao `raw`/texto: copie o SQL e rode no **SQL Editor** do workspace, ou em um notebook do Databricks. `DROP` e irreversivel — o objetivo aqui e uma execucao limpa antes do ensaio, nao uma rotina.
# >
# > Confira o catalogo/schema se voce sobrescreveu `DATABRICKS_CATALOG`, `DATABRICKS_SCHEMA` ou `DATABRICKS_BRONZE_SCHEMA` no `.env`.
#
# ### 11.1 — Inventario ANTES (sempre olhe primeiro)

# %% [raw]
# -- O que existe hoje
# SHOW SCHEMAS IN nimbus;
# SHOW TABLES  IN nimbus.silver;
# SHOW TABLES  IN nimbus.bronze;
# SHOW VOLUMES IN nimbus.silver;
# SHOW VOLUMES IN nimbus.bronze;
#
# -- Particoes ja ingeridas (util para explicar dat_ref na banca)
# LIST '/Volumes/nimbus/silver/landing/tb_clientes';
# LIST '/Volumes/nimbus/bronze/landing/tb_clientes';

# %% [markdown]
# ### 11.2 — Limpeza cirurgica (recomendada): so as tabelas do Nimbus
#
# Preserva schemas, Volumes e qualquer GRANT ja concedido.

# %% [raw]
# -- Silver
# DROP TABLE IF EXISTS nimbus.silver.tb_clientes;
# DROP TABLE IF EXISTS nimbus.silver.tb_transacoes;
# DROP TABLE IF EXISTS nimbus.silver.tb_contratos_credito;
#
# -- Bronze: uma tabela por formato de origem
# DROP TABLE IF EXISTS nimbus.bronze.tb_clientes;
# DROP TABLE IF EXISTS nimbus.bronze.tb_clientes_json;
# DROP TABLE IF EXISTS nimbus.bronze.tb_clientes_txt;
# DROP TABLE IF EXISTS nimbus.bronze.tb_transacoes;
# DROP TABLE IF EXISTS nimbus.bronze.tb_transacoes_json;
# DROP TABLE IF EXISTS nimbus.bronze.tb_transacoes_txt;
# DROP TABLE IF EXISTS nimbus.bronze.tb_contratos_credito;
# DROP TABLE IF EXISTS nimbus.bronze.tb_contratos_credito_json;
# DROP TABLE IF EXISTS nimbus.bronze.tb_contratos_credito_txt;
#
# -- Quarentena (prefixo quarantine_, no schema bronze)
# DROP TABLE IF EXISTS nimbus.bronze.quarantine_tb_clientes;
# DROP TABLE IF EXISTS nimbus.bronze.quarantine_tb_clientes_json;
# DROP TABLE IF EXISTS nimbus.bronze.quarantine_tb_clientes_txt;
# DROP TABLE IF EXISTS nimbus.bronze.quarantine_tb_transacoes;
# DROP TABLE IF EXISTS nimbus.bronze.quarantine_tb_transacoes_json;
# DROP TABLE IF EXISTS nimbus.bronze.quarantine_tb_transacoes_txt;
# DROP TABLE IF EXISTS nimbus.bronze.quarantine_tb_contratos_credito;
# DROP TABLE IF EXISTS nimbus.bronze.quarantine_tb_contratos_credito_json;
# DROP TABLE IF EXISTS nimbus.bronze.quarantine_tb_contratos_credito_txt;
#
# -- Confirmacao
# SHOW TABLES IN nimbus.silver;
# SHOW TABLES IN nimbus.bronze;

# %% [markdown]
# > Rodou cenario `breaking`/`non_breaking` e apareceram tabelas com esses sufixos (`tb_clientes_breaking`, etc.)? Adicione os `DROP` correspondentes, ou use a limpeza total abaixo.
#
# ### 11.3 — Arquivos nos Volumes
#
# `DROP TABLE` remove o objeto do metastore; os **arquivos** ficam no Volume (e o `read_files` do proximo CTAS pode reler particao antiga). Para uma execucao realmente limpa, remova as particoes.

# %% [raw]
# -- Inspecione antes de remover
# LIST '/Volumes/nimbus/bronze/landing/tb_clientes';
#
# -- Em notebook Databricks (Python), remocao recursiva das particoes:
# -- dbutils.fs.rm("/Volumes/nimbus/bronze/landing/tb_clientes", True)
# -- dbutils.fs.rm("/Volumes/nimbus/silver/landing/tb_clientes", True)
#
# -- Ou remova o Volume inteiro (recria no proximo upload):
# -- DROP VOLUME IF EXISTS nimbus.bronze.landing;
# -- DROP VOLUME IF EXISTS nimbus.silver.landing;

# %% [markdown]
# ### 11.4 — Limpeza total (opcao nuclear)
#
# Derruba tabelas, Volumes, funcoes de mascara e GRANTs dos dois schemas. Use so se o catalogo `nimbus` for exclusivo da PoC.

# %% [raw]
# -- CUIDADO: CASCADE apaga tudo dentro do schema, incluindo Volumes e arquivos.
# DROP SCHEMA IF EXISTS nimbus.silver CASCADE;
# DROP SCHEMA IF EXISTS nimbus.bronze CASCADE;
#
# -- O pipeline recria os schemas no proximo upload (CREATE SCHEMA IF NOT EXISTS),
# -- mas os Volumes precisam existir para o Files API:
# CREATE SCHEMA IF NOT EXISTS nimbus.silver;
# CREATE SCHEMA IF NOT EXISTS nimbus.bronze;
# CREATE VOLUME IF NOT EXISTS nimbus.silver.landing;
# CREATE VOLUME IF NOT EXISTS nimbus.bronze.landing;

# %% [markdown]
# ### 11.5 — Limpeza local do ledger (opcional)
#
# Se voce limpou o Databricks e quer que a demo de idempotencia comece do `FIRST_LOAD`, apague tambem o ledger local — senao a proxima run aparece como reprocessamento.

# %%
# Mude para True para apagar o ledger de idempotencia
CONFIRMO_LIMPEZA_LEDGER = False

import pathlib
led = pathlib.Path("data/metrics/_ingest_ledger.json")
if CONFIRMO_LIMPEZA_LEDGER and led.exists():
    led.unlink(); print("ledger removido — proxima carga sera FIRST_LOAD")
else:
    print("ledger preservado:", led.exists())

# %% [markdown]
# **O que este notebook NAO faz, de proposito:** executar `GRANT`, criar service principal, alterar permissao no workspace ou rodar `DROP` automatico. Tudo isso e decisao com alcada, nao efeito colateral de celula.

# %% [markdown]
# ---
# # Parte 12 — Ordem sugerida para a apresentacao
#
# A ordem de teste (acima) e diferente da ordem de **narrativa**. Na apresentacao o encadeamento que sustenta o argumento e este:
#
# | # | Passo | O que voce prova | Onde | ~min |
# |---|---|---|---|---|
# | 1 | Abrir `data/contracts/tb_clientes.yaml` | O Manifest e o acordo: dono, versao (manual), classificacao de sensibilidade, tipos, regras | editor | 2 |
# | 2 | `python tasks.py emit-grants --file data/contracts/tb_clientes.yaml` | O contrato e autoridade **ate a camada de permissao** — e o pipeline nao executa GRANT | Parte 9 | 1 |
# | 3 | Limpeza (local + Databricks) **feita antes**, fora da apresentacao | Execucao limpa sem gastar tempo de palco | Partes 1 e 11 | — |
# | 4 | `python run_pipeline.py --scenario baseline --format csv` -> exit 0 | Caminho feliz ponta a ponta | Parte 3 | 3 |
# | 5 | Mostrar o arquivo original no `bronze` e o Parquet no `silver` | Bronze preserva o recebido; Silver e tipada pelo Manifest | Parte 7 (console MinIO) | 2 |
# | 6 | `python tasks.py score` | Qualidade medida, decomposta em dimensoes | Parte 5 | 2 |
# | 7 | `python run_pipeline.py --scenario type_drift --format csv` -> exit 2 | O gate bloqueia de verdade e o exit code comunica bloqueio, nao crash | Parte 4 | 3 |
# | 8 | `ls data/quarantine` e as colunas `_reject_*` | Rejeito rastreavel, com PII mascarada, **fora** da Silver | Parte 4 | 3 |
# | 9 | Rodar a **mesma `dat_ref` duas vezes** -> `REPROCESS_IDENTICAL` | Idempotencia por SHA-256, e deteccao de arquivo corrigido | Parte 6 | 3 |
# | 10 | Catalog Explorer: tabela Silver com comentarios e tags | Publicacao governada no Databricks, nao `write` cru | Parte 10 | 3 |
# | 11 | Limitacoes, ditas por voce antes da pergunta | Maturidade de engenharia | — | 3 |
#
# **Total: ~25 min de demo.** Se o tempo apertar, corte os passos 6 e 10 — 4, 7, 8 e 9 sao o nucleo do argumento.
#
# ### Preparacao na vespera (nao faca isso no palco)
# 1. `python -m unittest discover -s tests -p "test_*.py"` -> 627 OK
# 2. Limpeza local (Parte 1) e Databricks (Parte 11)
# 3. `python tasks.py demo` -> MinIO de pe, buckets criados, console logado **no navegador, aba ja aberta**
# 4. `docker compose up --build` uma vez, para saber que sobe
# 5. `python tasks.py test-databricks` -> 4 niveis verdes
# 6. Promover o Manifest se estiver `DRAFT`: `python tasks.py validate-manifest --file ... --steward "Nome"`
#
# ### Limitacoes para dizer antes de perguntarem
# - **Ledger sem lock**: JSON reescrito inteiro, sem estado `RUNNING` — execucao sequencial, nao concorrente.
# - **Mascara determinística nao e anonimizacao**: quem tem o valor original recomputa o token `MASK:<hash>`.
# - **Autenticacao por PAT**: sem service principal; trocar depende de provisionamento, nao de codigo.
# - **`version` do Manifest e manual**: bump por diff de schema esta mapeado, nao implementado.
# - **Escala**: pandas/DuckDB em maquina unica — o desenho e o controle estao provados; volume produtivo pediria Spark.
# - **Gold vazia**: fora do escopo da PoC de ingestao.
#
# ### Perguntas que a banca faz, e a resposta curta
# - *"Reprocessar duplica dado?"* -> Nao: a identidade e `(tabela, dat_ref, formato)` e a mesma `dat_ref` sobrescreve a particao; o SHA-256 distingue reprocesso identico de arquivo corrigido.
# - *"E se chegar arquivo corrigido?"* -> `REPROCESS_MODIFIED`, `--skip-existing` e ignorado de proposito e o hash anterior fica no ledger para a divergencia continuar auditavel.
# - *"Quem autoriza a Silver?"* -> O gate, contra o Manifest `VALIDATED`; reprovado vai para quarentena e o exit code e 2.
# - *"Quem concede acesso?"* -> Nao o pipeline. Ele **deriva** o DDL do contrato; a concessao e do dono do dado.
# - *"Por que MinIO e nao S3?"* -> Mesma API S3; o codigo de storage e o mesmo e a troca e de endpoint/credencial.
# - *"Onde isso roda em producao?"* -> Prefect para orquestracao local da PoC; em producao, Control-M dispara o mesmo entrypoint — a pipeline nao depende do orquestrador.
