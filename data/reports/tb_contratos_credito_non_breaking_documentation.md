# Dicionário Técnico da Tabela `tb_contratos_credito_non_breaking`

## Visão Geral

A tabela `tb_contratos_credito_non_breaking` contém dados sobre contratos de produtos de crédito ativos e encerrados, conforme descrito no contrato YAML. Ela alimenta o Sistema de Controle de Risco (SCR) mensalmente e é gerida pela equipe `squad-credito`. A tabela está em formato SAS (`sas7bdat`) e é atualizada diariamente.

### Contexto de Negócio

Os contratos incluem todos os produtos oferecidos pelo banco, com tolerância específica para o valor utilizado exceder o limite aprovado até 15% para produtos como cheque especial. O status `EM_ATRASO` desencadeia uma cobrança automática após D+1.

### Regulamentação e Classificação de Dados

- **Tags Regulatórias**: SCR, BACEN_4658, LGPD
- **Classificação de Dados**: Restrita
- **Período de Retenção**: 10 anos

## Colunas da Tabela

### `id_contrato`

- **Tipo**: String
- **Descrição**: Identificador único do contrato gerado pelo sistema de crédito.
- **Comportamento Esperado**: Não nulo, chave primária. Cada valor é único conforme as estatísticas (unique_count: 299).
- **SAS Label**: ID CONTRATO CREDITO

### `cd_cliente`

- **Tipo**: String
- **Descrição**: Referência ao cliente em `tb_clientes`.
- **Comportamento Esperado**: Não nulo, deve corresponder a um registro válido na tabela de clientes.
- **Estatísticas**: Todos os valores são únicos (unique_count: 299).

### `dt_contrato`

- **Tipo**: Date
- **Descrição**: Data de abertura do contrato.
- **Comportamento Esperado**: Não nulo, deve ser uma data válida e coerente com o contexto do negócio.
- **Estatísticas**: Alta variabilidade nas datas (unique_count: 284).

### `vl_limite`

- **Tipo**: Float
- **Descrição**: Limite de crédito aprovado em BRL.
- **Comportamento Esperado**: Não nulo, valores positivos. Candidato para SCR.
- **Estatísticas**: Variação significativa nos valores (min: 869.5, max: 99856.72).

### `vl_utilizado`

- **Tipo**: Float
- **Descrição**: Saldo utilizado atual em BRL. Pode exceder o limite aprovado para produtos com tolerância.
- **Comportamento Esperado**: Não nulo, valores positivos. Para cheque especial, pode ser até 15% acima do `vl_limite`.
- **Estatísticas**: Variação significativa nos valores (min: 93382.1, max: 15481.19).

### `tp_produto`

- **Tipo**: String
- **Descrição**: Tipo do produto de crédito. Domínio: CARTAO_CREDITO, CHEQUE_ESPECIAL, CREDITO_PESSOAL, FINANCIAMENTO_VEICULO, CONSIGNADO.
- **Comportamento Esperado**: Não nulo, deve corresponder a um dos tipos definidos no domínio.

### `cd_status`

- **Tipo**: String
- **Descrição**: Status do contrato. Domínio: ATIVO, ENCERRADO, EM_ATRASO, RENEGOCIADO.
- **Comportamento Esperado**: Não nulo, deve corresponder a um dos status definidos

---
> **[AI_METADATA_STATUS: DRAFT]**