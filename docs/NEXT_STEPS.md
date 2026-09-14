# Proximos Passos — Projeto Nimbus

> Substituido a cada sessao. Historico acumulado fica no CHANGELOG.md.

Ultima atualizacao: sprint `feature/expand-minio` — metricas/relatorios no storage configuravel,
portabilidade S3 (TLS, regiao, prefixo), idempotencia com SHA-256 do input, geracao deterministica,
correcao da ordem gate/Silver, privacidade na quarentena, `emit-grants` e versionamento do
Manifest por diff (661 testes).

---

## 1. Concluido nesta sprint

- Metricas, relatorio e ledger gravados pelo storage configurado (local ou MinIO/S3), e
  `show_metrics.py` lendo do mesmo backend.
- `MinIOStorage` com `MINIO_SECURE`, `MINIO_REGION`, `BUCKET_PREFIX` e `MINIO_CREATE_BUCKETS`;
  pipeline exercitado em MinIO e em um segundo servidor S3-compativel com HTTPS.
- `GateBlocked`: bloqueio de publicacao aparece como run **Failed** no Prefect, mantendo exit 2 na
  CLI; `--no-prefect` passou a executar as funcoes puras, sem servidor efemero.
- Idempotencia: `(tabela, dat_ref, formato)` + SHA-256 do arquivo de entrada, com
  `FIRST_LOAD` / `REPROCESS_IDENTICAL` / `REPROCESS_MODIFIED`, `previous_sha256` e `--skip-existing`
  respeitando conteudo modificado e carga `BLOCKED`.
- Geracao deterministica por `--dat-ref` (semente derivada de `SHA-256(scenario|format|dat_ref)`),
  o que torna o caso "reprocessamento identico" demonstravel.
- Cobertura dos componentes novos: `test_idempotency.py`, `test_quality_score.py`,
  `test_minio_storage.py`, `test_slm_metrics.py`, `test_prefect_flow.py` e determinismo em
  `test_data_generator.py`.
- Higiene do ambiente de demonstracao: imagens pinadas
  (`quay.io/minio/minio:RELEASE.2025-09-07T16-13-09Z`, `ollama/ollama:0.32.15`,
  `python:3.11.15-slim-bookworm`) e credencial de object storage sem default — compose com
  `${MINIO_ACCESS_KEY:?...}`, `config.py` com variavel vazia e `get_storage()` levantando
  `RuntimeError` quando `USE_MINIO=true` sem credencial.
- **Ordem gate/Silver**: carga reprovada e retirada da Silver e movida para a quarentena
  (`QUARANTINE_BLOCKED_SILVER=true`), preservando exit 2, metricas e motivo do bloqueio.
- **Privacidade na quarentena**: `DATABRICKS_QUARANTINE_UPLOAD` passou a `false` por padrao e
  `QUARANTINE_MASK_PII=true` mascara, nos rejeitos e dentro de `_reject_values`, as colunas
  marcadas `LGPD_SENSITIVE` no Manifest.
- **`emit-grants`**: `python tasks.py emit-grants --file <manifest>` deriva da classificacao do
  Manifest o `GRANT SELECT`, o `CREATE FUNCTION` de mascara (uma por tipo, porque o Unity Catalog
  exige que a mascara devolva o tipo da coluna) e os `ALTER COLUMN ... SET MASK`. **Nao executa,
  nao autentica e nao abre conexao** — a saida e um arquivo SQL revisavel.

- **Versionamento do Manifest derivado do diff.** `python tasks.py manifest-version` compara o
  contrato com o baseline (Git por padrao, lock file em `data/contracts/.lock/` como fallback no
  container) e calcula o bump: MAJOR para coluna removida, tipo, `nullable` endurecido, PK, ordem
  de colunas, formato da origem e tolerancia restringida; MINOR para coluna nova opcional,
  `nullable` afrouxado e tolerancia relaxada; PATCH para descricao e metadados. O `--apply` grava
  `version_history` no proprio Manifest e devolve contrato `VALIDATED` alterado para `DRAFT`. O
  `manifest_validator` recusa promover contrato alterado sem bump.

