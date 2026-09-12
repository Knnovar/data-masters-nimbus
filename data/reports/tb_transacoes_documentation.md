# Dicionário Técnico da Tabela `tb_transacoes`

## Visão Geral

A tabela `tb_transacoes` registra todas as movimentações financeiras realizadas por diferentes canais de atendimento. Ela é essencial para o monitoramento e análise de transações, incluindo a identificação de transações suspeitas pelo motor antifraude. A tabela é mantida pelo `squad-transacoes` e está em conformidade com as regulamentações BACEN_4658 e PCI_DSS, sendo classificada como confidencial e com uma retenção de dados de 7 anos.

## Colunas

### `id_transacao`
- **Tipo**: `string`
- **Nullable**: Não
- **Descrição**: UUID da transação gerado pelo switch transacional no momento da operação.
- **Propósito de Negócio**: Identificador único para cada transação.
- **Comportamento Esperado**: Deve ser único para cada transação.
- **Anomalias**: 2% de duplicatas observadas, o que excede o limite permitido de 0% de duplicatas.

### `cd_cliente`
- **Tipo**: `string`
- **Nullable**: Não
- **Descrição**: Referência ao cliente em `tb_clientes`.
- **Propósito de Negócio**: Identifica o cliente associado à transação.
- **Comportamento Esperado**: Deve corresponder a um cliente válido na tabela `tb_clientes`.
- **Anomalias**: Alta frequência de valores repetidos, indicando transações múltiplas por cliente.

### `dt_transacao`
- **Tipo**: `string`
- **Nullable**: Não
- **Descrição**: Data da transação no fuso horário America/Sao_Paulo.
- **Propósito de Negócio**: Registro do momento exato da transação.
- **Comportamento Esperado**: Deve estar no formato de data e corresponder ao fuso horário especificado.
- **Anomalias**: Dados de tipo `VARCHAR` em vez de `date`, o que pode causar problemas de análise.

### `vl_transacao`
- **Tipo**: `string`
- **Nullable**: Não
- **Descrição**: Valor em BRL. Positivo para débitos, negativo para estornos.
- **Propósito de Negócio**: Representa o valor monetário da transação.
- **Comportamento Esperado**: Deve ser um número válido em BRL.
- **Anomalias**: Dados de tipo `VARCHAR` em vez de `float`, o que pode causar problemas de análise.

### `tp_transacao`
- **Tipo**: `string`
- **Nullable**: Não
- **Descrição**: Tipo da operação. Dominio: COMPRA, SAQUE, TED, PIX, PAGAMENTO_BOLETO, ESTORNO.
- **Propósito de Negócio**: Identifica o tipo de transação realizada.
- **Comportamento Esperado**: Deve corresponder a um dos tipos de operação definidos.
- **Anomalias**: Nenhuma anomalia observada.

### `cd_estabelecimento`
- **Tipo**: `string`
- **Nullable**: Sim
- **Descrição**: CNPJ do estabelecimento. Nulo para compras online não identificadas (~6%).
- **Propósito de Negócio**: Identifica o estabelecimento associado à transação.
- **Comportamento Esperado**: Deve ser um CNPJ válido ou nulo para transações online não identificadas.
- **Anomalias**: 6.5% de valores nulos, ligeiramente acima do esperado (~6%).

### `fl_suspeita`
- **Tipo**: `string`
- **Nullable**: Não
- **Descrição**: Flag do motor antifraude. True indica transação em análise (~4% do volume).
- **Propósito de Negócio**: Indica se a transação está sob análise por suspeita de fraude.
- **Comportamento Esperado**: Deve ser `true` ou `false`.
- **Anomalias**: 3.8% das transações marcadas como suspeitas, dentro do esperado (~4%).

### `cd_canal`
- **Tipo**: `string`
- **Nullable**: Não
- **Descrição**: Canal de origem. Dominio: APP, INTERNET, AGENCIA, ATM, POS.
- **Propósito de Negócio**: Identifica o canal através do qual a transação foi realizada.
- **Comportamento Esperado**: Deve corresponder a um dos canais definidos.
- **Anomalias**: Nenhuma anomalia observada.

## Considerações Regulatórias

A tabela está sujeita às regulamentações BACEN_4658 e PCI_DSS, o que implica requisitos rigorosos de segurança e privacidade dos dados. A classificação de confidencialidade exige medidas adequadas de proteção de dados.

## Pontos de Atenção

1. **Duplicatas em `id_transacao`**: A presença de duplicatas viola a restrição de unicidade e pode comprometer a integridade dos dados.
2. **Tipo de Dados Incorreto**: As colunas `dt_transacao` e `vl_transacao` estão registradas como `VARCHAR` em vez de `date` e `float`, respectivamente, o que pode causar problemas de análise e processamento.
3. **Frequência de Nulos em `cd_estabelecimento`**: A porcentagem de nulos está ligeiramente acima do esperado, o que pode indicar problemas na identificação de estabelecimentos para transações online.
4. **Compliance Regulatória**: Devido à classificação de confidencialidade, é crucial garantir que as medidas de segurança estejam alinhadas com as regulamentações BACEN_4658 e PCI_DSS.

---

> **[AI_METADATA_STATUS: DRAFT]** — Documentação gerada por SLM. Requer validação humana pelo Data Steward responsável antes de uso em produção.