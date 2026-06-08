# Dicionário Técnico da Tabela `tb_transacoes_non_breaking`

## Visão Geral

A tabela `tb_transacoes_non_breaking` contém registros das movimentações financeiras realizadas através de diversos canais de atendimento do banco. Ela é gerida pela equipe `squad-transacoes` e está em versão 2.3.1, com status atual de DRAFT no contrato de dados.

### Contexto de Negócio

- **Propósito**: Registro de todas as movimentações financeiras por canal.
- **Detalhes Importantes**:
  - A coluna `fl_suspeita` indica se uma transação está sendo analisada pelo motor antifraude. Transações suspeitas representam aproximadamente 4% do volume total.
  - O campo `cd_estabelecimento` pode ser nulo para compras online não identificadas, o que ocorre em cerca de 6% dos casos.

### Regulamentação e Compliance

- **Tags Regulatórias**: A tabela está sujeita aos padrões BACEN_4658 e PCI_DSS.
- **Classificação de Dados**: Os dados são classificados como confidenciais, com um período de retenção de 7 anos.

## Esquema da Tabela

### Colunas

1. **`id_transacao`**
   - **Tipo**: `VARCHAR`
   - **Descrição**: UUID da transação gerado pelo switch transacional no momento da operação.
   - **Comportamento Esperado**: Não nulo, chave primária única para cada transação.
   - **Anomalias Observadas**:
     - 0.2% das transações apresentam duplicatas de `id_transacao`.

2. **`cd_cliente`**
   - **Tipo**: `VARCHAR`
   - **Descrição**: Referência ao cliente em `tb_clientes`.
   - **Comportamento Esperado**: Não nulo, deve corresponder a um registro válido na tabela de clientes.
   - **Anomalias Observadas**:
     - Algumas IDs de clientes aparecem com alta frequência (ex.: 15 ocorrências para "29F4AE29-495").

3. **`dt_transacao`**
   - **Tipo**: `VARCHAR`
   - **Descrição**: Data da transação no fuso horário America/Sao_Paulo.
   - **Comportamento Esperado**: Não nulo, deve ser uma data válida e formatada corretamente.
   - **Anomalias Observadas**:
     - A coluna é do tipo `VARCHAR`, o que pode indicar inconsistências no formato de data.

4. **`vl_transacao`**
   - **Tipo**: `VARCHAR`
   - **Descrição**: Valor em BRL da transação. Positivo para débitos, negativo para estornos.
   - **Comportamento Esperado**: Não nulo, deve ser um valor numérico representando o montante da transação.
   - **Anomalias Observadas**:
     - A coluna é do tipo `VARCHAR`, sugerindo a necessidade de conversão para um tipo numérico adequado.

5. **`tp_transacao`**
   - **Tipo**: `VARCHAR`
   - **Descrição**: Tipo da operação, com domínio definido como COMPRA, SAQUE, TED, PIX, PAGAMENTO_BOLETO, ESTORNO.
   - **Comportamento Esperado**: Não nulo, deve corresponder a um dos tipos de transação permitidos.

6. **`cd_estabelecimento`**
   - **Tipo**: `VARCHAR`
   - **Descrição**: CNPJ do est

---
> **[AI_METADATA_STATUS: DRAFT]**