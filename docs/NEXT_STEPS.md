# Proximos Passos, Projeto Nimbus

> Substituido a cada sessao. O historico acumulado fica no CHANGELOG.md.

Ultima atualizacao: sprint `feature/manifest-version`. O contrato passou a ter versao derivada do
diff, com baseline em Git e lock file, bloqueio de promocao sem bump e historico gravado no
proprio Manifest. Suite em 661 testes.

---

## 1. Concluido nesta sprint

Versionamento do Manifest derivado do diff. O comando `python tasks.py manifest-version` compara o
contrato com o baseline (Git por padrao, lock file em `data/contracts/.lock/` como alternativa
dentro do container) e calcula o bump. Coluna removida, mudanca de tipo, `nullable` endurecido,
troca de chave primaria, mudanca na ordem das colunas, alteracao no formato da origem e tolerancia
restringida sao MAJOR. Coluna nova opcional, `nullable` afrouxado e tolerancia relaxada sao MINOR.
Descricao e metadado sao PATCH. Com `--apply`, o comando grava `version_history` no Manifest e
devolve para `DRAFT` um contrato que estava `VALIDATED`, porque o carimbo do Steward vale para a
versao que ele revisou. O `manifest_validator` recusa promover contrato alterado sem bump.

O que ja tinha sido concluido nas sprints anteriores e continua valendo:

- Metricas, relatorio e ledger gravados pelo storage configurado, local ou MinIO e S3, com o
  `show_metrics.py` lendo do mesmo backend.
- `MinIOStorage` com `MINIO_SECURE`, `MINIO_REGION`, `BUCKET_PREFIX` e `MINIO_CREATE_BUCKETS`. O
  pipeline foi exercitado em MinIO e em um segundo servidor S3-compativel com HTTPS.
- `GateBlocked`: o bloqueio de publicacao aparece como run Failed no Prefect e mantem o exit 2 na
  CLI. O `--no-prefect` executa as funcoes puras, sem servidor efemero.
- Idempotencia por `(tabela, dat_ref, formato)` mais SHA-256 do arquivo de entrada, com
  `FIRST_LOAD`, `REPROCESS_IDENTICAL` e `REPROCESS_MODIFIED`, `previous_sha256` guardado e
  `--skip-existing` respeitando conteudo modificado e carga `BLOCKED`.
- Geracao deterministica por `--dat-ref`, com semente vinda de `SHA-256(scenario|format|dat_ref)`,
  que e o que torna o caso de reprocessamento identico demonstravel.
- Cobertura dos componentes novos em `test_idempotency.py`, `test_quality_score.py`,
  `test_minio_storage.py`, `test_slm_metrics.py`, `test_prefect_flow.py`, `test_manifest_version.py`
  e determinismo em `test_data_generator.py`.
- Higiene do ambiente de demonstracao, com imagens pinadas
  (`quay.io/minio/minio:RELEASE.2025-09-07T16-13-09Z`, `ollama/ollama:0.32.15`,
  `python:3.11.15-slim-bookworm`) e credencial de object storage sem default. O compose usa
  `${MINIO_ACCESS_KEY:?...}`, o `config.py` deixa a variavel vazia e `get_storage()` levanta
  `RuntimeError` quando `USE_MINIO=true` sem credencial.
- Ordem entre gate e Silver: a carga reprovada e retirada da Silver e movida para a quarentena
  (`QUARANTINE_BLOCKED_SILVER=true`), preservando exit 2, metricas e motivo do bloqueio.
- Privacidade na quarentena: `DATABRICKS_QUARANTINE_UPLOAD` passou a `false` por padrao e
  `QUARANTINE_MASK_PII=true` mascara, nos rejeitos e dentro de `_reject_values`, as colunas marcadas
  `LGPD_SENSITIVE` no Manifest.
- `emit-grants`: `python tasks.py emit-grants --file <manifest>` deriva da classificacao do
  Manifest o `GRANT SELECT`, o `CREATE FUNCTION` de mascara (uma por tipo, porque o Unity Catalog
  exige que a mascara devolva o tipo da coluna) e os `ALTER COLUMN ... SET MASK`. O comando nao
  executa, nao autentica e nao abre conexao: a saida e um arquivo SQL revisavel.

---

## 2. Pendente, do maior retorno para o menor

### Registry de contratos

