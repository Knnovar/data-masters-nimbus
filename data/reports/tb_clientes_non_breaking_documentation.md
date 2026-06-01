# Dicionário Técnico da Tabela `tb_clientes_non_breaking`

## Visão Geral

A tabela `tb_clientes_non_breaking` é uma versão não quebrada do cadastro mestre de clientes, tanto pessoa física quanto jurídica. Ela é utilizada por todos os produtos de crédito e relacionamento no banco. A segmentação dos clientes determina o produto oferecido e o gestor responsável. Esta tabela é atualizada diariamente pelo batch noturno do sistema CORE_BANCARIO_TOTVS.

### Propriedades da Tabela

- **Owner**: squad-dados-cadastrais
- **Versão**: 1.0.0
- **Status do Manifesto**: DRAFT
- **Fonte**:
  - Sistema: CORE_BANCARIO_TOTVS
  - Formato: CSV
  - Codificação: UTF-8
  - Sistema Operacional: Unix
  - Frequência de Atualização: Diária
  - Contato: squad-dados-cadastrais@banco.com.br

### Contexto Regulatório

- **Tags Regulatórias**:
  - LGPD (Lei Geral de Proteção de Dados)
  - BACEN_4658
- **Classificação de Dados**: Confidencial
- **Período de Retenção**: 10 anos

### Pontos de Atenção

- **Tolerância**:
  - Máximo de % nulos: 25%
  - Duplicatas não permitidas

## Colunas da Tabela

### `cd_cliente`

- **Tipo**: VARCHAR
- **Descrição**: Código único do cliente no sistema legado. Gerado sequencialmente pelo CORE_BANCARIO.
- **Negócio**:
  - Propósito: Identificação única de cada cliente.
  - Comportamento Esperado: Não nulo, valores únicos para todos os registros.
- **Estatísticas Observadas**:
  - % Nulos: 0.0%
  - Contagem Única: 500
- **Anomalias**: Nenhuma

### `nr_cpf_cnpj`

- **Tipo**: VARCHAR
- **Descrição**: CPF (11 dígitos) ou CNPJ (14 dígitos) sem máscara.
- **Negócio**:
  - Propósito: Identificação fiscal do cliente.
  - Comportamento Esperado: Não nulo, deve conter valores válidos de CPF ou CNPJ.
- **Estatísticas Observadas**:
  - % Nulos: 0.0%
  - Contagem Única: 500
  - Mínimo: 1457389657.0
  - Máximo: 98651023405.0
  - Média: 47631701980.896
- **Anomalias**: Valores fora do intervalo esperado para CPF/CNPJ.

### `nm_cliente`

- **Tipo**: VARCHAR
- **Descrição**: Nome completo do cliente conforme cadastro na Receita Federal.
- **Negócio**:
  - Propósito: Identificação nominal do cliente.
  - Comportamento Esperado: Não nulo, deve ser único para a maioria dos registros.
- **Estatísticas Observadas**:
  - % Nulos: 0.0%
  - Contagem Única: 497
  - Valores Duplicados: "Brenda Ribeiro", "Ana Liz Carvalho", "Catarina da Rosa" (cada um com contagem de 2)
- **Anomalias**: Existem duplicatas nos nomes dos clientes.

### `dt_nascimento

---
> **[AI_METADATA_STATUS: DRAFT]**