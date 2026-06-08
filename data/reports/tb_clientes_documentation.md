# Dicionário Técnico da Tabela `tb_clientes`

## Visão Geral

A tabela `tb_clientes` é um cadastro mestre de clientes pessoa física e jurídica, utilizada por todos os produtos de crédito e relacionamento do banco. A segmentação dos clientes determina o produto oferecido e o gestor responsável. Esta tabela é atualizada diariamente pelo batch noturno do sistema CORE_BANCARIO_TOTVS.

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

### Regulamentação e Classificação

- **Tags Regulatórias**: LGPD, BACEN_4658
- **Classificação de Dados**: Confidencial
- **Período de Retenção**: 10 anos

## Colunas da Tabela

### `cd_cliente`
- **Tipo**: String
- **Pode ser Nulo?**: Não
- **Chave Primária**: Sim
- **Descrição**: Código único do cliente no sistema legado, gerado sequencialmente pelo CORE_BANCARIO.
- **Estatísticas**:
  - Percentual de Nulos: 0.0%
  - Contagem Única: 500
  - Valores Principais: Todos únicos

### `nr_cpf_cnpj`
- **Tipo**: String
- **Pode ser Nulo?**: Não
- **Descrição**: CPF (11 dígitos) ou CNPJ (14 dígitos) sem máscara.
- **Implicações Regulatórias**: LGPD_SENSITIVE
- **Estatísticas**:
  - Percentual de Nulos: 0.0%
  - Contagem Única: 500
  - Intervalo: Min = 1325896721, Max = 98762314564

### `nm_cliente`
- **Tipo**: String
- **Pode ser Nulo?**: Não
- **Descrição**: Nome completo do cliente conforme cadastro na Receita Federal.
- **Implicações Regulatórias**: LGPD_SENSITIVE
- **Estatísticas**:
  - Percentual de Nulos: 0.0%
  - Contagem Única: 499 (Anomalia: Duplicatas)
  - Valores Principais: "Matheus Silva" aparece duas vezes

### `dt_nascimento`
- **Tipo**: String
- **Pode ser Nulo?**: Sim
- **Descrição**: Data de nascimento. Nula para clientes PJ.
- **Implicações Regulatórias**: LGPD_SENSITIVE
- **Estatísticas**:
  - Percentual de Nulos: 0.0%
  - Contagem Única: 496 (Anomalia: Duplicatas)
  - Valores Principais: "1987-08-12" e outros aparecem duas vezes

### `cd_segmento`
- **Tipo**: String
- **Pode ser Nulo?**: Não
- **Descrição**: Segmento de relacionamento. Domínio: VAREJO, PRIME, PRIVATE, PJ_PEQUENO, PJ_MEDIO.
- **Regras de Negócio**:
  - PRIME: `vl_renda_mensal

---
> **[AI_METADATA_STATUS: DRAFT]**