---

## 2. Pendente — maior retorno primeiro

**Registry de contratos.** O versionamento ja e automatico e auditavel no arquivo, mas o historico
vive dentro do proprio YAML e do lock: nao ha registry central, nem consulta "quem consome a versao
2.x de tb_clientes", nem notificacao de consumidor quando sai um MAJOR. Falta tambem ligar o bump
ao `check-manifest` do `_draft` e publicar a versao vigente como metadado da tabela no Unity
Catalog.

**IAM e aplicacao dos GRANTs.** O `emit-grants` produz o DDL; aplicar continua sendo ato de quem
tem alcada no workspace. O pipeline **nao** cria service principal, nao concede permissao e nao
administra identidade — o acesso ao Databricks e por PAT. Trocar PAT por identidade de servico
depende de provisionamento de plataforma, nao de codigo. Falta ainda: revisao do DDL contra o
dialeto do workspace-alvo e um processo que ligue a promocao do Manifest a abertura do pedido de
acesso.

**Deteccao de dado sensivel.** O mascaramento cobre exatamente o que o Manifest declara como
`LGPD_SENSITIVE` — coluna sensivel nao declarada nao e mascarada, e a marcacao inicial proposta
pela SLM e heuristica por nome, entao nomes legados (`NRDOC`, `DDD_FONE`, `LOGRAD`) escapam ate
um Steward marca-los. Uma lista de sinonimos no Manifest resolveria a maior parte dos casos sem
prometer classificacao juridica. O token `MASK:<hash>` tambem nao e anonimizacao juridica: e
deterministico por desenho, para preservar correlacao na investigacao do rejeito.

**Papel da SLM.** O modelo local propoe metadado e nada mais: toda saida nasce `[AI_METADATA_STATUS:
DRAFT]` e so vira contrato depois de `validate-manifest` com Steward nomeado. Isso e desenho, nao
governanca de IA corporativa — falta politica de uso de modelo, registro de prompt/resposta e
revisao formal de vies antes de qualquer uso alem de PoC.

**Decidir o destino do Gold.** Ou uma agregacao minima de verdade (serie historica de score, por
exemplo), ou remover Gold da narrativa e do compose e declarar "medallion ate Silver, por escopo".

---

## 3. Planejado (fora do escopo desta PoC)

**Databricks em workspace real.** Codigo e testes cobrem Files API, CTAS STRING no Bronze e Parquet
no Silver com mock. Falta confirmar no workspace:

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

**AWS S3 em conta real.** A compatibilidade de API, TLS, regiao e prefixo esta exercitada com dois
servidores S3-compativeis. Para AWS falta conta, IAM de escopo minimo, nome unico de bucket e
controle de custo — nao codigo. Receita e politica de exemplo em [STORAGE_S3.md](STORAGE_S3.md).

**Terraform.** Provisionar catalog `nimbus`, schemas `bronze`/`silver`, Volumes `landing`, warehouse
e permissoes.

**Fix Docker/Ollama — servico `ollama-init`.** Separar o pull do modelo em um servico que roda uma
vez e encerra antes do `nimbus` subir, eliminando o timeout do healthcheck no primeiro boot.

**`MERGE INTO` para upsert incremental.** Hoje cada particao `dat_ref` substitui a anterior com
`overwrite=true`. Para dado real com PK declarada no Manifest, upsert via `MERGE INTO`.

**`DESCRIBE HISTORY` no dashboard.** `show_metrics.py` mostrando o historico Delta junto das
metricas locais.

**Operacao.** Retry com backoff, lock de execucao, estado `RUNNING` no ledger e atomicidade entre
publicacao e ledger — o que falta para "operavel por terceiros" sem ressalva.

**Escala.** Substituir o executor pandas por Spark caso o volume deixe de caber em single-node. O
Manifest, o roteamento de rejeito e o contrato de exit code sobrevivem a essa troca; e o executor que
muda.
