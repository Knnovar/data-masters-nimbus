# Dicionário Técnico da Tabela `tb_transacoes`

## Visão Geral

A tabela `tb_transacoes` registra todas as movimentações financeiras por canal de atendimento. Ela é gerida pela equipe `squad-transacoes` e está atualmente em versão `2.3.1`. O sistema de origem é o `SWITCH_TRANSACIONAL`, e os dados são armazenados em formato CSV com codificação UTF-8. A atualização dos dados é event-driven, e o contato para mais informações é `squad-transacoes@banco.com.br`.

### Contexto de Negócio

- **Propósito**: Registro de todas as movimentações financeiras por canal.
- **Detalhes Importantes**:
  - A coluna `fl_suspeita` indica se a transação está sendo analisada pelo motor antifraude.
  - A coluna `cd_estabelecimento` pode ser nula para compras online não identificadas, o que ocorre em aproximadamente 6% dos casos.

### Implicações de Compliance

- **Regulatory Tags**: A tabela está sujeita às normas `BACEN_4658` e `PCI_DSS`.
- **Classificação de Dados**: Os dados são classificados como confidenciais.
- **Retenção de Dados**: Os dados devem ser retidos por 7 anos.

## Colunas

### `id_transacao`

- **Tipo**: `string`
- **Nullable**: Não
- **Descrição**: UUID da transação, gerado pelo switch transacional no momento da operação.
- **Comportamento Esperado**: Deve ser único para cada transação.
- **Anomalias**:
  - **Duplicatas**: 2% das transações têm IDs duplicados, o que é uma anomalia crítica.

### `cd_cliente`

- **Tipo**: `string`
- **Nullable**: Não
- **Descrição**: Referência ao cliente em `tb_clientes`.
- **Comportamento Esperado**: Deve corresponder a um cliente válido na tabela `tb_clientes`.
- **Anomalias**:
  - **Duplicatas**: Alguns clientes têm múltiplas transações, o que é esperado.

### `dt_transacao`

- **Tipo**: `string`
- **Nullable**: Não
- **Descrição**: Data da transação no fuso horário `America/Sao_Paulo`.
- **Comportamento Esperado**: Deve estar no formato de data válido.
- **Anomalias**:
  - **Futuras**: Algumas datas estão no futuro, o que pode indicar um problema de registro.

### `vl_transacao`

- **Tipo**: `string`
- **Nullable**: Não
- **Descrição**: Valor em BRL. Positivo para débitos, negativo para estornos.
- **Comportamento Esperado**: Deve ser um número válido representando o valor da transação.
- **Anomalias**:
  - **Formato**: O valor está armazenado como string, o que pode causar problemas de análise.

### `tp_transacao`

- **Tipo**: `string`
- **Nullable**: Não
- **Descrição**: Tipo da operação. Domínio: `COMPRA`, `SAQUE`, `TED`, `PIX`, `PAGAMENTO_BOLETO`, `ESTORNO`.
- **Comportamento Esperado**: Deve corresponder a um dos tipos de operação definidos.
- **Anomalias**:
  - **Valores Inválidos**: Qualquer valor fora do domínio definido é considerado inválido.

### `cd_estabelecimento`

- **Tipo**: `string`
- **Nullable**: Sim
- **Descrição**: CNPJ do estabelecimento. Nulo para compras online não identificadas (~6%).
- **Comportamento Esperado**: Deve ser um CNPJ válido ou nulo.
- **Anomalias**:
  - **Formato**: O valor está armazenado como string, o que pode causar problemas de validação.

### `fl_suspeita`

- **Tipo**: `string`
- **Nullable**: Não
- **Descrição**: Flag do motor antifraude. True indica transação em análise (~4% do volume).
- **Comportamento Esperado**: Deve ser `True` ou `False`.
- **Anomalias**:
  - **Formato**: O valor está armazenado como string, o que pode causar problemas de análise.

### `cd_canal`

- **Tipo**: `string`
- **Nullable**: Não
- **Descrição**: Canal de origem. Domínio: `APP`, `INTERNET`, `AGENCIA`, `ATM`, `POS`.
- **Comportamento Esperado**: Deve corresponder a um dos canais de origem definidos.
- **Anomalias**:
  - **Valores Inválidos**: Qualquer valor fora do domínio definido é considerado inválido.

## Pontos de Atenção

1. **Duplicatas em `id_transacao`**: 2% das transações têm IDs duplicados, o que é uma anomalia crítica que deve ser investigada.
2. **Datas Futuras em `dt_transacao`**: Algumas datas estão no futuro, o que pode indicar um problema de registro.
3. **Formato de Valores**: Vários campos (`vl_transacao`, `fl_suspeita`, `cd_estabelecimento`) estão armazenados como strings, o que pode causar problemas de análise e validação.
4. **Valores Inválidos**: Qualquer valor fora dos domínios definidos para `tp_transacao` e `cd_canal` é considerado inválido e deve ser tratado.
5. **Compliance**: A tabela está sujeita a normas regulatórias rigorosas (`BACEN_4658` e `PCI_DSS`), e qualquer anomalia pode ter implicações legais.

> **[AI_METADATA_STATUS: DRAFT]** — Documentação gerada por SLM. Requer validação humana pelo Data Steward responsável antes de uso em produção.