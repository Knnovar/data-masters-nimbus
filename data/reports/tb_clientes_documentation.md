# Dicionário Técnico da Tabela `tb_clientes`

## Visão Geral

A tabela `tb_clientes` é um cadastro mestre de clientes pessoa física e jurídica, utilizada por todos os produtos de crédito e relacionamento do banco. A segmentação (`cd_segmento`) determina o produto ofertado e o gestor responsável. A tabela é atualizada diariamente pelo batch noturno do sistema CORE_BANCARIO_TOTVS.

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
- **Tipo**: VARCHAR
- **Nullable**: Não
- **Descrição**: Código único do cliente no sistema legado, gerado sequencialmente pelo CORE_BANCARIO.
- **Propósito de Negócio**: Identificação única de cada cliente.
- **Comportamento Esperado**: Cada valor deve ser único e não nulo.
- **Estatísticas Observadas**: 499 valores únicos, 0% de nulos.

### 2. `nr_cpf_cnpj`
- **Tipo**: VARCHAR
- **Nullable**: Não
- **Descrição**: CPF (11 dígitos) ou CNPJ (14 dígitos) sem máscara.
- **Propósito de Negócio**: Identificação fiscal do cliente.
- **Comportamento Esperado**: Deve conter 11 ou 14 dígitos, sem espaços ou caracteres especiais.
- **Implicações de Compliance**: LGPD_SENSITIVE.
- **Estatísticas Observadas**: Não disponíveis diretamente, mas deve ser coerente com a descrição.

### 3. `nm_cliente`
- **Tipo**: VARCHAR
- **Nullable**: Não
- **Descrição**: Nome completo do cliente conforme cadastro na Receita Federal.
- **Propósito de Negócio**: Nome do cliente para identificação.
- **Comportamento Esperado**: Não deve conter valores nulos.
- **Implicações de Compliance**: LGPD_SENSITIVE.
- **Estatísticas Observadas**: 497 valores únicos, 0% de nulos. Anomalia: 2 duplicatas observadas.

### 4. `dt_nascimento`
- **Tipo**: VARCHAR (observado como VARCHAR no profiler)
- **Nullable**: Sim
- **Descrição**: Data de nascimento. Nula para clientes PJ.
- **Propósito de Negócio**: Data de nascimento para clientes PF.
- **Comportamento Esperado**: Deve estar no formato de data, nulo para clientes PJ.
- **Estatísticas Observadas**: Combinado com `cd_segmento` em uma única coluna, o que indica uma anomalia.

### 5. `cd_segmento`
- **Tipo**: VARCHAR (observado como VARCHAR no profiler)
- **Nullable**: Não
- **Descrição**: Segmento de relacionamento. Domínio: VAREJO, PRIME, PRIVATE, PJ_PEQUENO, PJ_MEDIO.
- **Propósito de Negócio**: Determina o produto ofertado e o gestor responsável.
- **Comportamento Esperado**: De

---
> **[AI_METADATA_STATUS: DRAFT]**