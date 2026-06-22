# Próximos Passos — Projeto Nimbus

> Este arquivo é **substituído a cada sessão de desenvolvimento**, não
> acumula histórico. Para ver o que já foi feito, consulte
> [CHANGELOG.md](CHANGELOG.md).

Última atualização: reestruturação de documentação (rebrand para Projeto Nimbus).

---

## Pendente da última sessão

Nenhuma pendência aberta — a reestruturação de documentação foi concluída
nesta sessão: pasta `docs/` criada, `tasks.py` entregue como alternativa
cross-platform ao Makefile, README reescrito, rebrand aplicado.

---

## Planejado — Sprint 3 (candidatos)

Nenhuma decisão de priorização tomada ainda. Candidatos identificados ao
longo do desenvolvimento:

### Manifest e Extração
- CLI unificada com auto-detecção de formato:
  `python -m src.manifest.extract --file X --format auto`
- Parâmetro `auto_extract: true` no `prefect.yaml` para acionar
  `JOB-DM-000-EXTRACT` automaticamente em deployments agendados

### Métricas
- Tabela Gold consolidada de métricas (hoje fica apenas em JSON por run)
- Série histórica de quality score por tabela ao longo do tempo

### Infraestrutura
- Validar backend `MinIOStorage` end-to-end quando Docker estiver
  disponível no ambiente de desenvolvimento
- Testar `prefect_flow.py` com servidor Prefect real (hoje validado
  apenas via `--no-prefect`)

### Migração
- Nenhuma ação iniciada rumo a Azure/Databricks — projeto segue como PoC
  local. Plano completo documentado em [MIGRATION_PLAN.md](MIGRATION_PLAN.md)
  para quando houver aprovação de avançar.

---

## Como usar este arquivo

Ao final de cada sessão de desenvolvimento, este arquivo deve ser
**reescrito** (não anexado) com:

1. O que ficou pendente desta sessão, se houver
2. O que está planejado, com prioridade se já definida
3. Decisões de negócio aguardando resposta, se houver

Decisões já tomadas e resolvidas saem deste arquivo e viram entrada no
[CHANGELOG.md](CHANGELOG.md).
