# Dicionário Técnico da Tabela `tb_clientes`

## Visão Geral

A tabela `tb_clientes` é um cadastro mestre de clientes pessoa física e jurídica, utilizada por todos os produtos de crédito e relacionamento do banco. A segmentação dos clientes determina o produto oferecido e o gestor responsável. A tabela é atualizada diariamente pelo batch noturno do sistema CORE_BANCARIO_TOTVS.

### Propriedades da Tabela

- **Owner**: squad-dados-cadastrais
- **Versão**: 1.0.0
- **Status do Manifesto**: DRAFT
- **Fonte**: Sistema CORE_BANCARIO_TOTVS, formato CSV, codificação UTF-8, sistema operacional Unix, atualização diária.
- **Contato**: squad-dados-cadastrais@banco.com.br
- **Classificação de Dados**: Confidencial
- **Período de Retenção**: 10 anos
- **Regulamentações**: LGPD, BACEN 4658

## Colunas

### 1. `cd_cliente`

- **Tipo**: string
- **Nullable**: false
- **Descrição**: Código único do cliente no sistema legado, gerado sequencialmente pelo CORE_BANCARIO.
- **Propósito de Negócio**: Identificador único para cada cliente.
- **Comportamento Esperado**: Não deve conter valores nulos ou duplicados.
- **Anomalias**: Nenhuma observada; 100% de unicidade.

### 2. `nr_cpf_cnpj`

- **Tipo**: string
- **Nullable**: false
- **Descrição**: CPF (11 dígitos) ou CNPJ (14 dígitos) sem máscara.
- **Propósito de Negócio**: Identificação fiscal do cliente.
- **Comportamento Esperado**: Não deve conter valores nulos ou duplicados.
- **Regulamentações**: Considerado sensível sob LGPD.
- **Anomalias**: Nenhuma observada; 100% de unicidade.

### 3. `nm_cliente`

- **Tipo**: string
- **Nullable**: false
- **Descrição**: Nome completo do cliente conforme cadastro na Receita Federal.
- **Propósito de Negócio**: Nome do cliente para identificação e comunicação.
- **Comportamento Esperado**: Não deve conter valores nulos.
- **Regulamentações**: Considerado sensível sob LGPD.
- **Anomalias**: 6 duplicatas observadas.

### 4. `dt_nascimento`

- **Tipo**: date
- **Nullable**: true
- **Descrição**: Data de nascimento. Nula para clientes PJ.
- **Propósito de Negócio**: Informação demográfica para clientes PF.
- **Comportamento Esperado**: Pode ser nulo para clientes PJ.
- **Regulamentações**: Considerado sensível sob LGPD.
- **Anomalias**: Nenhuma observada.

### 5. `cd_segmento`

- **Tipo**: string
- **Nullable**: false
- **Descrição**: Segmento de relacionamento. Domínio: VAREJO, PRIME, PRIVATE, PJ_PEQUENO, PJ_MEDIO.
- **Propósito de Negócio**: Determina o produto oferecido e o gestor responsável.
- **Comportamento Esperado**: Não deve conter valores nulos.
- **Regras de Negócio**:
  - PRIME: `vl_renda_mensal >= 10000`
  - PRIVATE: `vl_renda_mensal >= 30000`
- **Anomalias**:

---
> **[AI_METADATA_STATUS: DRAFT]**