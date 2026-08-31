# Dicionário Técnico: tb_contratos_credito

## Visão Geral

A tabela `tb_contratos_credito` contém dados sobre contratos de produtos de crédito ativos e encerrados. Ela é gerida pela equipe de crédito e alimenta o Sistema de Controle de Risco (SCR) mensalmente. A tabela é atualizada diariamente e é classificada como restrita, com uma retenção de dados de 10 anos. As informações são extraídas do sistema `SISTEMA_CREDITO_SAS` no formato `sas7bdat`.

### Contexto de Negócio

Os contratos de crédito cobrem todos os produtos oferecidos pelo banco. O valor utilizado (`vl_utilizado`) pode exceder o valor limite (`vl_limite`) em até 15% para produtos com tolerância de limite, como o cheque especial. O status `EM_ATRASO` dispara uma cobrança automática após D+1.

### Regulamentação

A tabela possui tags regulatórias como SCR, BACEN_4658 e LGPD, indicando a necessidade de conformidade com regulamentos de controle de risco, normas do Banco Central e proteção de dados pessoais.

## Colunas

### id_contrato

- **Tipo**: String
- **Nullable**: Não
- **Descrição**: Identificador único do contrato gerado pelo sistema de crédito.
- **SAS Label**: ID CONTRATO CREDITO
- **Propósito de Negócio**: Serve como chave primária para identificar exclusivamente cada contrato.
- **Comportamento Esperado**: Deve ser único e não nulo para cada registro.
- **Estatísticas**: 299 valores únicos, 0% de nulos.

### cd_cliente

- **Tipo**: String
- **Nullable**: Não
- **Descrição**: Referência ao cliente em `tb_clientes`.
- **Propósito de Negócio**: Liga o contrato ao cliente correspondente.
- **Comportamento Esperado**: Deve corresponder a um cliente válido na tabela `tb_clientes`.
- **Estatísticas**: 299 valores únicos, 0% de nulos.

### dt_contrato

- **Tipo**: Date
- **Nullable**: Não
- **Descrição**: Data de abertura do contrato.
- **Propósito de Negócio**: Indica quando o contrato foi formalizado.
- **Comportamento Esperado**: Deve ser uma data válida e não nula.
- **Estatísticas**: 282 valores únicos, 0% de nulos.

### vl_limite

- **Tipo**: Float
- **Nullable**: Não
- **Descrição**: Limite de crédito aprovado em BRL.
- **Propósito de Negócio**: Define o limite máximo de crédito disponível para o cliente.
- **Comportamento Esperado**: Deve ser um valor positivo e não nulo.
- **Estatísticas**: Min: 1065.12, Max: 99779.85, Média: 52944.0009, 0% de nulos.
- **Implicações Regulatórias**: Candidato ao SCR.

### vl_utilizado

- **Tipo**: Float
- **Nullable**: Não
- **Descrição**: Saldo utilizado atual em BRL. Pode exceder `vl_limite` em produtos com tolerância.
- **Propósito de Negócio**: Reflete o saldo atual utilizado pelo cliente.
- **Comportamento Esperado**: Deve ser um valor positivo e não nulo. Pode exceder `vl_limite` em até 15% para produtos como cheque especial.
- **E

---
> **[AI_METADATA_STATUS: DRAFT]**