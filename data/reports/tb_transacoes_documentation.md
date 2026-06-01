# Dicionário Técnico da Tabela `tb_transacoes`

## Visão Geral

A tabela `tb_transacoes` registra todas as movimentações financeiras por canal, conforme descrito no manifesto. Ela é gerida pela equipe `squad-transacoes` e está atualmente em versão 2.3.1. O sistema de origem é o `SWITCH_TRANSACIONAL`, que fornece dados em formato CSV com codificação UTF-8.

### Contexto de Negócio

O propósito principal da tabela é documentar todas as transações financeiras realizadas através dos diversos canais de atendimento do banco. A coluna `fl_suspeita` indica se uma transação está sendo analisada pelo motor antifraude, enquanto a coluna `cd_estabelecimento` pode ser nula para compras online não identificadas.

### Regulamentações e Classificação de Dados

- **Tags Regulatórias**: BACEN_4658, PCI_DSS
- **Classificação de Dados**: Confidencial
- **Período de Retenção**: 7 anos

## Colunas da Tabela

### `id_transacao`
- **Tipo**: String (VARCHAR)
- **Nullable**: Não
- **Descrição**: UUID da transação, gerado pelo switch transacional no momento da operação.
- **Comportamento Esperado**: Valor único para cada transação. No entanto, foram observadas duplicatas em 0.99% dos registros.

### `cd_cliente`
- **Tipo**: String (VARCHAR)
- **Nullable**: Não
- **Descrição**: Referência ao cliente na tabela `tb_clientes`.
- **Comportamento Esperado**: Valor único por transação. A coluna apresenta alta frequência de valores repetidos, indicando múltiplas transações por cliente.

### `dt_transacao`
- **Tipo**: String (VARCHAR)
- **Nullable**: Não
- **Descrição**: Data da transação no fuso horário America/Sao_Paulo.
- **Comportamento Esperado**: Deve ser um valor de data válido. A coluna está atualmente como VARCHAR, o que pode indicar inconsistências na formatação.

### `vl_transacao`
- **Tipo**: String (VARCHAR)
- **Nullable**: Não
- **Descrição**: Valor em BRL da transação. Positivo para débitos e negativo para estornos.
- **Comportamento Esperado**: Deve ser um valor numérico. A coluna está atualmente como VARCHAR, o que pode causar problemas de validação.

### `tp_transacao`
- **Tipo**: String (VARCHAR)
- **Nullable**: Não
- **Descrição**: Tipo da operação. Dominio: COMPRA, SAQUE, TED, PIX, PAGAMENTO_BOLETO, ESTORNO.
- **Comportamento Esperado**: Deve conter apenas os valores do domínio especificado.

### `cd_estabelecimento`
- **Tipo**: String (VARCHAR)
- **Nullable**: Sim
- **Descrição**: CNPJ do estabelecimento. Pode ser nulo para compras online não identificadas (~6%).
- **Comportamento Esperado**: Deve conter valores numéricos válidos de CNPJ ou ser nulo conforme descrito.

### `fl_suspeita`
- **Tipo**: String (VARCHAR)
- **Nullable**: Não
- **Descrição**: Flag do motor antifraude. True indica transação em análise (~4% do volume).
- **Comportamento Esperado**: Deve ser um valor booleano (`True` ou `False`). A coluna está atualmente como VARCHAR

---
> **[AI_METADATA_STATUS: DRAFT]**