# Dicionário Técnico da Tabela `tb_transacoes`

## Visão Geral

A tabela `tb_transacoes` registra todas as movimentações financeiras realizadas por diferentes canais de atendimento do banco, conforme descrito no contrato YAML. Esta documentação técnica fornece detalhes sobre cada coluna, incluindo propósito de negócio, tipo de dados e comportamento esperado, além de identificar anomalias observadas nas estatísticas do Data Profiler.

### Contexto de Negócios

- **Registro de Movimentações**: A tabela captura todas as transações financeiras por canal.
- **Flag de Suspeita**: `fl_suspeita` indica se uma transação está em análise pelo motor antifraude.
- **Estabelecimento Nulo**: `cd_estabelecimento` pode ser nulo para compras online não identificadas.

### Implicações de Conformidade

A tabela é classificada como confidencial e sujeita a regulamentações do BACEN (Banco Central do Brasil) e PCI DSS, exigindo medidas rigorosas de proteção de dados e retenção por 7 anos.

## Colunas Detalhadas

### `id_transacao`
- **Tipo**: String
- **Nullable**: Não
- **Descrição**: UUID da transação gerado pelo sistema no momento da operação.
- **Propósito**: Identificador único para cada transação.
- **Anomalias**:
  - **Duplicatas**: Apenas 2000 valores únicos em 2030 linhas, indicando duplicatas.

### `cd_cliente`
- **Tipo**: String
- **Nullable**: Não
- **Descrição**: Referência ao cliente na tabela `tb_clientes`.
- **Propósito**: Identifica o cliente associado à transação.
- **Comportamento Esperado**: Cada transação deve ter um cliente válido.

### `dt_transacao`
- **Tipo**: String (esperado como Date)
- **Nullable**: Não
- **Descrição**: Data da transação no fuso horário America/Sao_Paulo.
- **Propósito**: Registro do momento exato da transação.
- **Anomalias**:
  - **Formato de Dados**: Tipo VARCHAR em vez de DATE, o que pode causar problemas na análise.

### `vl_transacao`
- **Tipo**: String (esperado como Float)
- **Nullable**: Não
- **Descrição**: Valor da transação em BRL. Positivo para débitos e negativo para estornos.
- **Propósito**: Representa o valor financeiro envolvido na transação.
- **Anomalias**:
  - **Formato de Dados**: Tipo VARCHAR em vez de FLOAT, exigindo conversão.

### `tp_transacao`
- **Tipo**: String
- **Nullable**: Não
- **Descrição**: Tipo da operação (COMPRA, SAQUE, TED, PIX, PAGAMENTO_BOLETO, ESTORNO).
- **Propósito**: Categoriza a natureza da transação.
- **Comportamento Esperado**: Deve seguir o domínio especificado.

### `cd_estabelecimento`
- **Tipo**: String
- **Nullable**: Sim
- **Descrição**: CNPJ do estabelecimento. Nulo para compras online não identificadas (~6%).
- **Propósito**: Identifica o estabelecimento associado à transação.
- **Comportamento Esperado**: Pode ser nulo conforme descrito no contexto de negócios.

### `fl_suspeita`
- **Tipo**: String (esperado como Boolean)
- **

---
> **[AI_METADATA_STATUS: DRAFT]**