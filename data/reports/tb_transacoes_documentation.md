# Dicionário Técnico da Tabela `tb_transacoes`

## Descrição Geral

A tabela `tb_transacoes` armazena informações sobre movimentações financeiras realizadas através de diversos canais de atendimento do banco. Ela é gerida pela equipe `squad-transacoes` e está na versão 2.3.1.

## Colunas da Tabela

### `id_transacao`
- **Propósito de Negócio**: Identificador único para cada transação.
- **Tipo**: String (VARCHAR)
- **Comportamento Esperado**: Não deve conter valores nulos e é a chave primária da tabela.
- **Anomalias Observadas**:
  - Existem duplicatas: 2 registros com o mesmo `id_transacao`.
  
### `cd_cliente`
- **Propósito de Negócio**: Código identificador do cliente que realizou a transação.
- **Tipo**: String (VARCHAR)
- **Comportamento Esperado**: Não deve conter valores nulos.
- **Anomalias Observadas**:
  - Alta concentração de clientes: alguns códigos aparecem repetidamente, indicando múltiplas transações por cliente.

### `dt_transacao`
- **Propósito de Negócio**: Data em que a transação foi realizada.
- **Tipo**: String (VARCHAR) — esperado como tipo Date
- **Comportamento Esperado**: Não deve conter valores nulos.
- **Anomalias Observadas**:
  - Datas futuras presentes, como "2024-02-28", que podem ser erros de entrada.

### `vl_transacao`
- **Propósito de Negócio**: Valor monetário da transação.
- **Tipo**: String (VARCHAR) — esperado como tipo Float
- **Comportamento Esperado**: Não deve conter valores nulos.
- **Anomalias Observadas**:
  - Tipo de dado incorreto: armazenado como VARCHAR ao invés de FLOAT.

### `tp_transacao`
- **Propósito de Negócio**: Tipo da transação (ex.: saque, pagamento).
- **Tipo**: String (VARCHAR)
- **Comportamento Esperado**: Não deve conter valores nulos.
- **Anomalias Observadas**:
  - Limitada variedade de tipos de transações.

### `cd_estabelecimento`
- **Propósito de Negócio**: Código identificador do estabelecimento onde a transação ocorreu.
- **Tipo**: String (VARCHAR)
- **Comportamento Esperado**: Pode conter valores nulos, com tolerância de 6.5% de nulidade.
- **Anomalias Observadas**:
  - Tipo de dado incorreto: armazenado como VARCHAR ao invés de um tipo numérico.

### `fl_suspeita`
- **Propósito de Negócio**: Indica se a transação é suspeita (True/False).
- **Tipo**: String (VARCHAR) — esperado como tipo Boolean
- **Comportamento Esperado**: Não deve conter valores nulos.
- **Anomalias Observadas**:
  - Tipo de dado incorreto: armazenado como VARCHAR ao invés de BOOLEAN.

### `cd_canal`
- **Propósito de Negócio**: Canal através do qual a transação foi realizada (ex.: ATM, APP).
- **Tipo**: String (VARCHAR)
- **Comportamento Esperado**: Não deve conter valores nulos.
- **Anomalias Observadas**:
  - Limitada variedade de canais.

## Chaves de Negócio

### `id_transacao`
- **Implicações**: Como chave primária, deve

---
> **[AI_METADATA_STATUS: DRAFT]**