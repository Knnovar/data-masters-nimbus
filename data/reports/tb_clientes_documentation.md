# Dicionário Técnico da Tabela `tb_clientes`

## Visão Geral

A tabela `tb_clientes` é um cadastro mestre de clientes pessoa física e jurídica, utilizada por todos os produtos de crédito e relacionamento do banco. A segmentação dos clientes determina o produto ofertado e o gestor responsável. A tabela é atualizada diariamente pelo batch noturno do sistema CORE_BANCARIO_TOTVS.

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
- **Propósito de Negócio**: Identificação única de cada cliente.
- **Comportamento Esperado**: Sem valores nulos, deve ser único para cada cliente.
- **Anomalias Observadas**: Nenhuma duplicata ou valor nulo observado.

### 2. `nr_cpf_cnpj`
- **Tipo**: string
- **Nullable**: false
- **Descrição**: CPF (11 dígitos) ou CNPJ (14 dígitos) sem máscara.
- **Propósito de Negócio**: Identificação fiscal do cliente.
- **Comportamento Esperado**: Sempre preenchido, sem valores nulos.
- **Regulamentações**: LGPD_SENSITIVE
- **Anomalias Observadas**: Nenhuma duplicata ou valor nulo observado.

### 3. `nm_cliente`
- **Tipo**: string
- **Nullable**: false
- **Descrição**: Nome completo do cliente conforme cadastro na Receita Federal.
- **Propósito de Negócio**: Nome do cliente para identificação.
- **Comportamento Esperado**: Sempre preenchido, sem valores nulos.
- **Regulamentações**: LGPD_SENSITIVE
- **Anomalias Observadas**: 2 duplicatas observadas para o nome "Ravy Borges".

### 4. `dt_nascimento`
- **Tipo**: date
- **Nullable**: true
- **Descrição**: Data de nascimento. Nula para clientes PJ.
- **Propósito de Negócio**: Data de nascimento para clientes pessoa física.
- **Comportamento Esperado**: Pode ser nulo para clientes jurídicos.
- **Regulamentações**: LGPD_SENSITIVE
- **Anomalias Observadas**: Nenhuma observada.

### 5. `cd_segmento`
- **Tipo**: string
- **Nullable**: false
- **Descrição**: Segmento de relacionamento. Dominio: VAREJO, PRIME, PRIVATE, PJ_PEQUENO, PJ_MEDIO.
- **Propósito de Negócio**: Determina o produto ofertado e o gestor responsável.
- **Comportamento Esperado**: Sempre preenchido, sem valores nulos.
- **Regras de Negócio**:
  - PRIME: `vl_renda_mensal >= 10000`
  - PRIVATE: `vl_renda_mensal >= 30000`
- **Anomalias Observadas**: 3 duplicatas observadas para o segmento "PJ_MEDIO".

### 6. `cd_agencia`
- **Tipo**: string
- **Nullable**: false
- **Descrição**: Código numérico de 4 dígitos da agência de relacionamento principal.
- **Propósito de Negócio**: Identificação da agência responsável pelo cliente.
- **Comportamento Esperado**: Sempre preenchido, sem valores nulos.
- **Anomalias Observadas**: 15 valores "AGENC-" observados, possivelmente indicando dados incompletos ou incorretos.

### 7. `vl_renda_mensal`
- **Tipo**: float
- **Nullable**: true
- **Descrição**: Renda mensal declarada em BRL. Nula para clientes PJ.
- **Propósito de Negócio**: Indicador de renda para clientes pessoa física.
- **Comportamento Esperado**: Pode ser nulo para clientes jurídicos e segmentos PJ_PEQUENO, PJ_MEDIO.
- **Regulamentações**: SCR_CANDIDATE
- **Anomalias Observadas**: Nenhuma observada.

### 8. `fl_ativo`
- **Tipo**: boolean
- **Nullable**: false
- **Descrição**: Indica se o cliente possui relacionamento ativo com o banco.
- **Propósito de Negócio**: Status de ativação do cliente.
- **Comportamento Esperado**: Sempre preenchido, sem valores nulos.

### 9. `dt_cadastro`
- **Tipo**: date
- **Nullable**: false
- **Descrição**: Data de abertura do cadastro no sistema.
- **Propósito de Negócio**: Registro da data de cadastro do cliente.
- **Comportamento Esperado**: Sempre preenchido, sem valores nulos.

## Análise de Anomalias

- **Duplicatas**: Observadas para `nm_cliente` ("Ravy Borges") e `cd_segmento` ("PJ_MEDIO").
- **Valores Incompletos**: Observados para `cd_agencia` ("AGENC-").
- **Comportamento Esperado**: Todas as colunas obrigatórias estão preenchidas conforme esperado, exceto `dt_nascimento` e `vl_renda_mensal`, que podem ser nulos conforme as regras de negócio.

## Implicações de Compliance

- **LGPD**: Dados sensíveis como CPF/CNPJ, nome e data de nascimento estão sujeitos a regulamentações de proteção de dados.
- **BACEN 4658**: Requisitos de segurança e proteção de dados financeiros.
- **SCR_CANDIDATE**: Renda mensal pode ser considerada para Score de Crédito.

## Pontos de Atenção

1. **Duplicatas**: Verificar e corrigir duplicatas nos nomes e segmentos.
2. **Valores Incompletos**: Investigar e corrigir valores incompletos na coluna `cd_agencia`.
3. **Compliance**: Garantir conformidade contínua com LGPD e BAC

---
> **[AI_METADATA_STATUS: DRAFT]**