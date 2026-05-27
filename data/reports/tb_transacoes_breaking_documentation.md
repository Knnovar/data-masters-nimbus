# Dicionário Técnico da Tabela `tb_transacoes_breaking`

## Descrição Geral

A tabela `tb_transacoes_breaking` registra movimentações financeiras realizadas através de diversos canais de atendimento do banco. Ela é gerida pela equipe responsável pelas transações (squad-transacoes) e está na versão 2.3.1.

## Colunas da Tabela

### `id_transacao`
- **Propósito de Negócio**: Identificador único para cada transação.
- **Tipo Esperado**: String
- **Comportamento Esperado**: Não deve conter valores nulos e ser única em toda a tabela (chave primária).
- **Anomalias Observadas**:
  - Existem duplicatas: `3bc339e0-f2aa-4d33-883b-302d2dd05cfe`, `11698d09-c47f-4130-8e7f-ce7c39271a77` e `3d751a35-70b3-4d09-8ae7-fef53c7f9903` aparecem duas vezes.
  
### `cd_cliente`
- **Propósito de Negócio**: Código identificador do cliente que realizou a transação.
- **Tipo Esperado**: String
- **Comportamento Esperado**: Não deve conter valores nulos.
- **Anomalias Observadas**:
  - Alta concentração em poucos códigos: `48E5DA3F-4B9`, `08B6AAAB-0CF` e `8536384A-BF4` aparecem com frequência elevada.

### `dt_transacao`
- **Propósito de Negócio**: Data em que a transação foi realizada.
- **Tipo Esperado**: Date
- **Comportamento Esperado**: Não deve conter valores nulos e formatar corretamente as datas.
- **Anomalias Observadas**:
  - Tipo de dado incorreto: está sendo armazenado como VARCHAR, o que pode causar problemas na análise temporal.

### `vl_transacao`
- **Propósito de Negócio**: Valor monetário da transação.
- **Tipo Esperado**: Float
- **Comportamento Esperado**: Não deve conter valores nulos e representar corretamente os valores financeiros.
- **Anomalias Observadas**:
  - Tipo de dado incorreto: está sendo armazenado como VARCHAR, o que pode causar problemas na análise financeira.

### `tp_transacao`
- **Propósito de Negócio**: Tipo da transação (ex.: saque, pagamento).
- **Tipo Esperado**: String
- **Comportamento Esperado**: Não deve conter valores nulos.
- **Anomalias Observadas**:
  - Limitada variedade de tipos: apenas seis tipos distintos são registrados.

### `cd_estabelecimento`
- **Propósito de Negócio**: Código do estabelecimento onde a transação foi realizada.
- **Tipo Esperado**: String
- **Comportamento Esperado**: Pode conter valores nulos, mas deve ser consistente quando presente.
- **Anomalias Observadas**:
  - Percentual de valores nulos: 6.5% dos registros estão sem código de estabelecimento.

### `fl_suspeita`
- **Propósito de Negócio**: Indicador se a transação é suspeita ou não.
- **Tipo Esperado**: Boolean
- **Comportamento Esperado**: Não deve conter valores nulos e ser verdadeiro ou falso.
- **Anomalias Observadas**:
  -

---
> **[AI_METADATA_STATUS: DRAFT]**