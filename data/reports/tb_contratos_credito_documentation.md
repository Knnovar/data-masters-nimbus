# Dicionário Técnico da Tabela `tb_contratos_credito`

## Descrição Geral

A tabela `tb_contratos_credito` armazena informações sobre contratos de produtos de crédito, tanto ativos quanto encerrados. Ela é gerida pela equipe `squad-credito` e está na versão 3.0.0.

## Colunas da Tabela

### `id_contrato`
- **Propósito de Negócio**: Identificador único para cada contrato.
- **Tipo**: String
- **Comportamento Esperado**: Não deve conter valores nulos; deve ser única em toda a tabela (chave primária).
- **Anomalias Observadas**: Nenhuma anomalia detectada. Todos os registros são únicos e não há valores nulos.

### `cd_cliente`
- **Propósito de Negócio**: Código identificador do cliente associado ao contrato.
- **Tipo**: String
- **Comportamento Esperado**: Não deve conter valores nulos; pode ter duplicatas, indicando múltiplos contratos por cliente.
- **Anomalias Observadas**: Alta frequência de alguns códigos de clientes (ex.: "88092CC3-B56" aparece 4 vezes), o que é esperado para clientes com múltiplos contratos.

### `dt_contrato`
- **Propósito de Negócio**: Data em que o contrato foi formalizado.
- **Tipo**: String (deveria ser Date)
- **Comportamento Esperado**: Não deve conter valores nulos; cada data deve estar no formato correto.
- **Anomalias Observadas**: Tipo de dado está como `VARCHAR` ao invés de `DATE`, o que pode causar problemas em operações temporais.

### `vl_limite`
- **Propósito de Negócio**: Valor limite do crédito disponível para o contrato.
- **Tipo**: String (deveria ser Float)
- **Comportamento Esperado**: Não deve conter valores nulos; representa a capacidade máxima de empréstimo.
- **Anomalias Observadas**: Tipo de dado está como `VARCHAR` ao invés de `FLOAT`, o que pode causar problemas em cálculos financeiros.

### `vl_utilizado`
- **Propósito de Negócio**: Valor atualmente utilizado do crédito disponível.
- **Tipo**: String (deveria ser Float)
- **Comportamento Esperado**: Não deve conter valores nulos; representa o montante usado pelo cliente.
- **Anomalias Observadas**: Tipo de dado está como `VARCHAR` ao invés de `FLOAT`, o que pode causar problemas em cálculos financeiros.

### `tp_produto`
- **Propósito de Negócio**: Tipo do produto de crédito (ex.: Cheque Especial, Financiamento Veículo).
- **Tipo**: String
- **Comportamento Esperado**: Não deve conter valores nulos; deve refletir os tipos de produtos oferecidos.
- **Anomalias Observadas**: Nenhuma anomalia detectada. Os dados estão consistentes com o esperado.

### `cd_status`
- **Propósito de Negócio**: Status atual do contrato (ex.: Renegociado, Em Atraso).
- **Tipo**: String
- **Comportamento Esperado**: Não deve conter valores nulos; reflete a situação financeira do contrato.
- **Anomalias Observadas**: Nenhuma anomalia detectada. Os dados estão consistentes com o esperado.

### `dt_vencimento`
- **Propósito de Negócio**: Data em que o contrato está previsto para vencer.
- **Tipo**: String

---
> **[AI_METADATA_STATUS: DRAFT]**