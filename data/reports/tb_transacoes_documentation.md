# Dicionário Técnico da Tabela `tb_transacoes`

## Visão Geral

A tabela `tb_transacoes` registra todas as movimentações financeiras realizadas através de diferentes canais de atendimento do banco. Ela é gerida pela equipe `squad-transacoes` e está atualmente em versão `2.3.1`. A tabela é alimentada por um sistema chamado `SWITCH_TRANSACIONAL` e está formatada em CSV com codificação UTF-8. As atualizações são feitas de forma event-driven.

### Contexto de Negócio

- **Registro de Movimentações**: A tabela captura todas as transações financeiras, incluindo compras, saques, TEDs, PIXs, pagamentos de boletos e estornos.
- **Flag de Transações Suspeitas**: O campo `fl_suspeita` indica se uma transação está sendo analisada pelo motor antifraude.
- **Estabelecimento**: O campo `cd_estabelecimento` pode ser nulo para compras online não identificadas, o que ocorre em aproximadamente 6% das transações.

### Considerações de Conformidade

- **Regulatory Tags**: A tabela está sujeita às normas `BACEN_4658` e `PCI_DSS`, o que implica requisitos rigorosos de segurança e privacidade de dados.
- **Classificação de Dados**: Os dados são classificados como confidenciais e têm uma retenção de 7 anos.

## Colunas

### `id_transacao`

- **Tipo**: String
- **Descrição**: UUID da transação, gerado pelo switch transacional no momento da operação.
- **Comportamento Esperado**: Não nulo, deve ser único para cada transação.
- **Anomalias**: 2% das transações têm IDs duplicados, o que viola a regra de unicidade.

### `cd_cliente`

- **Tipo**: String
- **Descrição**: Referência ao cliente em `tb_clientes`.
- **Comportamento Esperado**: Não nulo, deve corresponder a um cliente existente.
- **Anomalias**: Apenas 487 clientes únicos em 2030 transações, indicando alta frequência de transações por cliente.

### `dt_transacao`

- **Tipo**: String (deveria ser Date)
- **Descrição**: Data da transação no fuso horário America/Sao_Paulo.
- **Comportamento Esperado**: Não nulo, deve estar no formato correto de data.
- **Anomalias**: Tipo de dado incorreto (VARCHAR), o que pode causar problemas de análise e validação.

### `vl_transacao`

- **Tipo**: String (deveria ser Float)
- **Descrição**: Valor em BRL. Positivo para débitos, negativo para estornos.
- **Comportamento Esperado**: Não nulo, deve representar valores monetários válidos.
- **Anomalias**: Tipo de dado incorreto (VARCHAR), o que pode afetar cálculos financeiros.

### `tp_transacao`

- **Tipo**: String
- **Descrição**: Tipo da operação. Domínio: COMPRA, SAQUE, TED, PIX, PAGAMENTO_BOLETO, ESTORNO.
- **Comportamento Esperado**: Não nulo, deve estar dentro do domínio especificado.
- **Anomalias**: Nenhuma anomalia observada.

### `cd_estabelecimento`

- **Tipo**: String
- **Descrição**: CNPJ do estabelecimento. Nulo para compras online não identificadas (~6%).
- **Comportamento Esperado**: Pode ser nulo, mas deve ser um CNPJ válido quando presente.
- **Anomalias**: 6.5% de valores nulos, ligeiramente acima do esperado (~6%).

### `fl_suspeita`

- **Tipo**: String (deveria ser Boolean)
- **Descrição**: Flag do motor antifraude. True indica transação em análise (~4% do volume).
- **Comportamento Esperado**: Não nulo, deve ser um valor booleano.
- **Anomalias**: Tipo de dado incorreto (VARCHAR), o que pode afetar a análise de fraude.

### `cd_canal`

- **Tipo**: String
- **Descrição**: Canal de origem. Domínio: APP, INTERNET, AGENCIA, ATM, POS.
- **Comportamento Esperado**: Não nulo, deve estar dentro do domínio especificado.
- **Anomalias**: Nenhuma anomalia observada.

## Pontos de Atenção

1. **Duplicatas em `id_transacao`**: A presença de IDs duplicados viola a regra de unicidade e pode causar inconsistências nos registros de transações.
2. **Tipos de Dados Incorretos**: As colunas `dt_transacao`, `vl_transacao` e `fl_suspeita` têm tipos de dados incorretos, o que pode afetar a integridade e a análise dos dados.
3. **Percentual de Nulos em `cd_estabelecimento`**: O percentual de valores nulos está ligeiramente acima do esperado, o que pode indicar problemas na identificação de estabelecimentos para compras online.
4. **Conformidade Regulatória**: A tabela deve ser gerida com cuidado para garantir a conformidade com as normas `BACEN_4658` e `PCI_DSS`, especialmente considerando a classificação de dados como confidencial.

---

> **[AI_METADATA_STATUS: DRAFT]** — Documentação gerada por SLM. Requer validação humana pelo Data Steward responsável antes de uso em produção.