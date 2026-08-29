# Próximos Passos — Projeto Nimbus

> Este arquivo é substituído a cada sessão de desenvolvimento, não acumula histórico. Para ver o que já foi feito, consulte o [CHANGELOG.md](CHANGELOG.md).

Última atualização: tipagem governada pelo Manifest no Silver (Sprint Parquet v2).

---

## Pendente da última sessão

Dois pontos identificados durante o desenvolvimento que ainda não foram resolvidos:

**Databricks — conexão não verificada.** O módulo `src/connectors/databricks_uploader.py` está implementado mas a conexão real nunca foi validada. Os problemas prováveis são: ausência de `DATABRICKS_WAREHOUSE_ID` no `.env` (a Statement Execution API exige o ID explícito no Community Edition), e o bloco `try/except` que engole erros de API silenciosamente tornando difícil diagnosticar falhas. Quando as credenciais estiverem disponíveis, os passos são: rodar `python tasks.py test-databricks` para validar o token, adicionar `DATABRICKS_WAREHOUSE_ID` ao `.env` e ao `config.py`, adicionar logs HTTP explícitos no uploader e implementar um modo `--dry-run` no `upload-silver` para simular o fluxo sem enviar dados.

**Docker + Ollama — inicialização quebrando.** O healthcheck do Ollama (15s intervalo, 10 retentativas, 30s start_period) dá aproximadamente 3 minutos para o serviço inicializar. Na primeira execução, o download do modelo pode exceder esse tempo, fazendo o container `nimbus` nunca subir. Solução imediata: fazer o pull do modelo manualmente antes do `docker compose up`:
```bash
docker run --rm -v ollama_models:/root/.ollama ollama/ollama pull phi3.5
docker compose up
```
Solução definitiva: separar o pull em um serviço `ollama-init` no `docker-compose.yml` que roda uma vez e encerra antes do `nimbus` subir.

---

## Planejado

**Databricks — rastreabilidade completa.** Com o Parquet do Silver agora carregando metadata do Manifest no footer (`nimbus.schema_source`, `nimbus.table`, etc.), o próximo passo natural é fazer o Databricks ler esse metadata ao registrar a tabela e popular os comentários das colunas no Unity Catalog automaticamente. Isso fecha o ciclo: o Data Steward valida no Nimbus, o Databricks herda a documentação sem digitação extra.

**Sprint C — Terraform.** Com Docker, Parquet e integração Databricks implementados, o Terraform tem infraestrutura concreta para codificar. O provider `databricks` funciona com Community Edition — provisionar workspace, configurar MinIO como external location, criar schemas no metastore e definir permissões de acesso.

**Delta Lake no Silver.** O Parquet com tipagem governada é a base. Delta Lake adiciona versionamento nativo — cada execução do Nimbus cria uma nova versão da tabela, permitindo `DESCRIBE HISTORY` no Databricks para auditar todas as execuções anteriores. A biblioteca `deltalake` (Python puro, sem Spark) escreve Delta em qualquer storage S3-compatível, incluindo o MinIO já presente no stack.

**CLI unificada para extração de Manifest.** O `src/manifest/extract.py` foi criado como roteador mas ainda não está exposto como comando principal no `tasks.py`. O comando `python tasks.py extract --file <path> --table <nome>` com detecção automática de formato completaria o fluxo de onboarding de novas tabelas.

**Série histórica de quality score.** As métricas ficam em JSON por execução, o que dificulta ver a tendência de uma tabela ao longo do tempo. Uma tabela Gold consolidando o histórico tornaria o `show_metrics.py` mais útil para acompanhamento contínuo.

---

## Como atualizar este arquivo

No início de cada sessão, leia este arquivo. No final, substitua-o com o que ficou pendente e o que está planejado. Não acrescente — substitua. O histórico acumulado fica no CHANGELOG.md.
