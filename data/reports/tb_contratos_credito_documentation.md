# Dicionário Técnico da Tabela `tb_contratos_credito`

## Visão Geral

A tabela `tb_contratos_credito` contém informações sobre contratos de produtos de crédito ativos e encerrados. Ela é gerida pela equipe `squad-credito` e está em versão `3.0.0`. A tabela é alimentada diariamente pelo sistema `SISTEMA_CREDITO_SAS` e utiliza o formato `sas7bdat` com codificação `latin-1` em um sistema operacional `unix`. A tabela é classificada como restrita e deve ser retenida por 10 anos, conforme as regulamentações `SCR`, `BACEN_4658` e `LGPD`.

### Propósito de Negócio

A tabela serve para armazenar dados sobre contratos de crédito de todos os produtos oferecidos pelo banco. Esses dados são utilizados para alimentar o SCR (Score de Crédito) mensalmente. Além disso, a tabela suporta regras de negócio específicas, como a possibilidade de o valor utilizado (`vl_utilizado`) exceder o valor limite (`vl_limite`) em até 15% para produtos com tolerância de limite, como o cheque especial. O status `EM_ATRASO` dispara cobrança automática após D+1.

### Colunas

#### `id_contrato`
- **Tipo**: string
- **Nullable**: false
- **Descrição**: Identificador único do contrato gerado pelo sistema de crédito.
- **Comportamento Esperado**: Deve ser único e não nulo.
- **Anomalias**: Nenhuma observada, conforme estatísticas.

#### `cd_cliente`
- **Tipo**: string
- **Nullable**: false
- **Descrição**: Referência ao cliente em `tb_clientes`.
- **Comportamento Esperado**: Deve ser único e não nulo.
- **Anomalias**: Nenhuma observada, conforme estatísticas.

#### `dt_contrato`
- **Tipo**: date
- **Nullable**: false
- **Descrição**: Data de abertura do contrato.
- **Comportamento Esperado**: Deve ser uma data válida e não nula.
- **Anomalias**: Nenhuma observada, conforme estatísticas.

#### `vl_limite`
- **Tipo**: float
- **Nullable**: false
- **Descrição**: Limite de crédito aprovado em BRL.
- **Comportamento Esperado**: Deve ser um valor monetário não nulo.
- **Anomalias**: Nenhuma observada, conforme estatísticas.
- **Implicações de Compliance**: Candidato ao SCR.

#### `vl_utilizado`
- **Tipo**: float
- **Nullable**: false
- **Descrição**: Saldo utilizado atual em BRL. Pode exceder `vl_limite` em produtos com tolerância.
- **Comportamento Esperado**: Deve ser um valor monetário não nulo.
- **Anomalias**: Nenhuma observada, conforme estatísticas.
- **Regras de Negócio**: Pode ser até 15% acima de `vl_limite` para `CHEQUE_ESPECIAL`.
- **Implicações de Compliance**: Candidato ao SCR.

#### `tp_produto`
- **Tipo**: string
- **Nullable**: false
- **Descrição**: Tipo do produto de crédito. Dominio: `CARTAO_CREDITO`, `CHEQUE_ESPECIAL`, `CREDITO_PESSOAL`, `FINANCIAMENTO_VEICULO`, `CONSIGNADO`.
- **Comportamento Esperado**:

---
> **[AI_METADATA_STATUS: DRAFT]**