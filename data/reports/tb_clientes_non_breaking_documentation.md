# Dicionário Técnico da Tabela `tb_clientes_non_breaking`

## Visão Geral

A tabela `tb_clientes_non_breaking` é uma versão não quebra do cadastro mestre de clientes, tanto pessoa física quanto jurídica. Ela serve como base para todos os produtos de crédito e relacionamento no banco, com segmentação determinando o produto ofertado e o gestor responsável.

### Propriedades da Tabela

- **Owner**: squad-dados-cadastrais
- **Versão**: 1.0.0
- **Status do Manifesto**: DRAFT
- **Fonte**:
  - Sistema: CORE_BANCARIO_TOTVS
  - Formato: CSV
  - Codificação: UTF-8
  - SO: Unix
  - Frequência de Atualização: Diária
- **Contato**: squad-dados-cadastrais@banco.com.br

### Contexto Regulatório

- **Tags Regulatórias**:
  - LGPD (Lei Geral de Proteção de Dados)
  - BACEN_4658
- **Classificação de Dados**: Confidencial
- **Período de Retenção**: 10 anos

### Contexto de Negócios

A tabela é atualizada diariamente pelo batch noturno do CORE_BANCARIO_TOTVS e serve como a base para todas as operações relacionadas aos clientes no banco.

## Colunas da Tabela

### `cd_cliente`

- **Tipo**: VARCHAR
- **Descrição**: Código único do cliente no sistema legado, gerado sequencialmente pelo CORE_BANCARIO.
- **Negócio**:
  - Propósito: Identificação única de cada cliente.
  - Comportamento Esperado: Não nulo e exclusivo para todos os registros.
- **Estatísticas**:
  - % Nulos: 0.0%
  - Contagem Única: 500
- **Anomalias**: Nenhuma

### `nr_cpf_cnpj`

- **Tipo**: VARCHAR
- **Descrição**: CPF (11 dígitos) ou CNPJ (14 dígitos) sem máscara.
- **Negócio**:
  - Propósito: Identificação fiscal do cliente.
  - Comportamento Esperado: Não nulo e exclusivo para cada registro.
- **Estatísticas**:
  - % Nulos: 0.0%
  - Contagem Única: 500
  - Mínimo: 1279354607.0
  - Máximo: 98725460374.0
  - Média: 50478969775.3
- **Anomalias**: Nenhuma

### `nm_cliente`

- **Tipo**: VARCHAR
- **Descrição**: Nome completo do cliente conforme cadastro na Receita Federal.
- **Negócio**:
  - Propósito: Identificação nominal do cliente.
  - Comportamento Esperado: Não nulo e deve ser único, exceto em casos de duplicação legítima (ex.: homônimos).
- **Estatísticas**:
  - % Nulos: 0.0%
  - Contagem Única: 498
  - Top Values: "Marina Duarte" aparece duas vezes.
- **Anomalias**: Possível duplicidade de nomes.

### `dt_nascimento`

- **Tipo**: VARCHAR (esperado DATE)
- **Descrição**: Data de nascimento. Nula para clientes PJ.
- **Negócio**:
  - Propósito: Identificação da idade do cliente pessoa física.
  - Comportamento Esperado

---
> **[AI_METADATA_STATUS: DRAFT]**