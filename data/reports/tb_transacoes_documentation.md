# Dicionário Técnico da Tabela `tb_transacoes`

## Visão Geral

A tabela `tb_transacoes` registra todas as movimentações financeiras realizadas por diferentes canais de atendimento. Ela é gerida pela equipe `squad-transacoes` e está atualmente em versão `2.3.1`. A tabela é alimentada por um sistema chamado `SWITCH_TRANSACIONAL` e é atualizada de forma event-driven. A classificação de dados é `confidencial`, com uma retenção de dados de 7 anos. As tags regulatórias associadas são `BACEN_4658` e `PCI_DSS`.

## Colunas

### `id_transacao`
- **Tipo**: `string`
- **Nullable**: `false`
- **Descrição**: UUID da transação, gerado pelo switch transacional no momento da operação.
- **Propósito de Negócio**: Identificador único para cada transação.
- **Comportamento Esperado**: Não deve conter valores nulos e deve ser único para cada transação.
- **Anomalias**: Nenhuma anomalia observada.

### `cd_cliente`
- **Tipo**: `string`
- **Nullable**: `false`
- **Descrição**: Referência ao cliente em `tb_clientes`.
- **Propósito de Negócio**: Identifica o cliente associado à transação.
- **Comportamento Esperado**: Não deve conter valores nulos.
- **Anomalias**: Nenhuma anomalia observada.

### `dt_transacao`
- **Tipo**: `date`
- **Nullable**: `false`
- **Descrição**: Data da transação no fuso horário `America/Sao_Paulo`.
- **Propósito de Negócio**: Registro da data em que a transação ocorreu.
- **Comportamento Esperado**: Não deve conter valores nulos.
- **Anomalias**: Nenhuma anomalia observada.

### `vl_transacao`
- **Tipo**: `float`
- **Nullable**: `false`
- **Descrição**: Valor em BRL. Positivo para débitos, negativo para estornos.
- **Propósito de Negócio**: Valor monetário da transação.
- **Comportamento Esperado**: Não deve conter valores nulos.
- **Anomalias**: Nenhuma anomalia observada.

### `tp_transacao`
- **Tipo**: `string`
- **Nullable**: `false`
- **Descrição**: Tipo da operação. Dominio: `COMPRA`, `SAQUE`, `TED`, `PIX`, `PAGAMENTO_BOLETO`, `ESTORNO`.
- **Propósito de Negócio**: Identifica o tipo de transação realizada.
- **Comportamento Esperado**: Não deve conter valores nulos e deve estar dentro do domínio especificado.
- **Anomalias**: Nenhuma anomalia observada.

### `cd_estabelecimento`
- **Tipo**: `string`
- **Nullable**: `true`
- **Descrição**: CNPJ do estabelecimento. Nulo para compras online não identificadas (~6%).
- **Propósito de Negócio**: Identifica o estabelecimento associado à transação.
- **Comportamento Esperado**: Pode conter valores nulos, especialmente para compras online não identificadas.
- **Anomalias**: 6.41% de valores nulos, o que está dentro do esperado (~6%).

### `fl_suspeita`
- **Tipo**: `boolean`
- **Nullable**: `false`
- **Descrição**: Flag do motor antifraude. True indica transação em análise (~4% do volume).
- **Propósito de Negócio**: Indica se a transação está sendo analisada pelo motor antifraude.
- **Comportamento Esperado**: Não deve conter valores nulos.
- **Anomalias**: Nenhuma anomalia observada.

### `cd_canal`
- **Tipo**: `string`
- **Nullable**: `false`
- **Descrição**: Canal de origem. Dominio: `APP`, `INTERNET`, `AGENCIA`, `ATM`, `POS`.
- **Propósito de Negócio**: Identifica o canal pelo qual a transação foi realizada.
- **Comportamento Esperado**: Não deve conter valores nulos e deve estar dentro do domínio especificado.
- **Anomalias**: Nenhuma anomalia observada.

## Anomalias Observadas

- **Duplicatas**: A coluna `id_transacao` apresenta duplicatas, o que é uma anomalia crítica, já que deve ser única para cada transação.
- **Valores Nulos**: A coluna `cd_estabelecimento` tem 6.41% de valores nulos, o que está dentro do esperado (~6%).

## Implicações de Compliance

- **BACEN_4658**: A tabela deve estar em conformidade com as normas estabelecidas pelo Banco Central do Brasil.
- **PCI_DSS**: Deve seguir as diretrizes de segurança para proteção de dados de cartões de pagamento.

## Pontos de Atenção

1. **Duplicatas em `id_transacao`**: A presença de duplicatas é uma anomalia crítica que precisa ser investigada e corrigida.
2. **Valores Nulos em `cd_estabelecimento`**: Embora dentro do esperado, é importante monitorar para garantir que não haja aumento no percentual de nulos.
3. **Compliance**: Garantir que todas as transações estejam em conformidade com as normas BACEN_4658 e PCI_DSS.

---

> **[AI_METADATA_STATUS: DRAFT]** — Documentação gerada por SLM. Requer validação humana pelo Data Steward responsável antes de uso em produção.