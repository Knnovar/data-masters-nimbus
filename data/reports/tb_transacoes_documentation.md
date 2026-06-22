# Dicionário Técnico da Tabela `tb_transacoes`

## Visão Geral

A tabela `tb_transacoes` registra todas as movimentações financeiras realizadas por diferentes canais de atendimento do banco, conforme especificado no contrato YAML. Ela é gerida pela equipe `squad-transacoes` e está atualmente em versão 2.3.1, com status de manifesto como DRAFT.

### Contexto de Negócio

- **Propósito**: Registrar todas as movimentações financeiras por canal.
- **Detalhes Importantes**:
  - O campo `fl_suspeita` indica se uma transação está sendo analisada pelo motor antifraude.
  - O campo `cd_estabelecimento` pode ser nulo para compras online não identificadas, o que ocorre em aproximadamente 6% dos casos.

### Regulamentações e Compliance

- **Tags Regulatórias**: BACEN_4658, PCI_DSS
- **Classificação de Dados**: Confidencial
- **Período de Retenção**: 7 anos

## Colunas da Tabela

### `id_transacao`

- **Tipo**: String (VARCHAR)
- **Nullable**: Não
- **Descrição**: UUID da transação, gerado pelo sistema no momento da operação.
- **Comportamento Esperado**:
  - Deve ser único para cada transação. No entanto, foram identificadas duplicatas em 2 registros.
- **Anomalias Observadas**:
  - Duplicatas encontradas: 3 valores distintos aparecem mais de uma vez.

### `cd_cliente`

- **Tipo**: String (VARCHAR)
- **Nullable**: Não
- **Descrição**: Referência ao cliente na tabela `tb_clientes`.
- **Comportamento Esperado**:
  - Deve corresponder a um identificador válido em `tb_clientes`.
- **Anomalias Observadas**:
  - Alta frequência de valores repetidos, com alguns clientes tendo até 11 transações.

### `dt_transacao`

- **Tipo**: String (VARCHAR)
- **Nullable**: Não
- **Descrição**: Data da transação no fuso horário America/Sao_Paulo.
- **Comportamento Esperado**:
  - Deve ser uma data válida e formatada corretamente.
- **Anomalias Observadas**:
  - Datas futuras (ex.: "2024-10-22") foram observadas, indicando potencial erro de entrada.

### `vl_transacao`

- **Tipo**: String (VARCHAR)
- **Nullable**: Não
- **Descrição**: Valor da transação em BRL. Positivo para débitos e negativo para estornos.
- **Comportamento Esperado**:
  - Deve ser um número válido representando o valor monetário da transação.
- **Anomalias Observadas**:
  - O tipo de dado é VARCHAR, indicando uma inconsistência que deve ser corrigida para FLOAT.

### `tp_transacao`

- **Tipo**: String (VARCHAR)
- **Nullable**: Não
- **Descrição**: Tipo da operação. Dominio: COMPRA, SAQUE, TED, PIX, PAGAMENTO_BOLETO, ESTORNO.
- **Comportamento Esperado**:
  - Deve corresponder a um dos tipos de transação definidos no domínio.
- **Anomalias Observadas**: Nenhuma anomalia específica relatada.

### `cd_estabelecimento`

- **Tipo**: String (VARCHAR)
- **Nullable**: Sim
- **Descrição**: CNPJ do estabelecimento. Pode ser nulo para compras

---
> **[AI_METADATA_STATUS: DRAFT]**