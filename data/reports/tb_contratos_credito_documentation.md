# Dicionário Técnico: tb_contratos_credito

## Visão Geral

A tabela `tb_contratos_credito` contém informações sobre contratos de produtos de crédito ativos e encerrados. Ela é gerida pela equipe `squad-credito` e está em versão 3.0.0. Os dados são extraídos diariamente do sistema `SISTEMA_CREDITO_SAS` no formato `sas7bdat` e codificados em `latin-1`. A tabela alimenta o SCR (Sistema de Controle de Risco) mensalmente e está sujeita a restrições de classificação de dados e retenção por 10 anos.

### Contexto de Negócio

Os contratos de crédito incluem todos os produtos oferecidos pelo banco. O valor utilizado (`vl_utilizado`) pode exceder o valor limite (`vl_limite`) em até 15% para produtos com tolerância de limite, como o cheque especial. O status `EM_ATRASO` dispara uma cobrança automática após D+1.

### Regulamentações e Compliance

- **Tags Regulatórias**: SCR, BACEN_4658, LGPD
- **Classificação de Dados**: Restrita
- **Implicações de Compliance**: Os campos `vl_limite` e `vl_utilizado` são candidatos ao SCR, exigindo monitoramento rigoroso para garantir conformidade com regulamentações financeiras.

## Esquema de Colunas

### id_contrato
- **Tipo**: string
- **Nullable**: false
- **Descrição**: Identificador único do contrato gerado pelo sistema de crédito.
- **Comportamento Esperado**: Deve ser único e não nulo.
- **Observações**: Correspondente ao `B04EADA8-18AD-49` no Data Profiler, com 299 valores únicos e 0% de nulos.

### cd_cliente
- **Tipo**: string
- **Nullable**: false
- **Descrição**: Referência ao cliente em `tb_clientes`.
- **Comportamento Esperado**: Deve ser único e não nulo.
- **Observações**: Correspondente ao `EBDC50C4-2D12019-11-30` no Data Profiler, com 299 valores únicos e 0% de nulos.

### dt_contrato
- **Tipo**: date
- **Nullable**: false
- **Descrição**: Data de abertura do contrato.
- **Comportamento Esperado**: Deve ser uma data válida e não nula.
- **Observações**: Correspondente ao `2026-07-01` no Data Profiler, com 282 valores únicos e 0% de nulos.

### vl_limite
- **Tipo**: float
- **Nullable**: false
- **Descrição**: Limite de crédito aprovado em BRL.
- **Comportamento Esperado**: Deve ser um valor numérico positivo e não nulo.
- **Observações**: Correspondente ao `77205.25` no Data Profiler, com valores variando de 1065.12 a 99779.85.

### vl_utilizado
- **Tipo**: float
- **Nullable**: false
- **Descrição**: Saldo utilizado atual em BRL. Pode exceder `vl_limite` em produtos com tolerância.
- **Comportamento Esperado**: Deve ser um valor numérico positivo e não nulo.
- **Observações**: Pode exceder `vl_limite` em até 15% para produtos como cheque especial.

### tp_produto
- **Tipo**: string
- **Nullable

---
> **[AI_METADATA_STATUS: DRAFT]**