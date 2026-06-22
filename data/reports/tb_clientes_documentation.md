# Dicionário Técnico da Tabela `tb_clientes`

## Visão Geral

A tabela `tb_clientes` é um cadastro mestre que contém informações sobre clientes pessoa física e jurídica. Ela é utilizada por todos os produtos de crédito e relacionamento do banco, com a segmentação determinando o produto ofertado e o gestor responsável. A atualização diária é realizada pelo batch noturno do sistema CORE_BANCARIO_TOTVS.

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

- **Tipo**: String
- **Nullable**: Não
- **Descrição**: Código único do cliente no sistema legado, gerado sequencialmente pelo CORE_BANCARIO.
- **Propósito de Negócio**: Identificador primário para cada cliente.
- **Comportamento Esperado**: Sem valores nulos e exclusivo por linha.

### `nr_cpf_cnpj`

- **Tipo**: String
- **Nullable**: Não
- **Descrição**: CPF (11 dígitos) ou CNPJ (14 dígitos) sem máscara.
- **Propósito de Negócio**: Identificação única do cliente conforme cadastro na Receita Federal.
- **Comportamento Esperado**: Sem valores nulos, deve conter 11 ou 14 caracteres numéricos.
- **Implicações Regulatórias**: Considerado sensível sob LGPD.

### `nm_cliente`

- **Tipo**: String
- **Nullable**: Não
- **Descrição**: Nome completo do cliente conforme cadastro na Receita Federal.
- **Propósito de Negócio**: Identificação textual do cliente.
- **Comportamento Esperado**: Sem valores nulos, deve ser único para a maioria dos registros.
- **Implicações Regulatórias**: Considerado sensível sob LGPD.

### `dt_nascimento`

- **Tipo**: Date
- **Nullable**: Sim
- **Descrição**: Data de nascimento. Nula para clientes PJ (pessoa jurídica).
- **Propósito de Negócio**: Informação demográfica relevante para segmentação e análise.
- **Comportamento Esperado**: Pode ser nulo, especialmente para clientes PJ.

### `cd_segmento`

- **Tipo**: String
- **Nullable**: Não
- **Descrição**: Segmento de relacionamento. Domínio: VAREJO, PRIME, PRIVATE, PJ_PEQUENO, PJ_MEDIO.
- **Propósito de Negócio**: Determina o produto oferecido e o gestor responsável.
- **Comportamento Esperado**: Sem valores nulos, deve seguir as regras de negócio associadas a renda mensal.

### `cd_agencia`

- **Tipo**: String
- **Nullable**: Não
- **Descrição**: Código numérico de 4 dígitos da agência de relacionamento principal.
- **Propósito de Negócio**: Identificação da

---
> **[AI_METADATA_STATUS: DRAFT]**