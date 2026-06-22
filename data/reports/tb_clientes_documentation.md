# Dicionário Técnico da Tabela `tb_clientes`

## Visão Geral

A tabela `tb_clientes` é um cadastro mestre que contém informações sobre clientes pessoa física e jurídica. Ela é utilizada por todos os produtos de crédito e relacionamento do banco, com segmentação determinando o produto ofertado e o gestor responsável. A tabela é atualizada diariamente pelo batch noturno do sistema CORE_BANCARIO_TOTVS.

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
  - Contato: squad-dados-cadastrais@banco.com.br

### Contexto Regulatório

- **Tags Regulatórias**: LGPD, BACEN_4658
- **Classificação de Dados**: Confidencial
- **Período de Retenção**: 10 anos

## Colunas da Tabela

### `cd_cliente`
- **Tipo**: VARCHAR (string)
- **Nulo**: Não permitido
- **Chave Primária**: Sim
- **Descrição**: Código único do cliente no sistema legado, gerado sequencialmente pelo CORE_BANCARIO.
- **Estatísticas**:
  - Percentual de Nulos: 0.0%
  - Contagem Única: 500

### `nr_cpf_cnpj`
- **Tipo**: VARCHAR (string)
- **Nulo**: Não permitido
- **Descrição**: CPF (11 dígitos) ou CNPJ (14 dígitos) sem máscara.
- **Implicações Regulatórias**: LGPD_SENSITIVE
- **Estatísticas**:
  - Percentual de Nulos: 0.0%
  - Contagem Única: 500
  - Mínimo: 1395867259.0
  - Máximo: 98750362429.0
  - Média: 48825936703.32

### `nm_cliente`
- **Tipo**: VARCHAR (string)
- **Nulo**: Não permitido
- **Descrição**: Nome completo do cliente conforme cadastro na Receita Federal.
- **Implicações Regulatórias**: LGPD_SENSITIVE
- **Estatísticas**:
  - Percentual de Nulos: 0.0%
  - Contagem Única: 499 (Anomalia: Duplicatas)
  - Valor Mais Comum: "Juliana Rocha" (2 ocorrências)

### `dt_nascimento`
- **Tipo**: VARCHAR (string) — Esperado como DATE
- **Nulo**: Permitido
- **Descrição**: Data de nascimento. Nula para clientes PJ.
- **Implicações Regulatórias**: LGPD_SENSITIVE
- **Estatísticas**:
  - Percentual de Nulos: 0.0%
  - Contagem Única: 496

### `cd_segmento`
- **Tipo**: VARCHAR (string)
- **Nulo**: Não permitido
- **Descrição**: Segmento de relacionamento. Domínio: VAREJO, PRIME, PRIVATE, PJ_PEQUENO, PJ_MEDIO.
- **Regras de Negócio**:
  - PRIME: vl_renda_mensal >= 10000
  - PRIVATE: vl_renda

---
> **[AI_METADATA_STATUS: DRAFT]**