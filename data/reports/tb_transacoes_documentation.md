# Dicionário Técnico da Tabela `tb_transacoes`

## Visão Geral

A tabela `tb_transacoes` registra todas as movimentações financeiras por canal de atendimento, conforme declarado no contrato de dados. Esta tabela é gerida pela equipe `squad-transacoes` e está em conformidade com as regulamentações BACEN_4658 e PCI_DSS, sendo classificada como confidencial com um período de retenção de 7 anos.

## Colunas

### `id_transacao`
- **Tipo**: `string`
- **Nullable**: Não
- **Descrição**: UUID da transação, gerado pelo switch transacional no momento da operação.
- **Propósito de Negócio**: Identificador único para cada transação.
- **Comportamento Esperado**: Deve ser único para cada transação.
- **Anomalias**:
  - **Duplicatas**: 2% das transações apresentam IDs duplicados, o que é uma anomalia crítica, já que `allow_duplicates` é definido como `false`.

### `cd_cliente`
- **Tipo**: `string`
- **Nullable**: Não
- **Descrição**: Referência ao cliente em `tb_clientes`.
- **Propósito de Negócio**: Identifica o cliente associado à transação.
- **Comportamento Esperado**: Deve corresponder a um cliente válido na tabela `tb_clientes`.
- **Anomalias**: Nenhuma anomalia relatada.

### `dt_transacao`
- **Tipo**: `string`
- **Nullable**: Não
- **Descrição**: Data da transação no fuso horário America/Sao_Paulo.
- **Propósito de Negócio**: Registro da data e hora em que a transação ocorreu.
- **Comportamento Esperado**: Deve ser uma data válida no formato esperado.
- **Anomalias**: Nenhuma anomalia relatada.

### `vl_transacao`
- **Tipo**: `string`
- **Nullable**: Não
- **Descrição**: Valor em BRL. Positivo para débitos, negativo para estornos.
- **Propósito de Negócio**: Valor monetário da transação.
- **Comportamento Esperado**: Deve ser um valor numérico representando o valor da transação.
- **Anomalias**: Nenhuma anomalia relatada.

### `tp_transacao`
- **Tipo**: `string`
- **Nullable**: Não
- **Descrição**: Tipo da operação. Dominio: COMPRA, SAQUE, TED, PIX, PAGAMENTO_BOLETO, ESTORNO.
- **Propósito de Negócio**: Identifica o tipo de transação realizada.
- **Comportamento Esperado**: Deve corresponder a um dos tipos de operação definidos.
- **Anomalias**: Nenhuma anomalia relatada.

### `cd_estabelecimento`
- **Tipo**: `string`
- **Nullable**: Sim
- **Descrição**: CNPJ do estabelecimento. Nulo para compras online não identificadas (~6%).
- **Propósito de Negócio**: Identifica o estabelecimento associado à transação.
- **Comportamento Esperado**: Pode ser nulo para transações online não identificadas.
- **Anomalias**: 6.7% das entradas são nulas, o que está dentro do esperado.

### `fl_suspeita`
- **Tipo**: `string`
- **Nullable**: Não
- **Descrição**: Flag do motor antifraude. True indica transação em análise (~4% do volume).
- **Propósito de Negócio**: Indica se a transação está sendo analisada por suspeita de fraude.
- **Comportamento Esperado**: Deve ser `true` ou `false`.
- **Anomalias**: 3.9% das transações estão marcadas como suspeitas, o que está dentro do esperado.

### `cd_canal`
- **Tipo**: `string`
- **Nullable**: Não
- **Descrição**: Canal de origem. Dominio: APP, INTERNET, AGENCIA, ATM, POS.
- **Propósito de Negócio**: Identifica o canal através do qual a transação foi realizada.
- **Comportamento Esperado**: Deve corresponder a um dos canais definidos.
- **Anomalias**: Nenhuma anomalia relatada.

## Considerações Regulatórias

- **BACEN_4658**: A tabela deve estar em conformidade com as normas do Banco Central do Brasil.
- **PCI_DSS**: A tabela contém dados sensíveis que devem ser protegidos conforme os padrões de segurança de dados de cartões de pagamento.

## Pontos de Atenção

1. **Duplicatas em `id_transacao`**: A presença de IDs duplicados é uma anomalia crítica que deve ser investigada e corrigida.
2. **Nulos em `cd_estabelecimento`**: Embora esperado, o percentual de nulos deve ser monitorado para garantir que não exceda o limite aceitável.
3. **Transações Suspeitas**: O percentual de transações marcadas como suspeitas deve ser monitorado para identificar padrões de fraude.
4. **Compliance Regulatória**: Garantir que todas as transações estejam em conformidade com as normas BACEN_4658 e PCI_DSS.

---

> **[AI_METADATA_STATUS: DRAFT]** — Documentação gerada por SLM. Requer validação humana pelo Data Steward responsável antes de uso em produção.