# Dicionário Técnico da Tabela `tb_contratos_credito`

## Visão Geral

A tabela `tb_contratos_credito` contém informações sobre contratos de produtos de crédito ativos e encerrados. Ela é gerida pela equipe `squad-credito` e alimenta o Sistema de Controle de Risco (SCR) mensalmente. A tabela está em formato `sas7bdat` e é atualizada diariamente. A classificação de dados é restrita, com uma retenção de 10 anos, conforme as regulamentações `SCR`, `BACEN_4658` e `LGPD`.

## Colunas

### `id_contrato`
- **Tipo**: `string`
- **Nullable**: Não
- **Descrição**: Identificador único do contrato gerado pelo sistema de crédito.
- **SAS Label**: ID CONTRATO CREDITO
- **Estatísticas**:
  - **Dtype**: `VARCHAR`
  - **Null Pct**: 0.0%
  - **Unique Count**: 300
- **Observações**: Serve como chave primária. Não há anomalias observadas.

### `cd_cliente`
- **Tipo**: `string`
- **Nullable**: Não
- **Descrição**: Referência ao cliente em `tb_clientes`.
- **Estatísticas**:
  - **Dtype**: `VARCHAR`
  - **Null Pct**: 0.0%
  - **Unique Count**: 213
  - **Top Values**: Algumas duplicatas observadas, indicando múltiplos contratos por cliente.
- **Observações**: A presença de duplicatas é esperada e não viola as regras de tolerância.

### `dt_contrato`
- **Tipo**: `date`
- **Nullable**: Não
- **Descrição**: Data de abertura do contrato.
- **Estatísticas**:
  - **Dtype**: `VARCHAR`
  - **Null Pct**: 0.0%
  - **Unique Count**: 280
- **Observações**: A coluna está armazenada como `VARCHAR`, o que pode indicar um problema de formatação de data.

### `vl_limite`
- **Tipo**: `float`
- **Nullable**: Não
- **Descrição**: Limite de crédito aprovado em BRL.
- **SAS Label**: VALOR LIMITE APROVADO
- **Regulatory Flags**: SCR_CANDIDATE
- **Estatísticas**:
  - **Dtype**: `VARCHAR`
  - **Null Pct**: 0.0%
  - **Min**: 1211.66
  - **Max**: 99512.12
  - **Mean**: 52329.4574
- **Observações**: A coluna está armazenada como `VARCHAR`, o que pode indicar um problema de formatação numérica.

### `vl_utilizado`
- **Tipo**: `float`
- **Nullable**: Não
- **Descrição**: Saldo utilizado atual em BRL. Pode exceder `vl_limite` em produtos com tolerância.
- **SAS Label**: VALOR UTILIZADO ATUAL
- **Regulatory Flags**: SCR_CANDIDATE
- **Business Rules**: Pode ser até 15% acima de `vl_limite` para `CHEQUE_ESPECIAL`.
- **Estatísticas**:
  - **Dtype**: `VARCHAR`
  - **Null Pct**: 0.0%
  - **Min**: 70.63
  - **Max**: 109174.48
  - **Mean**: 30840.8548
- **Observações**: A coluna está armazenada como `VARCHAR`, o que pode indicar um problema de formatação numérica.

### `tp_produto`
- **Tipo**: `string`
- **Nullable**: Não
- **Descrição**: Tipo do produto de crédito. Dominio: `CARTAO_CREDITO`, `CHEQUE_ESPECIAL`, `CREDITO_PESSOAL`, `FINANCIAMENTO_VEICULO`, `CONSIGNADO`.
- **Estatísticas**:
  - **Dtype**: `VARCHAR`
  - **Null Pct**: 0.0%
  - **Unique Count**: 5
- **Observações**: Nenhuma anomalia observada.

### `cd_status`
- **Tipo**: `string`
- **Nullable**: Não
- **Descrição**: Status do contrato. Dominio: `ATIVO`, `ENCERRADO`, `EM_ATRASO`, `RENEGOCIADO`.
- **Business Rules**: `EM_ATRASO` dispara cobrança automática após D+1.
- **Estatísticas**:
  - **Dtype**: `VARCHAR`
  - **Null Pct**: 0.0%
  - **Unique Count**: 4
- **Observações**: Nenhuma anomalia observada.

### `dt_vencimento`
- **Tipo**: `date`
- **Nullable**: Não
- **Descrição**: Data de vencimento da última parcela ou do contrato.
- **Estatísticas**:
  - **Dtype**: `VARCHAR`
  - **Null Pct**: 0.0%
  - **Unique Count**: 269
- **Observações**: A coluna está armazenada como `VARCHAR`, o que pode indicar um problema de formatação de data.

### `nr_parcelas`
- **Tipo**: `integer`
- **Nullable**: Não
- **Descrição**: Número total de parcelas do contrato. 1 para crédito rotativo.
- **Estatísticas**:
  - **Dtype**: `VARCHAR`
  - **Null Pct**: 0.0%
  - **Min**: 1.0
  - **Max**: 60.0
  - **Mean**: 30.01
- **Observações**: A coluna está armazenada como `VARCHAR`, o que pode indicar um problema de formatação numérica.

### `tx_juros_am`
- **Tipo**: `float`
- **Nullable**: Não
- **Descrição**: Taxa de juros ao mês em percentual. Ex: 2.5 = 2,5% a.m.
- **SAS Label**: TAXA JUROS MENSAL
- **Estatísticas**:
  - **Dtype**: `VARCHAR`
  - **Null Pct**: 0.0%
  - **Min**: 0.8133
  - **Max**: 8.4875
  - **Mean**: 4.6899
- **Observações**: A coluna está armazenada como `VARCHAR`, o que pode indicar um problema de formatação numérica.

## Regulamentações e Compliance

- **Classificação de Dados**: Restrita
- **Regulamentações**: `SCR`, `BACEN_4658`, `LGPD`
- **Retenção de Dados**: 10 anos

## Pontos de Atenção

- **Formato de Dados**: Múltiplas colunas (`dt_contrato`, `vl_limite`, `vl_utilizado`, `dt_vencimento`, `nr_parcelas`, `tx_juros_am`) estão armazenadas como `VARCHAR`, indicando potenciais problemas de formatação.
- **Duplicatas**: A coluna `cd_cliente` apresenta duplicatas, o que é esperado e não viola as regras de tolerância.
- **Compliance**: A tabela está sujeita a regulamentações rigorosas, incluindo `LGPD`, exigindo cuidado na manipulação e armazenamento dos dados.

---

> **[AI_METADATA_STATUS: DRAFT]** — Documentação gerada por SLM. Requer validação humana pelo Data Steward responsável antes de uso em produção.