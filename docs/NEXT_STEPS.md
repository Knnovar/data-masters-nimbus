# Próximos Passos — Projeto Nimbus

> Este arquivo é substituído a cada sessão de desenvolvimento, não acumula histórico. Para ver o que já foi feito, consulte o [CHANGELOG.md](CHANGELOG.md).

Última atualização: deploy Docker one-click com suporte a Parquet e integração Databricks.

---

## Pendente da última sessão

Nada ficou aberto. O deploy Docker foi concluído com os três serviços (nimbus, ollama, minio), o `entrypoint.sh` com a sequência completa de inicialização, o `.env.example` e a atualização do `config.py` para ler variáveis de ambiente.

---

## Planejado

**Sprint C — Terraform.** Com o ambiente Docker funcionando e a integração Databricks implementada, o próximo passo natural é codificar a infraestrutura como código. O provider `databricks` do Terraform funciona com Community Edition — provisionar o workspace, configurar o MinIO como external location, criar os schemas no metastore e definir permissões de acesso às tabelas Delta. O `terraform.tfstate` fica local para a PoC e migra para backend remoto quando o projeto evoluir para ambiente compartilhado.

**Delta Lake no Silver.** O Parquet puro no Silver funciona bem, mas o Delta Lake adiciona versionamento nativo — cada execução do Nimbus criaria uma nova versão da tabela, permitindo `DESCRIBE HISTORY` no Databricks para ver todas as execuções anteriores. A evolução de Parquet para Delta é uma extensão pequena: a biblioteca `deltalake` (Python puro, sem Spark) escreve tabelas Delta em qualquer storage S3-compatível, incluindo o MinIO já presente no stack.

**CLI unificada para extração de Manifest.** O `src/manifest/extract.py` foi criado como roteador mas ainda não está exposto no `tasks.py` de forma unificada. O comando `python tasks.py extract --file <path> --table <nome>` com detecção automática de formato tornaria o fluxo de onboarding de novas tabelas mais simples.

**Série histórica de quality score.** As métricas ficam em JSON por execução, o que dificulta ver a tendência de uma tabela ao longo do tempo. Uma tabela Gold consolidando o histórico de scores tornaria o `show_metrics.py` mais útil para acompanhamento contínuo.

**Testes de integração Docker.** Hoje os testes unitários cobrem a lógica de negócio, mas não validam o stack Docker completo. Um teste de smoke que sobe o `docker-compose.yml` em CI e verifica que o pipeline conclui com sucesso completaria a cobertura.

---

## Como atualizar este arquivo

No início de cada sessão, leia este arquivo. No final, substitua-o com o que ficou pendente e o que está planejado para a próxima. Não acrescente — substitua. O histórico acumulado fica no CHANGELOG.md.
