# Dicionário Técnico da Tabela `tb_contratos_credito`

## Descrição Geral

A tabela `tb_contratos_credito` armazena informações sobre contratos de produtos de crédito, tanto ativos quanto encerrados. É gerida pela equipe `squad-credito` e está na versão 3.0.0.

## Colunas da Tabela

### `id_contrato`
- **Propósito de Negócio**: Identificador único para cada contrato.
- **Tipo**: String
- **Comportamento Esperado**: Não nulo, deve ser único em toda a tabela (chave primária).
- **Observações**: Nenhum valor nulo e todos os valores são únicos conforme as estatísticas.

### `cd_cliente`
- **Propósito de Negócio**: Código identificador do cliente associado ao contrato.
- **Tipo**: String
- **Comportamento Esperado**: Não nulo, mas pode haver clientes com múltiplos contratos.
- **Observações**: 87% dos códigos são únicos, indicando que alguns clientes têm mais de um contrato.

### `dt_contrato`
- **Propósito de Negócio**: Data em que o contrato foi estabelecido.
- **Tipo**: String (esperado ser Date)
- **Comportamento Esperado**: Não nulo, deve representar datas válidas.
- **Observações**: O tipo de dado é VARCHAR, mas deveria ser DATE. Há 18 valores duplicados.

### `vl_limite`
- **Propósito de Negócio**: Valor limite do crédito disponível no contrato.
- **Tipo**: String (esperado ser Float)
- **Comportamento Esperado**: Não nulo, deve representar um valor monetário positivo.
- **Observações**: O tipo de dado é VARCHAR, mas deveria ser FLOAT. Valores variam entre 1211.66 e 99891.53.

### `vl_utilizado`
- **Propósito de Negócio**: Valor atualmente utilizado do crédito disponível no contrato.
- **Tipo**: String (esperado ser Float)
- **Comportamento Esperado**: Não nulo, deve representar um valor monetário positivo.
- **Observações**: O tipo de dado é VARCHAR, mas deveria ser FLOAT. Valores variam entre 92.24 e 109174.48.

### `tp_produto`
- **Propósito de Negócio**: Tipo do produto de crédito (ex: cheque especial, financiamento).
- **Tipo**: String
- **Comportamento Esperado**: Não nulo.
- **Observações**: Cinco tipos únicos de produtos são observados.

### `cd_status`
- **Propósito de Negócio**: Status atual do contrato (ex: renegociado, em atraso).
- **Tipo**: String
- **Comportamento Esperado**: Não nulo.
- **Observações**: Quatro status únicos são observados.

### `dt_vencimento`
- **Propósito de Negócio**: Data de vencimento do contrato.
- **Tipo**: String (esperado ser Date)
- **Comportamento Esperado**: Não nulo, deve representar datas válidas.
- **Observações**: O tipo de dado é VARCHAR, mas deveria ser DATE. Há 19 valores duplicados.

### `nr_parcelas`
- **Propósito de Negócio**: Número total de parcelas do contrato.
- **Tipo**: String (esperado ser Integer)
- **Comportamento Esperado**: Não nulo, deve representar um número inteiro positivo.
- **Observações**: O tipo de dado é VARCHAR, mas deveria ser INTEGER. Val

---
> **[AI_METADATA_STATUS: DRAFT]**