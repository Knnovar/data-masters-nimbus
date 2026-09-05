# Dicionário Técnico da Tabela `tb_clientes`

## Visão Geral

A tabela `tb_clientes` é um cadastro mestre de clientes pessoa física e jurídica. Ela é utilizada por todos os produtos de crédito e relacionamento do banco. A segmentação dos clientes determina o produto oferecido e o gestor responsável. A tabela é atualizada diariamente pelo batch noturno do sistema CORE_BANCARIO_TOTVS.

### Propriedades da Tabela

- **Owner**: squad-dados-cadastrais
- **Versão**: 1.0.0
- **Status do Manifesto**: DRAFT
- **Fonte**: Sistema CORE_BANCARIO_TOTVS, formato CSV, codificação UTF-8, sistema operacional Unix, atualização diária.
- **Contato**: squad-dados-cadastrais@banco.com.br
- **Classificação de Dados**: Confidencial
- **Período de Retenção**: 10 anos
- **Tags Regulatórias**: LGPD, BACEN_4658

## Colunas

### 1. `cd_cliente`

- **Tipo**: string
- **Nullable**: Não
- **Chave Primária**: Sim
- **Descrição**: Código único do cliente no sistema legado. Gerado sequencialmente pelo CORE_BANCARIO.
- **Estatísticas**:
  - Percentual de nulos: 0.0%
  - Contagem única: 499
- **Comportamento Esperado**: Cada cliente deve ter um código único e não nulo.

### 2. `nr_cpf_cnpj`

- **Tipo**: string
- **Nullable**: Não
- **Descrição**: CPF (11 dígitos) ou CNPJ (14 dígitos) sem máscara.
- **Implicações de Compliance**: Dados sensíveis conforme LGPD.
- **Comportamento Esperado**: Deve conter um CPF ou CNPJ válido e não nulo.

### 3. `nm_cliente`

- **Tipo**: string
- **Nullable**: Não
- **Descrição**: Nome completo do cliente conforme cadastro na Receita Federal.
- **Implicações de Compliance**: Dados sensíveis conforme LGPD.
- **Estatísticas**:
  - Percentual de nulos: 0.0%
  - Contagem única: 493
  - Valores duplicados: "Alícia Fernandes", "Larissa Novaes", "Maria Clara Novais" (cada um com 2 ocorrências)
- **Comportamento Esperado**: Nome completo e não nulo.

### 4. `dt_nascimento`

- **Tipo**: date
- **Nullable**: Sim
- **Descrição**: Data de nascimento. Nula para clientes PJ.
- **Implicações de Compliance**: Dados sensíveis conforme LGPD.
- **Comportamento Esperado**: Deve ser nula para clientes jurídicos.

### 5. `cd_segmento`

- **Tipo**: string
- **Nullable**: Não
- **Descrição**: Segmento de relacionamento. Domínio: VAREJO, PRIME, PRIVATE, PJ_PEQUENO, PJ_MEDIO.
- **Regras de Negócio**:
  - PRIME: `vl_renda_mensal >= 10000`
  - PRIVATE: `vl_renda_mensal >= 30000`
  - Sempre nulo para `cd_segmento` IN (PJ_PEQUENO, PJ_MEDIO)
- **Estatísticas**:
  - Percentual de nulos: 0.0%
  - Contagem única: 496
  - Valores duplic

---
> **[AI_METADATA_STATUS: DRAFT]**