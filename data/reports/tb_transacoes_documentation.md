# Dicionário Técnico da Tabela `tb_transacoes`

## Visão Geral

A tabela `tb_transacoes` registra todas as movimentações financeiras realizadas por diferentes canais de atendimento. Ela é gerida pela equipe `squad-transacoes` e está atualmente em fase de rascunho (`DRAFT`). A tabela é alimentada por um sistema chamado `SWITCH_TRANSACIONAL` e armazenada no formato CSV com codificação UTF-8. As transações são atualizadas de forma event-driven, e a equipe de contato é `squad-transacoes@banco.com.br`.

### Contexto de Negócio

- **Registro de Movimentações**: A tabela captura todas as transações financeiras por canal, incluindo compras online não identificadas, onde `cd_estabelecimento` pode ser nulo.
- **Análise Antifraude**: A coluna `fl_suspeita` indica se uma transação está sendo analisada pelo motor antifraude.

### Regulamentações e Classificação

- **Tags Regulatórias**: A tabela está sujeita às normas `BACEN_4658` e `PCI_DSS`, exigindo conformidade com requisitos de segurança e privacidade de dados.
- **Classificação de Dados**: Os dados são classificados como confidenciais, com um período de retenção de 7 anos.

## Colunas

### `id_transacao`

- **Tipo**: `string`
- **Nullable**: Não
- **Descrição**: UUID da transação, gerado pelo sistema no momento da operação.
- **Comportamento Esperado**: Cada transação deve ter um identificador único.
- **Anomalias**: Algumas duplicatas foram observadas (2 valores duplicados).

### `cd_cliente`

- **Tipo**: `string`
- **Nullable**: Não
- **Descrição**: Referência ao cliente na tabela `tb_clientes`.
- **Comportamento Esperado**: Deve corresponder a um cliente válido na tabela `tb_clientes`.

### `dt_transacao`

- **Tipo**: `date`
- **Nullable**: Não
- **Descrição**: Data da transação no fuso horário `America/Sao_Paulo`.
- **Comportamento Esperado**: Deve conter a data exata da transação.

### `vl_transacao`

- **Tipo**: `float`
- **Nullable**: Não
- **Descrição**: Valor da transação em BRL. Positivo para débitos, negativo para estornos.
- **Comportamento Esperado**: Deve refletir o valor monetário da transação.
- **Anomalias**: Nenhuma anomalia relatada.

### `tp_transacao`

- **Tipo**: `string`
- **Nullable**: Não
- **Descrição**: Tipo da operação. Domínio: `COMPRA`, `SAQUE`, `TED`, `PIX`, `PAGAMENTO_BOLETO`, `ESTORNO`.
- **Comportamento Esperado**: Deve corresponder a um tipo de operação válido.
- **Anomalias**: Algumas duplicatas foram observadas (2 valores duplicados).

### `cd_estabelecimento`

- **Tipo**: `string`
- **Nullable**: Sim
- **Descrição**: CNPJ do estabelecimento. Pode ser nulo para compras online não identificadas (~6%).
- **Comportamento Esperado**: Deve ser preenchido para transações físicas; nulo para compras online não identificadas.
- **Anomalias**: 6.41% de valores nulos, conforme esperado.

### `fl_suspeita`

- **Tipo**: `boolean`
- **Nullable**: Não
- **Descrição**: Flag do motor antifraude. `True` indica transação em análise (~4% do volume).
- **Comportamento Esperado**: Deve refletir o status da análise antifraude.

### `cd_canal`

- **Tipo**: `string`
- **Nullable**: Não
- **Descrição**: Canal de origem. Domínio: `APP`, `INTERNET`, `AGENCIA`, `ATM`, `POS`.
- **Comportamento Esperado**: Deve corresponder a um canal de atendimento válido.
- **Anomalias**: Nenhuma anomalia relatada.

## Pontos de Atenção

- **Duplicatas**: Algumas duplicatas foram identificadas nas colunas `id_transacao` e `tp_transacao`. Isso viola a regra de tolerância que não permite duplicatas.
- **Valores Nulos**: A porcentagem de valores nulos em `cd_estabelecimento` está dentro do esperado (~6%), mas deve ser monitorada para garantir que não exceda o limite.
- **Conformidade Regulatória**: A tabela deve ser gerenciada em conformidade com as normas `BACEN_4658` e `PCI_DSS`, garantindo a segurança e privacidade dos dados.

---

> **[AI_METADATA_STATUS: DRAFT]** — Documentação gerada por SLM. Requer validação humana pelo Data Steward responsável antes de uso em produção.