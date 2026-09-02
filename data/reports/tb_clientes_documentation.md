# Dicionário Técnico da Tabela `tb_clientes`

## Visão Geral

A tabela `tb_clientes` é um cadastro mestre de clientes pessoa física e jurídica, utilizado por todos os produtos de crédito e relacionamento do banco. A segmentação dos clientes determina o produto oferecido e o gestor responsável. A tabela é atualizada diariamente pelo batch noturno do sistema CORE_BANCARIO_TOTVS.

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

### `cd_cliente`
- **Tipo**: VARCHAR
- **Nullable**: Não
- **Descrição**: Código único do cliente no sistema legado, gerado sequencialmente pelo CORE_BANCARIO.
- **Propósito de Negócio**: Identificador único para cada cliente.
- **Comportamento Esperado**: Sem valores nulos, 500 valores únicos.
- **Anomalias**: Nenhuma.

### `nr_cpf_cnpj`
- **Tipo**: VARCHAR
- **Nullable**: Não
- **Descrição**: CPF (11 dígitos) ou CNPJ (14 dígitos) sem máscara.
- **Propósito de Negócio**: Identificação fiscal do cliente.
- **Comportamento Esperado**: Sem valores nulos, 500 valores únicos.
- **Regulatório**: Sensível conforme LGPD.
- **Anomalias**: Nenhuma.

### `nm_cliente`
- **Tipo**: VARCHAR
- **Nullable**: Não
- **Descrição**: Nome completo do cliente conforme cadastro na Receita Federal.
- **Propósito de Negócio**: Nome do cliente para identificação.
- **Comportamento Esperado**: Sem valores nulos, 498 valores únicos.
- **Regulatório**: Sensível conforme LGPD.
- **Anomalias**: 2 duplicatas identificadas.

### `dt_nascimento`
- **Tipo**: VARCHAR
- **Nullable**: Sim
- **Descrição**: Data de nascimento. Nula para clientes PJ.
- **Propósito de Negócio**: Informação demográfica do cliente.
- **Comportamento Esperado**: Pode ser nulo, 495 valores únicos.
- **Regulatório**: Sensível conforme LGPD.
- **Anomalias**: Nenhuma.

### `cd_segmento`
- **Tipo**: VARCHAR
- **Nullable**: Não
- **Descrição**: Segmento de relacionamento. Domínio: VAREJO, PRIME, PRIVATE, PJ_PEQUENO, PJ_MEDIO.
- **Propósito de Negócio**: Determina o produto oferecido e o gestor responsável.
- **Comportamento Esperado**: Sem valores nulos, 5 valores únicos.
- **Regras de Negócio**:
  - PRIME: `vl_renda_mensal >= 10000`
  - PRIVATE: `vl_renda_mensal >= 30000`
- **Anomalias**: Verificar se `vl_renda_mensal` está nulo para `PJ_PEQUENO` e `PJ_MEDIO`.

### `cd_agencia`
- **Tipo**: VARCHAR

---
> **[AI_METADATA_STATUS: DRAFT]**