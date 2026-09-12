# Dicionário Técnico da Tabela `tb_clientes`

## Visão Geral

A tabela `tb_clientes` é um cadastro mestre de clientes pessoa física e jurídica, utilizado por todos os produtos de crédito e relacionamento do banco. A segmentação (`cd_segmento`) determina o produto ofertado e o gestor responsável. A tabela é atualizada diariamente pelo batch noturno do sistema CORE_BANCARIO_TOTVS.

### Propriedades da Tabela

- **Owner**: squad-dados-cadastrais
- **Versão**: 1.0.0
- **Status do Manifesto**: VALIDADO
- **Fonte**: Sistema CORE_BANCARIO_TOTVS, formato CSV, codificação UTF-8, sistema operacional Unix, atualização diária.
- **Contato**: squad-dados-cadastrais@banco.com.br
- **Classificação de Dados**: Confidencial
- **Período de Retenção**: 10 anos
- **Tags Regulatórias**: LGPD, BACEN_4658
- **Validado por**: Renan Apolinario em 12 de setembro de 2026

## Colunas

### `cd_cliente`
- **Tipo**: string
- **Nullable**: Não
- **Descrição**: Código único do cliente no sistema legado. Gerado sequencialmente pelo CORE_BANCARIO.
- **Propósito de Negócio**: Identificação única de cada cliente.
- **Comportamento Esperado**: Cada valor deve ser único e não nulo.
- **Estatísticas**: 500 valores únicos, 0% de nulos.

### `nr_cpf_cnpj`
- **Tipo**: string
- **Nullable**: Não
- **Descrição**: CPF (11 dígitos) ou CNPJ (14 dígitos) sem máscara.
- **Propósito de Negócio**: Identificação fiscal do cliente.
- **Comportamento Esperado**: Sempre preenchido, com formato correto de CPF ou CNPJ.
- **Estatísticas**: 500 valores únicos, 0% de nulos.
- **Sensibilidade**: LGPD_SENSITIVE
- **Formato**: `[MASCARADO]` (CPF: 99999999999, CNPJ: 99999999999999)

### `nm_cliente`
- **Tipo**: string
- **Nullable**: Não
- **Descrição**: Nome completo do cliente conforme cadastro na Receita Federal.
- **Propósito de Negócio**: Nome do cliente para identificação.
- **Comportamento Esperado**: Sempre preenchido, com formato de nome completo.
- **Estatísticas**: 495 valores únicos, 0% de nulos.
- **Sensibilidade**: LGPD_SENSITIVE
- **Formato**: `[MASCARADO]` (Ex: AAAAAA AAAAA, AA. AAAAA AA AAAA)

### `dt_nascimento`
- **Tipo**: string
- **Nullable**: Sim
- **Descrição**: Data de nascimento. Nula para clientes PJ.
- **Propósito de Negócio**: Data de nascimento do cliente.
- **Comportamento Esperado**: Preenchido para PF, nulo para PJ.
- **Estatísticas**: 496 valores únicos, 0% de nulos.
- **Sensibilidade**: LGPD_SENSITIVE
- **Formato**: `[MASCARADO]` (9999-99-99)

### `cd_segmento`
- **Tipo**: string
- **Nullable**: Não
- **Descrição**: Segmento de relacionamento. Domínio: VAREJO, PRIME, PRIVATE, PJ_PEQUENO, PJ_MEDIO.
- **Propósito de Negócio**: Determina o produto ofertado e o gestor responsável.
- **Comportamento Esperado**: Sempre preenchido, com valores dentro do domínio especificado.
- **Estatísticas**: 5 valores únicos, 0% de nulos.
- **Regras de Negócio**:
  - PRIME: `vl_renda_mensal >= 10000`
  - PRIVATE: `vl_renda_mensal >= 30000`

### `cd_agencia`
- **Tipo**: string
- **Nullable**: Não
- **Descrição**: Código numérico de 4 dígitos da agência de relacionamento principal.
- **Propósito de Negócio**: Identificação da agência responsável pelo cliente.
- **Comportamento Esperado**: Sempre preenchido, com valores numéricos de 4 dígitos.
- **Estatísticas**: 475 valores únicos, 0% de nulos.
- **Anomalias**: Valores fora do intervalo esperado (1056.0 a 9984.0).

### `vl_renda_mensal`
- **Tipo**: string
- **Nullable**: Sim
- **Descrição**: Renda mensal declarada em BRL. Nula para clientes PJ.
- **Propósito de Negócio**: Indicador de renda para análise de crédito.
- **Comportamento Esperado**: Preenchido para PF, nulo para PJ.
- **Estatísticas**: 369 valores únicos, 19.2% de nulos.
- **Sensibilidade**: SCR_CANDIDATE
- **Formato**: `[MASCARADO]` (Ex: 1.234,56)
- **Anomalias**: Valores nulos para segmentos PJ_PEQUENO e PJ_MEDIO.

### `fl_ativo`
- **Tipo**: string
- **Nullable**: Não
- **Descrição**: Indica se o cliente possui relacionamento ativo com o banco.
- **Propósito de Negócio**: Status de ativação do cliente.
- **Comportamento Esperado**: Sempre preenchido, com valores booleanos.
- **Estatísticas**: 2 valores únicos, 0% de nulos.

### `dt_cadastro`
- **Tipo**: string
- **Nullable**: Não
- **Descrição**: Data de abertura do cadastro no sistema.
- **Propósito de Negócio**: Registro da data de cadastro do cliente.
- **Comportamento Esperado**: Sempre preenchido, com formato de data.
- **Estatísticas**: 468 valores únicos, 0% de nulos.

## Implicações de Compliance

- **LGPD**: A tabela contém dados sensíveis como CPF/CNPJ, nome, data de nascimento e renda mensal, exigindo medidas de proteção e anonimização adequadas.
- **BACEN_4658**: Requisitos específicos de segurança e proteção de dados financeiros.

## Pontos de Atenção

1. **Alto Percentual de Nulos em `vl_renda_mensal`**: 19.2% de nulos, o que pode impactar análises de crédito.
2. **Valores Fora de Faixa em `cd_agencia`**: Valores fora do intervalo esperado (1056.0 a 9984.0).
3. **Duplicatas em `nm_cliente`**: 5 duplicatas identificadas, o que pode indicar problemas de integridade de dados.
4. **Regras de Negócio Não Cumpridas**: Verificar se `vl_renda_mensal` está correto para segmentos PRIME e PRIVATE.
5. **Formato de Dados**: Algumas colunas (`vl_renda_mensal`, `dt_cadastro`) estão em formato de string, o que pode afetar operações numéricas e de data.

---

> **[AI_METADATA_STATUS: DRAFT]** — Documentação gerada por SLM. Requer validação humana pelo Data Steward responsável antes de uso em produção.