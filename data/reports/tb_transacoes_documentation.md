# Dicionário Técnico da Tabela `tb_transacoes`

## Visão Geral

A tabela `tb_transacoes` registra todas as movimentações financeiras por canal de atendimento, conforme descrito no contrato de dados. Ela é gerida pela equipe `squad-transacoes` e está atualmente em versão 2.3.1. A tabela é alimentada por um sistema chamado `SWITCH_TRANSACIONAL` e é atualizada de forma event-driven. As transações são classificadas como confidenciais e devem ser retidas por 7 anos, conforme as regulamentações BACEN_4658 e PCI_DSS.

## Colunas

### `id_transacao`
- **Tipo**: String
- **Nullable**: Não
- **Descrição**: UUID da transação gerado pelo switch transacional no momento da operação.
- **Propósito de Negócio**: Identificador único para cada transação.
- **Comportamento Esperado**: Deve ser único para cada transação.
- **Anomalias**: 2% de duplicatas observadas, o que excede o limite tolerado de 0% de duplicatas.

### `cd_cliente`
- **Tipo**: String
- **Nullable**: Não
- **Descrição**: Referência ao cliente em `tb_clientes`.
- **Propósito de Negócio**: Identifica o cliente associado à transação.
- **Comportamento Esperado**: Deve corresponder a um cliente válido na tabela `tb_clientes`.
- **Anomalias**: Nenhuma anomalia observada.

### `dt_transacao`
- **Tipo**: String (deveria ser Date)
- **Nullable**: Não
- **Descrição**: Data da transação no fuso horário America/Sao_Paulo.
- **Propósito de Negócio**: Registro da data em que a transação ocorreu.
- **Comportamento Esperado**: Deve estar no formato de data válido.
- **Anomalias**: Tipo de dado incorreto (VARCHAR em vez de DATE).

### `vl_transacao`
- **Tipo**: String (deveria ser Float)
- **Nullable**: Não
- **Descrição**: Valor em BRL. Positivo para débitos, negativo para estornos.
- **Propósito de Negócio**: Valor monetário da transação.
- **Comportamento Esperado**: Deve ser um número válido representando o valor da transação.
- **Anomalias**: Tipo de dado incorreto (VARCHAR em vez de FLOAT).

### `tp_transacao`
- **Tipo**: String
- **Nullable**: Não
- **Descrição**: Tipo da operação. Domínio: COMPRA, SAQUE, TED, PIX, PAGAMENTO_BOLETO, ESTORNO.
- **Propósito de Negócio**: Identifica o tipo de transação.
- **Comportamento Esperado**: Deve ser um dos valores permitidos no domínio.
- **Anomalias**: Nenhuma anomalia observada.

### `cd_estabelecimento`
- **Tipo**: String
- **Nullable**: Sim
- **Descrição**: CNPJ do estabelecimento. Nulo para compras online não identificadas (~6%).
- **Propósito de Negócio**: Identifica o estabelecimento associado à transação.
- **Comportamento Esperado**: Pode ser nulo para transações online não identificadas.
- **Anomalias**: 6.5% de valores nulos observados, ligeiramente acima do esperado (~6%).

### `fl_suspeita`
- **Tipo**: String (deveria ser Boolean)
- **Nullable**: Não
- **Descrição**: Flag do motor antifraude. True indica transação em análise (~4% do volume).
- **Propósito de Negócio**: Indica se a transação está sendo analisada por fraude.
- **Comportamento Esperado**: Deve ser um valor booleano.
- **Anomalias**: Tipo de dado incorreto (VARCHAR em vez de BOOLEAN).

### `cd_canal`
- **Tipo**: String
- **Nullable**: Não
- **Descrição**: Canal de origem. Domínio: APP, INTERNET, AGENCIA, ATM, POS.
- **Propósito de Negócio**: Identifica o canal através do qual a transação foi realizada.
- **Comportamento Esperado**: Deve ser um dos valores permitidos no domínio.
- **Anomalias**: Nenhuma anomalia observada.

## Considerações Regulatórias

- **Regulatory Tags**: BACEN_4658 e PCI_DSS.
- **Implicações de Compliance**: A tabela contém dados financeiros confidenciais que devem ser protegidos e armazenados conforme as regulamentações mencionadas. A presença de transações suspeitas (fl_suspeita) requer análise e ação conforme procedimentos de compliance.

## Pontos de Atenção

1. **Duplicatas em `id_transacao`**: 2% de duplicatas observadas, o que excede o limite tolerado de 0%.
2. **Tipos de Dados Incorretos**: `dt_transacao`, `vl_transacao` e `fl_suspeita` estão armazenados como VARCHAR em vez de seus tipos esperados (DATE, FLOAT e BOOLEAN, respectivamente).
3. **Valores Nulos em `cd_estabelecimento`**: 6.5% de valores nulos observados, ligeiramente acima do esperado (~6%).
4. **Compliance**: Garantir que as transações suspeitas sejam devidamente analisadas e que os dados sejam protegidos conforme as regulamentações BACEN_4658 e PCI_DSS.

---

> **[AI_METADATA_STATUS: DRAFT]** — Documentação gerada por SLM. Requer validação humana pelo Data Steward responsável antes de uso em produção.