# Dicionário Técnico da Tabela `tb_transacoes`

## Visão Geral

A tabela `tb_transacoes` registra todas as movimentações financeiras realizadas por diferentes canais de atendimento do banco. Ela é gerida pela equipe `squad-transacoes` e está em conformidade com os regulamentos BACEN_4658 e PCI_DSS. A tabela é classificada como confidencial e possui um período de retenção de 7 anos.

## Colunas

### `id_transacao`
- **Tipo**: `string`
- **Nullable**: `false`
- **Descrição**: UUID da transação, gerado pelo sistema transacional no momento da operação.
- **Propósito de Negócio**: Identificador único para cada transação.
- **Comportamento Esperado**: Deve ser único para cada transação.
- **Anomalias**: 2% de duplicatas observadas, o que excede o limite de tolerância de 0% para duplicatas.

### `cd_cliente`
- **Tipo**: `string`
- **Nullable**: `false`
- **Descrição**: Referência ao cliente em `tb_clientes`.
- **Propósito de Negócio**: Identifica o cliente associado à transação.
- **Comportamento Esperado**: Deve corresponder a um cliente válido na tabela `tb_clientes`.
- **Anomalias**: Alta concentração de transações para alguns clientes, indicando potencialmente transações repetitivas ou padrões incomuns.

### `dt_transacao`
- **Tipo**: `string` (deveria ser `date`)
- **Nullable**: `false`
- **Descrição**: Data da transação no fuso horário America/Sao_Paulo.
- **Propósito de Negócio**: Registro da data e hora em que a transação ocorreu.
- **Comportamento Esperado**: Deve estar no formato de data e corresponder ao fuso horário especificado.
- **Anomalias**: Tipo de dado incorreto (`VARCHAR` em vez de `date`), o que pode afetar operações de data.

### `vl_transacao`
- **Tipo**: `string` (deveria ser `float`)
- **Nullable**: `false`
- **Descrição**: Valor em BRL. Positivo para débitos, negativo para estornos.
- **Propósito de Negócio**: Representa o valor monetário da transação.
- **Comportamento Esperado**: Deve ser um número decimal representando o valor da transação.
- **Anomalias**: Tipo de dado incorreto (`VARCHAR` em vez de `float`), o que pode afetar cálculos financeiros.

### `tp_transacao`
- **Tipo**: `string`
- **Nullable**: `false`
- **Descrição**: Tipo da operação. Dominio: COMPRA, SAQUE, TED, PIX, PAGAMENTO_BOLETO, ESTORNO.
- **Propósito de Negócio**: Classifica o tipo de transação realizada.
- **Comportamento Esperado**: Deve corresponder a um dos tipos de operação definidos no domínio.
- **Anomalias**: Nenhuma anomalia observada.

### `cd_estabelecimento`
- **Tipo**: `string`
- **Nullable**: `true`
- **Descrição**: CNPJ do estabelecimento. Nulo para compras online não identificadas (~6%).
- **Propósito de Negócio**: Identifica o estabelecimento associado à transação.
- **Comportamento Esperado**: Deve ser um CNPJ válido ou nulo para transações online não identificadas.
- **Anomalias**: 6.5% de valores nulos observados, ligeiramente acima do esperado (~6%).

### `fl_suspeita`
- **Tipo**: `string` (deveria ser `boolean`)
- **Nullable**: `false`
- **Descrição**: Flag do motor antifraude. True indica transação em análise (~4% do volume).
- **Propósito de Negócio**: Indica se a transação está sendo analisada pelo motor antifraude.
- **Comportamento Esperado**: Deve ser `true` ou `false`.
- **Anomalias**: Tipo de dado incorreto (`VARCHAR` em vez de `boolean`), o que pode afetar a lógica de detecção de fraude.

### `cd_canal`
- **Tipo**: `string`
- **Nullable**: `false`
- **Descrição**: Canal de origem. Dominio: APP, INTERNET, AGENCIA, ATM, POS.
- **Propósito de Negócio**: Identifica o canal através do qual a transação foi realizada.
- **Comportamento Esperado**: Deve corresponder a um dos canais definidos no domínio.
- **Anomalias**: Nenhuma anomalia observada.

## Implicações de Compliance

- **BACEN_4658**: Requer que todas as transações sejam registradas com precisão e que os dados sejam mantidos por um período mínimo de 7 anos.
- **PCI_DSS**: Exige que dados sensíveis, como informações de transação, sejam protegidos contra acesso não autorizado.

## Pontos de Atenção

1. **Duplicatas em `id_transacao`**: 2% de duplicatas observadas, o que excede o limite de tolerância.
2. **Tipos de Dados Incorretos**: `dt_transacao`, `vl_transacao` e `fl_suspeita` estão armazenados como `VARCHAR` em vez de `date`, `float` e `boolean`, respectivamente.
3. **Valores Nulos em `cd_estabelecimento`**: 6.5% de valores nulos observados, ligeiramente acima do esperado (~6%).
4. **Alta Concentração de Transações por Cliente**: Alguns clientes têm um número significativo de transações, o que pode indicar padrões incomuns ou potencial fraude.

---

> **[AI_METADATA_STATUS: DRAFT]** — Documentação gerada por SLM. Requer validação humana pelo Data Steward responsável antes de uso em produção.