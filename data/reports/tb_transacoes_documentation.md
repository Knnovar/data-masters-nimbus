# Dicionário Técnico da Tabela `tb_transacoes`

## Visão Geral

A tabela `tb_transacoes` registra todas as movimentações financeiras realizadas através dos diversos canais de atendimento do banco, conforme especificado no manifesto. Ela é gerida pela equipe `squad-transacoes` e está atualmente em versão 2.3.1 com status de DRAFT.

### Contexto de Negócio

- **Propósito**: Registro das movimentações financeiras por canal.
- **Detalhes Importantes**:
  - O campo `fl_suspeita` indica se uma transação está sob análise pelo motor antifraude.
  - O campo `cd_estabelecimento` pode ser nulo para compras online não identificadas, o que ocorre em aproximadamente 6% das entradas.

### Regulamentações e Compliance

- **Tags Regulatórias**: BACEN_4658, PCI_DSS
- **Classificação de Dados**: Confidencial
- **Período de Retenção**: 7 anos

## Esquema da Tabela

### Colunas

1. **`id_transacao`**
   - **Tipo**: `string`
   - **Nullable**: Não
   - **Descrição**: UUID gerado pelo sistema no momento da operação, servindo como chave primária.
   - **Comportamento Esperado**: Deve ser único e não nulo para cada transação.

2. **`cd_cliente`**
   - **Tipo**: `string`
   - **Nullable**: Não
   - **Descrição**: Referência ao cliente na tabela `tb_clientes`.
   - **Comportamento Esperado**: Sempre deve ter um valor válido referenciando um cliente existente.

3. **`dt_transacao`**
   - **Tipo**: `date`
   - **Nullable**: Não
   - **Descrição**: Data da transação no fuso horário America/Sao_Paulo.
   - **Comportamento Esperado**: Deve conter a data exata em que a transação ocorreu.

4. **`vl_transacao`**
   - **Tipo**: `float`
   - **Nullable**: Não
   - **Descrição**: Valor da transação em BRL. Positivo para débitos e negativo para estornos.
   - **Comportamento Esperado**: Deve refletir corretamente o valor financeiro da operação.

5. **`tp_transacao`**
   - **Tipo**: `string`
   - **Nullable**: Não
   - **Descrição**: Tipo de transação (COMPRA, SAQUE, TED, PIX, PAGAMENTO_BOLETO, ESTORNO).
   - **Comportamento Esperado**: Deve estar dentro do domínio especificado.

6. **`cd_estabelecimento`**
   - **Tipo**: `string`
   - **Nullable**: Sim
   - **Descrição**: CNPJ do estabelecimento. Pode ser nulo para compras online não identificadas.
   - **Comportamento Esperado**: Aproximadamente 6% das entradas devem ter este campo como nulo.

7. **`fl_suspeita`**
   - **Tipo**: `boolean`
   - **Nullable**: Não
   - **Descrição**: Indica se a transação está sendo analisada pelo motor antifraude.
   - **Comportamento Esperado**: Cerca de 4% das transações devem ter este campo como verdadeiro.

8. **`cd_canal`**
   - **Tipo**: `string`
   - **Nullable**: Não
   - **Descrição**: Canal

---
> **[AI_METADATA_STATUS: DRAFT]**