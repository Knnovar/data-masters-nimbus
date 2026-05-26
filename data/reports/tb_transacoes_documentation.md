# Dicionário Técnico da Tabela `tb_transacoes`

## Descrição Geral

A tabela `tb_transacoes` armazena informações sobre movimentações financeiras realizadas através de diversos canais de atendimento do banco. Ela é gerida pela equipe `squad-transacoes` e está na versão 2.3.1.

## Colunas da Tabela

### id_transacao
- **Propósito de Negócio**: Identificador único para cada transação.
- **Tipo**: String (VARCHAR).
- **Comportamento Esperado**: Não deve conter valores nulos, pois é a chave primária.
- **Observações**:
  - Anomalia detectada: Existem duplicatas nos identificadores de transação. Isso viola o contrato que não permite chaves duplicadas.

### cd_cliente
- **Propósito de Negócio**: Código único para identificar o cliente associado à transação.
- **Tipo**: String (VARCHAR).
- **Comportamento Esperado**: Não deve conter valores nulos.
- **Observações**:
  - Alta concentração de alguns códigos de clientes, indicando possíveis duplicatas ou erros na atribuição.

### dt_transacao
- **Propósito de Negócio**: Data em que a transação foi realizada.
- **Tipo**: String (VARCHAR) — esperado como tipo Date.
- **Comportamento Esperado**: Não deve conter valores nulos.
- **Observações**:
  - A coluna está armazenando datas como strings, o que pode causar problemas em operações de data.

### vl_transacao
- **Propósito de Negócio**: Valor monetário da transação.
- **Tipo**: String (VARCHAR) — esperado como tipo Float.
- **Comportamento Esperado**: Não deve conter valores nulos.
- **Observações**:
  - A coluna está armazenando valores como strings, o que pode causar problemas em operações aritméticas.

### tp_transacao
- **Propósito de Negócio**: Tipo da transação (ex: saque, pagamento).
- **Tipo**: String (VARCHAR).
- **Comportamento Esperado**: Não deve conter valores nulos.
- **Observações**:
  - Existem apenas seis tipos únicos de transações registrados.

### cd_estabelecimento
- **Propósito de Negócio**: Código do estabelecimento onde a transação ocorreu.
- **Tipo**: String (VARCHAR).
- **Comportamento Esperado**: Pode conter valores nulos.
- **Observações**:
  - 6.5% dos registros estão sem um código de estabelecimento.

### fl_suspeita
- **Propósito de Negócio**: Indica se a transação é suspeita (True/False).
- **Tipo**: String (VARCHAR) — esperado como tipo Boolean.
- **Comportamento Esperado**: Não deve conter valores nulos.
- **Observações**:
  - A coluna está armazenando valores booleanos como strings.

### cd_canal
- **Propósito de Negócio**: Canal através do qual a transação foi realizada (ex: ATM, APP).
- **Tipo**: String (VARCHAR).
- **Comportamento Esperado**: Não deve conter valores nulos.
- **Observações**:
  - Existem apenas cinco canais únicos registrados.

## ⚠️ Pontos de Atenção

1. **Duplicatas na Chave Primária (`id_transacao`)**: Existe uma violação do contrato que não permite chaves duplicadas, o que pode causar problemas em operações que dependem da unicidade

---
> **[AI_METADATA_STATUS: DRAFT]**