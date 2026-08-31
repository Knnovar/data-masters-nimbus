# Dicionário Técnico da Tabela `tb_transacoes`

## Visão Geral

A tabela `tb_transacoes` registra todas as movimentações financeiras realizadas por diferentes canais de atendimento. Ela é gerida pela equipe `squad-transacoes` e está atualmente em versão `2.3.1`. O sistema fonte é o `SWITCH_TRANSACIONAL`, que gera arquivos em formato CSV com codificação UTF-8. A atualização dos dados é event-driven, e o contato para questões relacionadas é `squad-transacoes@banco.com.br`.

### Contexto de Negócio

O propósito da tabela é registrar todas as transações financeiras por canal. O campo `fl_suspeita` indica se uma transação está sendo analisada pelo motor antifraude. O campo `cd_estabelecimento` pode ser nulo para compras online não identificadas, o que ocorre em aproximadamente 6% dos casos.

### Regulamentações e Classificação de Dados

A tabela está sujeita às regulamentações `BACEN_4658` e `PCI_DSS`, com classificação de dados como confidencial. Os dados devem ser retidos por 7 anos.

## Colunas da Tabela

### `id_transacao`

- **Propósito de Negócio**: Identificador único de cada transação.
- **Tipo**: `string`
- **Comportamento Esperado**: Não nulo, é a chave primária da tabela.
- **Anomalias**: Nenhuma observada. Apenas 2 duplicatas foram encontradas.

### `cd_cliente`

- **Propósito de Negócio**: Referência ao cliente na tabela `tb_clientes`.
- **Tipo**: `string`
- **Comportamento Esperado**: Não nulo.
- **Anomalias**: Nenhuma observada.

### `dt_transacao`

- **Propósito de Negócio**: Data da transação no fuso horário America/Sao_Paulo.
- **Tipo**: `date`
- **Comportamento Esperado**: Não nulo.
- **Anomalias**: Nenhuma observada.

### `vl_transacao`

- **Propósito de Negócio**: Valor da transação em BRL. Positivo para débitos, negativo para estornos.
- **Tipo**: `float`
- **Comportamento Esperado**: Não nulo.
- **Anomalias**: Nenhuma observada.

### `tp_transacao`

- **Propósito de Negócio**: Tipo da operação. Domínio: COMPRA, SAQUE, TED, PIX, PAGAMENTO_BOLETO, ESTORNO.
- **Tipo**: `string`
- **Comportamento Esperado**: Não nulo.
- **Anomalias**: Nenhuma observada.

### `cd_estabelecimento`

- **Propósito de Negócio**: CNPJ do estabelecimento. Pode ser nulo para compras online não identificadas.
- **Tipo**: `string`
- **Comportamento Esperado**: Pode ser nulo, com aproximadamente 6% de valores nulos.
- **Anomalias**: Nenhuma observada além do comportamento esperado.

### `fl_suspeita`

- **Propósito de Negócio**: Flag do motor antifraude. True indica transação em análise.
- **Tipo**: `boolean`
- **Comportamento Esperado**: Não nulo.
- **Anomalias**: Nenhuma observada.

### `cd_canal`

- **Propósito de Negócio**: Canal de origem. Domínio: APP, INTERNET

---
> **[AI_METADATA_STATUS: DRAFT]**