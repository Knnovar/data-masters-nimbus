# Dicionário Técnico da Tabela `tb_transacoes`

## Visão Geral

A tabela `tb_transacoes` registra todas as movimentações financeiras realizadas por diferentes canais de atendimento. Ela é gerida pela equipe `squad-transacoes` e está atualmente em versão `2.3.1`. A tabela é alimentada de forma event-driven pelo sistema `SWITCH_TRANSACIONAL` e armazena dados em formato CSV com codificação UTF-8.

### Contexto de Negócio

- **Registro de Movimentações**: Captura todas as transações financeiras por canal.
- **Flag de Suspeita**: `fl_suspeita` indica se uma transação está sendo analisada pelo motor antifraude.
- **Estabelecimento Nulo**: `cd_estabelecimento` pode ser nulo para compras online não identificadas, o que ocorre em aproximadamente 6% das transações.

### Implicações de Compliance

- **Regulatory Tags**: A tabela está sujeita às normas `BACEN_4658` e `PCI_DSS`, exigindo medidas rigorosas de segurança e privacidade dos dados.
- **Classificação de Dados**: Os dados são classificados como confidenciais, com uma política de retenção de 7 anos.

## Colunas

### `id_transacao`

- **Tipo**: `string`
- **Nullable**: Não
- **Descrição**: UUID da transação, gerado no momento da operação pelo switch transacional.
- **Comportamento Esperado**: Valor único para cada transação.
- **Anomalias**: Nenhuma anomalia relatada.

### `cd_cliente`

- **Tipo**: `string`
- **Nullable**: Não
- **Descrição**: Referência ao cliente em `tb_clientes`.
- **Comportamento Esperado**: Valor único e não nulo, correspondendo a um cliente existente.
- **Anomalias**: Nenhuma anomalia relatada.

### `dt_transacao`

- **Tipo**: `date`
- **Nullable**: Não
- **Descrição**: Data da transação no fuso horário `America/Sao_Paulo`.
- **Comportamento Esperado**: Data válida e não nula.
- **Anomalias**: Nenhuma anomalia relatada.

### `vl_transacao`

- **Tipo**: `float`
- **Nullable**: Não
- **Descrição**: Valor em BRL. Positivo para débitos, negativo para estornos.
- **Comportamento Esperado**: Valor numérico, refletindo a natureza da transação.
- **Anomalias**: Nenhuma anomalia relatada.

### `tp_transacao`

- **Tipo**: `string`
- **Nullable**: Não
- **Descrição**: Tipo da operação. Dominio: COMPRA, SAQUE, TED, PIX, PAGAMENTO_BOLETO, ESTORNO.
- **Comportamento Esperado**: Valor dentro do domínio especificado.
- **Anomalias**: Duplicatas observadas para alguns valores, mas dentro do limite de tolerância.

### `cd_estabelecimento`

- **Tipo**: `string`
- **Nullable**: Sim
- **Descrição**: CNPJ do estabelecimento. Nulo para compras online não identificadas (~6%).
- **Comportamento Esperado**: Pode ser nulo conforme o contexto de negócio.
- **Anomalias**: Nulo em aproximadamente 6% das transações, conforme esperado.

### `fl_suspeita`

- **Tipo**: `boolean`
- **Nullable**: Não
- **Descrição**: Flag do motor antifraude. True indica transação em análise (~4% do volume).
- **Comportamento Esperado**: Valor booleano, refletindo a análise de fraude.
- **Anomalias**: Nenhuma anomalia relatada.

### `cd_canal`

- **Tipo**: `string`
- **Nullable**: Não
- **Descrição**: Canal de origem. Dominio: APP, INTERNET, AGENCIA, ATM, POS.
- **Comportamento Esperado**: Valor dentro do domínio especificado.
- **Anomalias**: Nenhuma anomalia relatada.

## Análise de Estatísticas

- **Duplicatas**: Algumas duplicatas foram observadas nos valores de `id_transacao` e `tp_transacao`, mas estão dentro do limite de tolerância de 10% de nulos e não duplicatas permitidas.
- **Nulos**: `cd_estabelecimento` tem um percentual de nulos de 6.41%, o que está dentro do esperado para compras online não identificadas.

## Pontos de Atenção

1. **Duplicatas**: Monitorar duplicatas em `id_transacao` e `tp_transacao` para garantir integridade dos dados.
2. **Compliance**: Manter a conformidade com `BACEN_4658` e `PCI_DSS` é crucial, especialmente considerando a classificação de dados como confidencial.
3. **Retenção de Dados**: Garantir que a política de retenção de 7 anos seja seguida rigorosamente.
4. **Análise de Fraude**: Monitorar o percentual de transações suspeitas para ajustar o motor antifraude conforme necessário.

---

> **[AI_METADATA_STATUS: DRAFT]** — Documentação gerada por SLM. Requer validação humana pelo Data Steward responsável antes de uso em produção.