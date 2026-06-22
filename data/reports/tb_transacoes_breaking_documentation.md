# Dicionário Técnico da Tabela `tb_transacoes_breaking`

## Visão Geral

A tabela `tb_transacoes_breaking` contém registros das movimentações financeiras realizadas através de diversos canais de atendimento do banco, conforme descrito no contrato YAML. Este documento visa detalhar cada coluna presente na tabela, destacando propósitos de negócio, tipos de dados, comportamentos esperados e anomalias observadas.

### Contexto de Negócios

- **Registro de Movimentações**: A tabela registra todas as transações financeiras por canal. 
- **Flag de Transação Suspeita (`fl_suspeita`)**: Sinaliza transações em análise pelo motor antifraude.
- **Código do Estabelecimento (`cd_estabelecimento`)**: Pode ser nulo para compras online não identificadas.

### Regulamentações e Compliance

- **Tags Regulatórias**: 
  - `BACEN_4658`: Norma regulatória brasileira que deve ser observada.
  - `PCI_DSS`: Requisitos de segurança para processamento de dados de cartão de crédito.

### Classificação e Retenção de Dados

- **Classificação**: Confidencial
- **Período de Retenção**: 7 anos

## Descrição das Colunas

### 1. `bf593f98-45de-4688-8ef7-1b9d7121769694A38DFF-81A2023-03-20`

- **Propósito de Negócio**: Identificador único da transação.
- **Tipo de Dado**: VARCHAR
- **Comportamento Esperado**: Não deve conter valores nulos. Deve ser único para cada registro, exceto por duplicatas observadas (2 ocorrências).
- **Anomalias**:
  - Duplas ocorridas em `top_values` indicam potenciais problemas de integridade.

### 2. `21951.46PIX`

- **Propósito de Negócio**: Tipo da transação.
- **Tipo de Dado**: VARCHAR
- **Comportamento Esperado**: Não deve conter valores nulos e deve seguir o domínio definido (`COMPRA`, `SAQUE`, etc.).
- **Anomalias**:
  - Duplas ocorridas em `top_values` indicam potenciais problemas de integridade.

### 3. `Unnamed: 2`

- **Propósito de Negócio**: Valor da transação.
- **Tipo de Dado**: VARCHAR
- **Comportamento Esperado**: Não deve conter valores nulos, mas apresenta uma taxa de nulidade de 6.16%.
- **Anomalias**:
  - Taxa de nulidade acima do limite aceitável (10%).
  - Valores extremos observados: mínimo de `1235684000173.0` e máximo de `98763105000105.0`.

### 4. `FAPP`

- **Propósito de Negócio**: Canal de origem da transação.
- **Tipo de Dado**: VARCHAR
- **Comportamento Esperado**: Não deve conter valores nulos, com domínio definido (`APP`, `INTERNET`, etc.).
- **Anomalias**:
  - Nenhuma anomalia observada em relação a duplicatas ou nulidade.

## Pontos de Atenção

1. **Duplas Identificadas**: Existem registros duplicados para os identificadores de transação e tipos de transação, o que pode indicar problemas na integridade dos dados.
2. **Tax

---
> **[AI_METADATA_STATUS: DRAFT]**