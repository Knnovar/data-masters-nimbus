# Dicionário Técnico da Tabela `tb_transacoes_breaking`

## Visão Geral

A tabela `tb_transacoes_breaking` contém registros das movimentações financeiras realizadas através de diversos canais de atendimento do banco. Ela é gerida pela equipe "squad-transacoes" e está atualmente em versão 2.3.1, com o status de manifesto como DRAFT.

### Contexto de Negócio

- **Propósito**: Registro de todas as movimentações financeiras por canal.
- **Detalhes Importantes**:
  - A coluna `fl_suspeita` indica se uma transação está sendo analisada pelo motor antifraude. Cerca de 4% do volume total é marcado como suspeito.
  - O campo `cd_estabelecimento` pode ser nulo para compras online não identificadas, o que ocorre em aproximadamente 6% dos casos.

### Regulamentações e Compliance

- **Tags Regulatórias**: 
  - BACEN_4658
  - PCI_DSS
- **Classificação de Dados**: Confidencial
- **Período de Retenção**: 7 anos

## Colunas da Tabela

### `id_transacao`
- **Tipo**: VARCHAR (string)
- **Nullable**: Não
- **Descrição**: UUID da transação, gerado pelo sistema no momento da operação.
- **Comportamento Esperado**: Deve ser único para cada transação. No entanto, foram identificadas duplicatas em 2 registros.
- **Anomalias**:
  - Duplicatas observadas: 3 valores distintos aparecem mais de uma vez.

### `cd_cliente`
- **Tipo**: VARCHAR (string)
- **Nullable**: Não
- **Descrição**: Referência ao cliente na tabela `tb_clientes`.
- **Comportamento Esperado**: Deve corresponder a um cliente válido.
- **Anomalias**:
  - Alta frequência de valores repetidos: 3 clientes aparecem com mais de 10 ocorrências.

### `dt_transacao`
- **Tipo**: VARCHAR (string)
- **Nullable**: Não
- **Descrição**: Data da transação no fuso horário America/Sao_Paulo.
- **Comportamento Esperado**: Deve ser uma data válida e formatada corretamente.
- **Anomalias**:
  - Tipo de dado incorreto: Deveria ser do tipo DATE, mas está como VARCHAR.

### `vl_transacao`
- **Tipo**: VARCHAR (string)
- **Nullable**: Não
- **Descrição**: Valor da transação em BRL. Positivo para débitos e negativo para estornos.
- **Comportamento Esperado**: Deve ser um número decimal representando o valor monetário.
- **Anomalias**:
  - Tipo de dado incorreto: Deveria ser do tipo FLOAT, mas está como VARCHAR.

### `tp_transacao`
- **Tipo**: VARCHAR (string)
- **Nullable**: Não
- **Descrição**: Tipo da operação. Dominio: COMPRA, SAQUE, TED, PIX, PAGAMENTO_BOLETO, ESTORNO.
- **Comportamento Esperado**: Deve corresponder a um dos tipos de transação definidos no domínio.

### `cd_estabelecimento`
- **Tipo**: VARCHAR (string)
- **Nullable**: Sim
- **Descrição**: CNPJ do estabelecimento. Pode ser nulo para compras online não identificadas.
- **Comportamento Esperado**: Deve ser um número válido de CNPJ ou nulo conforme o contexto.
- **

---
> **[AI_METADATA_STATUS: DRAFT]**