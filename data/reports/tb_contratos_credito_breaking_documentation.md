# Dicionário Técnico da Tabela `tb_contratos_credito_breaking`

## Descrição Geral

A tabela `tb_contratos_credito_breaking` contém informações sobre contratos de produtos de crédito, tanto ativos quanto encerrados. Ela é gerida pela equipe `squad-credito` e está na versão 3.0.0.

## Colunas da Tabela

### `id_contrato`
- **Propósito de Negócio**: Identificador único para cada contrato.
- **Tipo Esperado**: String
- **Comportamento Esperado**: Não nulo, deve ser único em toda a tabela (chave primária).
- **Anomalias Observadas**: Nenhuma anomalia detectada; todos os valores são únicos e não há registros nulos.

### `cd_cliente`
- **Propósito de Negócio**: Código identificador do cliente associado ao contrato.
- **Tipo Esperado**: String
- **Comportamento Esperado**: Não nulo, pode haver duplicatas indicando múltiplos contratos para um mesmo cliente.
- **Anomalias Observadas**: Alta frequência de valores repetidos (4 e 3 ocorrências), sugerindo que alguns clientes têm múltiplos contratos.

### `dt_contrato`
- **Propósito de Negócio**: Data em que o contrato foi estabelecido.
- **Tipo Esperado**: Date
- **Comportamento Esperado**: Não nulo, deve ser uma data válida.
- **Anomalias Observadas**: Tipo de dado está como `VARCHAR`, indicando um problema na conversão ou armazenamento. Além disso, há valores repetidos.

### `vl_limite`
- **Propósito de Negócio**: Valor limite do crédito disponível no contrato.
- **Tipo Esperado**: Float
- **Comportamento Esperado**: Não nulo, deve ser um número positivo.
- **Anomalias Observadas**: Tipo de dado está como `VARCHAR`, indicando um problema na conversão ou armazenamento.

### `vl_utilizado`
- **Propósito de Negócio**: Valor do crédito já utilizado pelo cliente.
- **Tipo Esperado**: Float
- **Comportamento Esperado**: Não nulo, deve ser um número positivo e não superior ao valor limite (`vl_limite`).
- **Anomalias Observadas**: Tipo de dado está como `VARCHAR`, indicando um problema na conversão ou armazenamento.

### `tp_produto`
- **Propósito de Negócio**: Tipo do produto de crédito (ex: cheque especial, financiamento veículo).
- **Tipo Esperado**: String
- **Comportamento Esperado**: Não nulo.
- **Anomalias Observadas**: Nenhuma anomalia detectada; os valores são consistentes com tipos esperados.

### `cd_status`
- **Propósito de Negócio**: Status atual do contrato (ex: renegociado, em atraso).
- **Tipo Esperado**: String
- **Comportamento Esperado**: Não nulo.
- **Anomalias Observadas**: Nenhuma anomalia detectada; os valores são consistentes com status esperados.

### `dt_vencimento`
- **Propósito de Negócio**: Data em que o contrato vence ou deve ser totalmente pago.
- **Tipo Esperado**: Date
- **Comportamento Esperado**: Não nulo, deve ser uma data válida.
- **Anomalias Observadas**: Tipo de dado está como `VARCHAR`, indicando um problema na conversão ou armazenamento. Além disso, há valores repetidos.

### `nr_parcelas`
- **Propósito de Negó

---
> **[AI_METADATA_STATUS: DRAFT]**