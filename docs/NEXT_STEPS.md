# Próximos Passos — Projeto Nimbus

> Este arquivo é substituído a cada sessão de desenvolvimento, não acumula histórico. Para ver o que já foi feito, consulte o [CHANGELOG.md](CHANGELOG.md).

Última atualização: reestruturação de documentação e rebrand para Projeto Nimbus.

---

## Pendente da última sessão

Nada ficou aberto. A reestruturação de documentação foi concluída integralmente: pasta `docs/` criada, `tasks.py` entregue, README reescrito, todos os arquivos `.md` revisados com linguagem natural, rebrand aplicado em código e documentação.

---

## Planejado

Nenhuma priorização formal foi feita ainda. Os itens abaixo foram identificados ao longo do desenvolvimento como candidatos naturais para a próxima sprint.

**CLI unificada para extração de Manifest.** Hoje cada extrator tem seu próprio módulo com interface ligeiramente diferente. Uma interface única com detecção automática de formato simplificaria o uso: `python -m src.manifest.extract --file X` detectaria se é SAS7BDAT, CSV, JSON ou Fixed-Width e rotearia para o extrator correto. O parâmetro `--format auto` também seria útil no `tasks.py`.

**Série histórica de quality score.** As métricas de qualidade ficam em JSON por execução, o que permite consultar um run específico mas dificulta ver a tendência de uma tabela ao longo do tempo. Uma tabela Gold consolidando o histórico de scores por tabela tornaria o `show_metrics.py` mais útil para acompanhamento contínuo.

**Parâmetro `auto_extract` no Prefect.** A task `JOB-DM-000-EXTRACT` existe e funciona, mas precisa ser disparada manualmente. Adicionar `auto_extract: true` no `prefect.yaml` permitiria que deployments agendados gerassem o Manifest automaticamente quando um arquivo novo chegar sem contrato associado.

**Validação do backend MinIO end-to-end.** O `MinIOStorage` está implementado e testado unitariamente, mas nunca foi validado em um fluxo completo com o Docker rodando. Quando houver um ambiente com Docker disponível, esse teste precisa ser feito antes de qualquer apresentação que use o MinIO como argumento.

**Cobertura de testes para integração com Prefect.** Os testes do `prefect_flow.py` usam `--no-prefect`, o que valida a lógica mas não a integração real com o servidor. Um conjunto de testes de integração que suba um servidor Prefect local para o teste completaria a cobertura.

---

## Como atualizar este arquivo

No início de cada sessão, leia este arquivo. No final, substitua-o com o que ficou pendente e o que está planejado para a próxima. Não acrescente — substitua. O histórico acumulado fica no CHANGELOG.md.
