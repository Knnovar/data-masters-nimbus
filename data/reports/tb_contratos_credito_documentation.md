# Dicionário Técnico da Tabela `tb_contratos_credito`

## Visão Geral

A tabela `tb_contratos_credito` armazena informações sobre contratos de produtos de crédito ativos e encerrados, conforme descrito no contrato YAML. Ela é gerida pela equipe `squad-credito` e alimenta o Sistema de Controle de Risco (SCR) mensalmente. A tabela está em formato SAS7BDAT com codificação Latin-1 e atualiza-se diariamente.

### Contexto de Negócio

Os contratos de crédito incluem todos os produtos oferecidos pelo banco, como cartão de crédito, cheque especial, crédito pessoal, financiamento veicular e consignado. A tabela suporta regras específicas, como o valor utilizado (`vl_utilizado`) podendo exceder o limite aprovado (`vl_limite`) em até 15% para produtos com tolerância de limite (ex: cheque especial). Além disso, um contrato com status `EM_ATRASO` desencadeia uma cobrança automática após D+1.

### Regulamentação e Compliance

A tabela está sujeita a várias regulamentações:
- **SCR**: Candidato para inclusão no SCR.
- **BACEN_4658**: Normas do Banco Central do Brasil.
- **LGPD**: Lei Geral de Proteção de Dados.

Os dados são classificados como restritos e têm uma retenção obrigatória de 10 anos. Qualquer análise ou uso deve considerar essas regulamentações para garantir conformidade.

## Colunas da Tabela

### `id_contrato`
- **Tipo**: String
- **Descrição**: Identificador único do contrato gerado pelo sistema de crédito.
- **Comportamento Esperado**: Não nulo, chave primária. Cada valor é único conforme as estatísticas (100% de unicidade).
- **Anomalias**: Nenhuma observada.

### `cd_cliente`
- **Tipo**: String
- **Descrição**: Referência ao cliente na tabela `tb_clientes`.
- **Comportamento Esperado**: Não nulo. Deve corresponder a um identificador válido em `tb_clientes`.
- **Anomalias**: Alta duplicidade observada (213 únicos de 300 registros).

### `dt_contrato`
- **Tipo**: String
- **Descrição**: Data de abertura do contrato.
- **Comportamento Esperado**: Não nulo. Deve ser uma data válida no formato apropriado.
- **Anomalias**: Tratada como string; deve ser convertida para tipo `date`.

### `vl_limite`
- **Tipo**: String
- **Descrição**: Limite de crédito aprovado em BRL.
- **Comportamento Esperado**: Não nulo. Deve representar um valor monetário válido.
- **Anomalias**: Tratada como string; deve ser convertida para tipo `float`.

### `vl_utilizado`
- **Tipo**: String
- **Descrição**: Saldo utilizado atual em BRL. Pode exceder o limite aprovado em até 15% para produtos com tolerância.
- **Comportamento Esperado**: Não nulo. Deve ser um valor monetário válido e respeitar as regras de tolerância.
- **Anomalias**: Tratada como string; deve ser convertida para tipo `float`.

### `tp_produto`
- **Tipo**: String
- **Descrição**: Tipo do produto de crédito. Domínio: CARTAO_CREDITO, CHEQUE_ESPECIAL, CREDITO_PESSOAL, FIN

---
> **[AI_METADATA_STATUS: DRAFT]**