# Dicionário Técnico da Tabela `tb_transacoes`

## Visão Geral

A tabela `tb_transacoes` registra todas as movimentações financeiras por canal de atendimento do banco. Ela é gerida pela equipe `squad-transacoes` e está em versão `2.3.1`. A tabela é alimentada por um sistema chamado `SWITCH_TRANSACIONAL` e armazena dados em formato CSV com codificação UTF-8. A atualização dos dados é event-driven, e o sistema operacional utilizado é Unix. O contato para questões relacionadas é `squad-transacoes@banco.com.br`.

### Contexto de Negócio

- **Registro de Movimentações**: A tabela captura todas as transações financeiras realizadas através de diferentes canais.
- **Flag de Transações Suspeitas**: O campo `fl_suspeita` indica se uma transação está sendo analisada pelo motor antifraude.
- **Estabelecimento Não Identificado**: O campo `cd_estabelecimento` pode ser nulo para compras online não identificadas, o que ocorre em aproximadamente 6% das transações.

### Regulamentações e Compliance

- **Tags Regulatórias**: A tabela está sujeita às normas `BACEN_4658` e `PCI_DSS`.
- **Classificação de Dados**: Os dados são classificados como confidenciais.
- **Período de Retenção**: Os dados devem ser mantidos por 7 anos.

### Tolerância e Dependências

- **Tolerância a Nulos**: O máximo permitido de nulos é de 10%.
- **Duplicatas**: Não são permitidas duplicatas.
- **Dependências**: A tabela depende da tabela `tb_clientes` para referenciar clientes.

## Descrição das Colunas

### `id_transacao`

- **Tipo**: `string`
- **Nullable**: Não
- **Descrição**: UUID da transação, gerado pelo switch transacional no momento da operação.
- **Comportamento Esperado**: Deve ser único para cada transação.
- **Anomalias**: A presença de duplicatas (2 registros) indica uma anomalia que deve ser investigada.

### `cd_cliente`

- **Tipo**: `string`
- **Nullable**: Não
- **Descrição**: Referência ao cliente em `tb_clientes`.
- **Comportamento Esperado**: Deve corresponder a um cliente válido na tabela `tb_clientes`.
- **Anomalias**: Alta frequência de valores repetidos pode indicar padrões de uso ou erros de entrada.

### `dt_transacao`

- **Tipo**: `string` (deveria ser `date`)
- **Nullable**: Não
- **Descrição**: Data da transação no fuso horário America/Sao_Paulo.
- **Comportamento Esperado**: Deve estar no formato de data e corresponder ao fuso horário especificado.
- **Anomalias**: A coluna está como `VARCHAR`, o que pode causar problemas de validação e formatação.

### `vl_transacao`

- **Tipo**: `string` (deveria ser `float`)
- **Nullable**: Não
- **Descrição**: Valor em BRL. Positivo para débitos, negativo para estornos.
- **Comportamento Esperado**: Deve ser um número decimal representando o valor da transação.
- **Anomalias**: A coluna está como `VARCHAR`, o que pode causar problemas de cálculo e análise.

### `tp_transacao`

- **Tipo**: `string`
- **Nullable**: Não
- **Descrição**: Tipo da operação. Dominio: COMPRA, SAQUE, TED, PIX, PAGAMENTO_BOLETO, ESTORNO.
- **Comportamento Esperado**: Deve conter apenas valores do domínio especificado.
- **Anomalias**: Nenhuma anomalia detectada.

### `cd_estabelecimento`

- **Tipo**: `string`
- **Nullable**: Sim
- **Descrição**: CNPJ do estabelecimento. Nulo para compras online não identificadas (~6%).
- **Comportamento Esperado**: Deve ser um CNPJ válido ou nulo.
- **Anomalias**: Nenhuma anomalia detectada, mas o percentual de nulos está próximo do esperado.

### `fl_suspeita`

- **Tipo**: `string` (deveria ser `boolean`)
- **Nullable**: Não
- **Descrição**: Flag do motor antifraude. True indica transação em análise (~4% do volume).
- **Comportamento Esperado**: Deve ser `true` ou `false`.
- **Anomalias**: A coluna está como `VARCHAR`, o que pode causar problemas de lógica booleana.

### `cd_canal`

- **Tipo**: `string`
- **Nullable**: Não
- **Descrição**: Canal de origem. Dominio: APP, INTERNET, AGENCIA, ATM, POS.
- **Comportamento Esperado**: Deve conter apenas valores do domínio especificado.
- **Anomalias**: Nenhuma anomalia detectada.

## Pontos de Atenção

1. **Duplicatas em `id_transacao`**: A presença de duplicatas é uma anomalia crítica que deve ser investigada e corrigida.
2. **Tipos de Dados**: Múltiplas colunas (`dt_transacao`, `vl_transacao`, `fl_suspeita`) estão com tipos de dados incorretos (`VARCHAR` em vez de `date`, `float`, `boolean` respectivamente). Isso pode causar problemas de validação, formatação e análise.
3. **Comportamento de `cd_estabelecimento`**: O percentual de nulos está próximo do esperado, mas deve ser monitorado para garantir que não ultrapasse o limite aceitável.
4. **Compliance Regulatório**: A tabela está sujeita a normas regulatórias rigorosas (`BACEN_4658` e `PCI_DSS`), portanto, qualquer anomalia deve ser tratada com prioridade para evitar penalidades.
5. **Dependência de `tb_clientes`**: Qualquer inconsistência na tabela `tb_clientes` pode afetar a integridade dos dados em `tb_transacoes`.

---

> **[AI_METADATA_STATUS: DRAFT]** — Documentação gerada por SLM. Requer validação humana pelo Data Steward responsável antes de uso em produção.