O bump ja e automatico e auditavel, mas o historico vive dentro do YAML e do lock. Nao ha registry
central, nao da para perguntar quem consome a versao 2.x de `tb_clientes` e nao existe notificacao
de consumidor quando sai um MAJOR. Falta tambem ligar o bump ao `check-manifest` do `_draft` e
publicar a versao vigente como metadado da tabela no Unity Catalog.

### IAM e aplicacao dos GRANTs

O `emit-grants` produz o DDL, mas aplicar continua sendo ato de quem tem alcada no workspace. O
pipeline nao cria service principal, nao concede permissao e nao administra identidade, e o acesso
ao Databricks e por PAT. Trocar PAT por identidade de servico depende de provisionamento de
plataforma, nao de codigo. Falta ainda revisar o DDL contra o dialeto do workspace alvo e ligar a
promocao do Manifest a abertura do pedido de acesso.

### Deteccao de dado sensivel

O mascaramento cobre exatamente o que o Manifest declara como `LGPD_SENSITIVE`. Coluna sensivel
nao declarada nao e mascarada, e a marcacao inicial proposta pela SLM e heuristica por nome, entao
nomes legados como `NRDOC`, `DDD_FONE` e `LOGRAD` escapam ate um Steward marca-los. Uma lista de
sinonimos no Manifest resolveria a maior parte dos casos sem prometer classificacao juridica. O
token `MASK:<hash>` tambem nao e anonimizacao juridica: ele e deterministico por desenho, para
preservar correlacao na investigacao do rejeito.

### Papel da SLM

O modelo local propoe metadado e nada mais. Toda saida nasce `[AI_METADATA_STATUS: DRAFT]` e so
vira contrato depois de `validate-manifest` com Steward nomeado. Isso e desenho de fluxo, nao
governanca de IA corporativa: falta politica de uso de modelo, registro de prompt e resposta e
revisao formal de vies antes de qualquer uso alem de PoC.

### Destino do Gold

Ou entra uma agregacao minima de verdade, como serie historica de score, ou o Gold sai da
narrativa e do compose e o projeto declara medallion ate a Silver, por escopo.

---

## 3. Planejado, fora do escopo desta PoC

### Databricks em workspace real

Codigo e testes cobrem Files API, CTAS STRING no Bronze e Parquet no Silver com mock. Falta
confirmar no workspace:

```sql
CREATE SCHEMA IF NOT EXISTS nimbus.bronze;
CREATE SCHEMA IF NOT EXISTS nimbus.silver;
CREATE VOLUME IF NOT EXISTS nimbus.bronze.landing;
CREATE VOLUME IF NOT EXISTS nimbus.silver.landing;
```

```bash
# .env: DATABRICKS_HOST, DATABRICKS_TOKEN, DATABRICKS_WAREHOUSE_ID
python tasks.py test-databricks
python tasks.py upload-bronze
python tasks.py upload-silver --dry-run
python tasks.py baseline
```

### AWS S3 em conta real

A compatibilidade de API, TLS, regiao e prefixo esta exercitada com dois servidores
S3-compativeis. Para AWS falta conta, IAM de escopo minimo, nome unico de bucket e controle de
custo, nao codigo. Receita e politica de exemplo em [STORAGE_S3.md](STORAGE_S3.md).

### Terraform

Provisionar catalog `nimbus`, schemas `bronze` e `silver`, Volumes `landing`, warehouse e
permissoes.

### Servico `ollama-init` no Docker

Separar o pull do modelo em um servico que roda uma vez e encerra antes do `nimbus` subir,
eliminando o timeout do healthcheck no primeiro boot.

### `MERGE INTO` para upsert incremental

Hoje cada particao `dat_ref` substitui a anterior com `overwrite=true`. Para dado real com PK
declarada no Manifest, o caminho e upsert via `MERGE INTO`.

### `DESCRIBE HISTORY` no dashboard

O `show_metrics.py` mostrando o historico Delta junto das metricas locais.

### Operacao

Retry com backoff, lock de execucao, estado `RUNNING` no ledger e atomicidade entre publicacao e
ledger. E o que falta para o projeto ser operavel por terceiros sem ressalva.

### Escala

Substituir o executor pandas por Spark caso o volume deixe de caber em single-node. O Manifest, o
roteamento de rejeito e o contrato de exit code sobrevivem a essa troca. Quem muda e o executor.
