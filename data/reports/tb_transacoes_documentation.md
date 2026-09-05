# Dicionário Técnico da Tabela `tb_transacoes`

## Visão Geral

A tabela `tb_transacoes` registra todas as movimentações financeiras realizadas através de diferentes canais de atendimento do banco. Ela é gerida pela equipe `squad-transacoes` e está atualmente em versão 2.3.1, com status de manifesto como DRAFT. As transações são capturadas de forma event-driven a partir do sistema `SWITCH_TRANSACIONAL` e armazenadas em formato CSV com codificação UTF-8.

### Contexto de Negócio

- **Propósito**: Registro de todas as movimentações financeiras por canal.
- **Detalhes Importantes**: 
  - O campo `fl_suspeita` indica se uma transação está sendo analisada pelo motor antifraude.
  - O campo `cd_estabelecimento` pode ser nulo para compras online não identificadas, o que ocorre em aproximadamente 6% dos casos.

### Regulamentações e Compliance

- **Tags Regulatórias**: 
  - BACEN_4658
  - PCI_DSS
- **Classificação de Dados**: Confidencial
- **Período de Retenção**: 7 anos

## Colunas

### `id_transacao`

- **Tipo**: String
- **Descrição**: UUID da transação, gerado pelo switch transacional no momento da operação.
- **Comportamento Esperado**: Não nulo, chave primária, único para cada transação.
- **Estatísticas**:
  - **Null Pct**: 0.0%
  - **Unique Count**: 1999
  - **Anomalias**: Existem duplicatas (ex.: 2 ocorrências para alguns valores).

### `cd_cliente`

- **Tipo**: String
- **Descrição**: Referência ao cliente em `tb_clientes`.
- **Comportamento Esperado**: Não nulo.
- **Estatísticas**:
  - **Null Pct**: 0.0%
  - **Unique Count**: 1999

### `dt_transacao`

- **Tipo**: Date
- **Descrição**: Data da transação no fuso horário America/Sao_Paulo.
- **Comportamento Esperado**: Não nulo.
- **Estatísticas**: Não disponíveis no perfil de dados.

### `vl_transacao`

- **Tipo**: Float
- **Descrição**: Valor em BRL. Positivo para débitos, negativo para estornos.
- **Comportamento Esperado**: Não nulo.
- **Estatísticas**:
  - **Null Pct**: 0.0%
  - **Min**: 1235749000180.0
  - **Max**: 98706123000147.0
  - **Mean**: 49641986374552.44

### `tp_transacao`

- **Tipo**: String
- **Descrição**: Tipo da operação. Domínio: COMPRA, SAQUE, TED, PIX, PAGAMENTO_BOLETO, ESTORNO.
- **Comportamento Esperado**: Não nulo.
- **Estatísticas**:
  - **Null Pct**: 0.0%
  - **Unique Count**: 1999
  - **Top Values**: COMPRA, PAGAMENTO_BOLETO, SAQUE (cada um com 2 ocorrências).

### `cd_estabelecimento`

- **Tipo**: String
- **Descrição**: CNPJ do estabelecimento. Nulo para compras online não identificadas (~6%).
- **Comportamento Esperado**: Pode ser nulo.


---
> **[AI_METADATA_STATUS: DRAFT]**