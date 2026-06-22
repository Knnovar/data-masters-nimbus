# Dicionário Técnico da Tabela `tb_clientes_non_breaking`

## Visão Geral

A tabela `tb_clientes_non_breaking` é uma versão não quebrada do cadastro mestre de clientes, tanto pessoa física quanto jurídica. Ela serve como base para todos os produtos de crédito e relacionamento oferecidos pelo banco. A segmentação dos clientes determina o produto ofertado e o gestor responsável.

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

- **Tipo**: VARCHAR
- **Descrição**: Código único do cliente no sistema legado. Gerado sequencialmente pelo CORE_BANCARIO.
- **Nullable**: Não
- **Chave Primária**: Sim
- **Estatísticas**:
  - Percentual de Nulos: 0%
  - Contagem Única: 499

### `nr_cpf_cnpj`

- **Tipo**: VARCHAR (observado como parte do campo composto)
- **Descrição**: CPF (11 dígitos) ou CNPJ (14 dígitos) sem máscara.
- **Nullable**: Não
- **Implicações Regulatórias**: LGPD_SENSITIVE

### `nm_cliente`

- **Tipo**: VARCHAR (observado como parte do campo composto)
- **Descrição**: Nome completo do cliente conforme cadastro na Receita Federal.
- **Nullable**: Não
- **Implicações Regulatórias**: LGPD_SENSITIVE
- **Estatísticas**:
  - Percentual de Nulos: 0%
  - Contagem Única: 495
  - Valores Duplicados: "Alícia Camargo", "Emanuella da Mata", "Aylla Cavalcanti" (cada um com contagem de 2)

### `dt_nascimento` e `cd_segmento`

- **Tipo**: VARCHAR (observado como parte do campo composto)
- **Descrição**:
  - `dt_nascimento`: Data de nascimento. Nula para clientes PJ.
  - `cd_segmento`: Segmento de relacionamento. Dominio: VAREJO, PRIME, PRIVATE, PJ_PEQUENO, PJ_MEDIO.
- **Nullable**: Não
- **Estatísticas**:
  - Percentual de Nulos: 0%
  - Contagem Única: 497

### `cd_agencia`

- **Tipo**: VARCHAR (observado como parte do campo composto)
- **Descrição**: Código numérico de 4 dígitos da agência de relacionamento principal.
- **Nullable**: Não
- **Estatísticas**:
  - Percentual de Nulos: 0%
  - Contagem Única: 472
  - Valores Duplicados: "AGENC-" (contagem de 15)

### `vl_renda_mensal` e `fl_ativo`

- **Tipo**: VARCHAR (observado como parte do

---
> **[AI_METADATA_STATUS: DRAFT]**