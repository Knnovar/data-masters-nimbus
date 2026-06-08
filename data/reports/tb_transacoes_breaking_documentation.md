# Dicionário Técnico da Tabela `tb_transacoes_breaking`

## Visão Geral

A tabela `tb_transacoes_breaking` contém registros das movimentações financeiras realizadas através de diversos canais de atendimento do banco. Ela é gerida pela equipe `squad-transacoes` e está em fase de rascunho (`DRAFT`). A fonte dos dados é o sistema `SWITCH_TRANSACIONAL`, que gera arquivos CSV codificados em UTF-8 no sistema operacional Unix, atualizados de forma event-driven. O contato para mais informações é `squad-transacoes@banco.com.br`.

### Contexto de Negócio

A tabela registra todas as movimentações financeiras por canal. A coluna `fl_suspeita` sinaliza transações em análise pelo motor antifraude, enquanto a coluna `cd_estabelecimento` pode ser nula para compras online não identificadas.

### Classificação e Retenção de Dados

- **Classificação**: Confidencial
- **Retenção**: 7 anos
- **Tags Regulatórias**: BACEN_4658, PCI_DSS

## Colunas da Tabela

### `id_transacao`
- **Tipo**: String (VARCHAR)
- **Descrição**: UUID da transação. Gerado pelo switch transacional no momento da operação.
- **Comportamento Esperado**: Não nulo e deve ser único para cada transação.
- **Anomalias Observadas**:
  - Existem duplicatas: 30 registros são duplicados, o que excede a tolerância de zero duplicatas permitida.

### `cd_cliente`
- **Tipo**: String (VARCHAR)
- **Descrição**: Referência ao cliente em `tb_clientes`.
- **Comportamento Esperado**: Não nulo.
- **Anomalias Observadas**:
  - Alta concentração de transações por poucos clientes, indicando potencial uso indevido ou fraude.

### `dt_transacao`
- **Tipo**: String (VARCHAR)
- **Descrição**: Data da transação no fuso horário America/Sao_Paulo.
- **Comportamento Esperado**: Não nulo e deve estar em formato de data válido.
- **Anomalias Observadas**:
  - Tipo de dado incorreto: Deveria ser do tipo `date`, mas está como `VARCHAR`.

### `vl_transacao`
- **Tipo**: String (VARCHAR)
- **Descrição**: Valor em BRL. Positivo para débitos, negativo para estornos.
- **Comportamento Esperado**: Não nulo e deve ser numérico.
- **Anomalias Observadas**:
  - Tipo de dado incorreto: Deveria ser do tipo `float`, mas está como `VARCHAR`.

### `tp_transacao`
- **Tipo**: String (VARCHAR)
- **Descrição**: Tipo da operação. Domínio: COMPRA, SAQUE, TED, PIX, PAGAMENTO_BOLETO, ESTORNO.
- **Comportamento Esperado**: Não nulo e deve estar dentro do domínio especificado.

### `cd_estabelecimento`
- **Tipo**: String (VARCHAR)
- **Descrição**: CNPJ do estabelecimento. Nulo para compras online não identificadas (~6%).
- **Comportamento Esperado**: Pode ser nulo, mas deve estar dentro de um intervalo válido quando presente.
- **Anomalias Observadas**:
  - Percentual de valores nulos está em linha com o esperado (6.4%).

### `fl_suspeita`
- **Tipo**: String (VARCHAR)
- **Descrição**: Flag

---
> **[AI_METADATA_STATUS: DRAFT]**