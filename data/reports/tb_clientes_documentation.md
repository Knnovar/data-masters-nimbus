# Dicionário Técnico da Tabela `tb_clientes`

## Visão Geral

A tabela `tb_clientes` é um cadastro mestre de clientes pessoa física e jurídica, utilizada por todos os produtos de crédito e relacionamento do banco. A segmentação (`cd_segmento`) determina o produto ofertado e o gestor responsável. A tabela é atualizada diariamente pelo batch noturno do sistema CORE_BANCARIO_TOTVS.

### Propriedades da Tabela

- **Owner**: squad-dados-cadastrais
- **Versão**: 1.0.0
- **Status do Manifesto**: VALIDATED
- **Fonte**:
  - Sistema: CORE_BANCARIO_TOTVS
  - Formato: CSV
  - Codificação: UTF-8
  - Sistema Operacional: Unix
  - Frequência de Atualização: Diária
  - Contato: squad-dados-cadastrais@banco.com.br
- **Classificação Regulatória**:
  - Tags: LGPD, BACEN_4658
  - Classificação de Dados: Confidencial
  - Anos de Retenção: 10
- **Validado por**: Renan Apolinario
- **Data de Validação**: 12 de Setembro de 2026

## Colunas

### `cd_cliente`
- **Tipo**: VARCHAR
- **Nullable**: Não
- **Descrição**: Código único do cliente no sistema legado. Gerado sequencialmente pelo CORE_BANCARIO.
- **Comportamento Esperado**: Cada cliente deve ter um código único. Não deve haver valores nulos ou duplicados.
- **Estatísticas**:
  - Percentual de Nulos: 0.0%
  - Contagem Única: 500
- **Anomalias**: Nenhuma

### `nr_cpf_cnpj`
- **Tipo**: VARCHAR
- **Nullable**: Não
- **Descrição**: CPF (11 dígitos) ou CNPJ (14 dígitos) sem máscara.
- **Comportamento Esperado**: Deve conter um CPF ou CNPJ válido, sem valores nulos.
- **Estatísticas**:
  - Percentual de Nulos: 0.0%
  - Contagem Única: 500
  - Sensível: Sim
  - Faixa: [MASCARADO]
- **Anomalias**: Nenhuma

### `nm_cliente`
- **Tipo**: VARCHAR
- **Nullable**: Não
- **Descrição**: Nome completo do cliente conforme cadastro na Receita Federal.
- **Comportamento Esperado**: Deve conter o nome completo do cliente, sem valores nulos.
- **Estatísticas**:
  - Percentual de Nulos: 0.0%
  - Contagem Única: 499
  - Sensível: Sim
- **Anomalias**: Existem duplicatas de nomes, o que pode indicar erros de entrada de dados.

### `dt_nascimento`
- **Tipo**: VARCHAR
- **Nullable**: Sim
- **Descrição**: Data de nascimento. Nula para clientes PJ.
- **Comportamento Esperado**: Deve conter a data de nascimento para clientes PF, nula para PJ.
- **Estatísticas**:
  - Percentual de Nulos: 0.0%
  - Contagem Única: 495
  - Sensível: Sim
- **Anomalias**: Nenhuma, mas a coluna não deve conter valores para clientes PJ.

### `cd_segmento`
- **Tipo**: VARCHAR
- **Nullable**: Não
- **Descrição**: Segmento de relacionamento. Domínio: VAREJO, PRIME, PRIVATE, PJ_PEQUENO, PJ_MEDIO.
- **Comportamento Esperado**: Deve conter um dos valores do domínio especificado.
- **Estatísticas**:
  - Percentual de Nulos: 0.0%
  - Contagem Única: 5
- **Anomalias**: Nenhuma

### `cd_agencia`
- **Tipo**: VARCHAR
- **Nullable**: Não
- **Descrição**: Código numérico de 4 dígitos da agência de relacionamento principal.
- **Comportamento Esperado**: Deve conter um código de agência válido, sem valores nulos.
- **Estatísticas**:
  - Percentual de Nulos: 0.0%
  - Contagem Única: 473
  - Mínimo: 1027.0
  - Máximo: 9984.0
  - Média: 5541.2062
- **Anomalias**: Existem valores de agência que aparecem com frequência, indicando potenciais duplicatas ou erros.

### `vl_renda_mensal`
- **Tipo**: VARCHAR
- **Nullable**: Sim
- **Descrição**: Renda mensal declarada em BRL. Nula para clientes PJ.
- **Comportamento Esperado**: Deve ser nulo para segmentos PJ_PEQUENO e PJ_MEDIO.
- **Estatísticas**:
  - Percentual de Nulos: 20.6%
  - Contagem Única: 397
  - Mínimo: 1669.2
  - Máximo: 79966.43
  - Média: 41564.8931
- **Anomalias**: Percentual de nulos acima do esperado, indicando potencial inconsistência com regras de negócio.

### `fl_ativo`
- **Tipo**: VARCHAR
- **Nullable**: Não
- **Descrição**: Indica se o cliente possui relacionamento ativo com o banco.
- **Comportamento Esperado**: Deve conter valores booleanos (True/False).
- **Estatísticas**:
  - Percentual de Nulos: 0.0%
  - Contagem Única: 2
- **Anomalias**: Nenhuma

### `dt_cadastro`
- **Tipo**: VARCHAR
- **Nullable**: Não
- **Descrição**: Data de abertura do cadastro no sistema.
- **Comportamento Esperado**: Deve conter a data de cadastro, sem valores nulos.
- **Estatísticas**:
  - Percentual de Nulos: 0.0%
  - Contagem Única: 462
- **Anomalias**: Nenhuma

## Implicações de Compliance

- **LGPD**: As colunas `nr_cpf_cnpj`, `nm_cliente`, `dt_nascimento` e `vl_renda_mensal` são consideradas sensíveis e devem ser tratadas conforme as diretrizes da LGPD.
- **BACEN_4658**: A tabela deve ser mantida conforme as normas regulatórias do Banco Central, especialmente em relação à confidencialidade e retenção de dados.

## Pontos de Atenção

1. **Duplicatas de Nomes**: A coluna `nm_cliente` apresenta duplicatas que devem ser investigadas.
2. **Percentual de Nulos em `vl_renda_mensal`**: O percentual de nulos é maior que o esperado, especialmente para segmentos PJ, o que pode indicar inconsistências.
3. **Valores de Agência**: A coluna `cd_agencia` apresenta valores frequentes que podem indicar duplicatas ou erros.
4. **Validação de CPF/CNPJ**: Assegurar que todos os valores na coluna `nr_cpf_cnpj` são válidos.
5. **Compliance LGPD**: Garantir que as práticas de tratamento de dados sensíveis estejam alinhadas com a LGPD.

---

> **[AI_METADATA_STATUS: DRAFT]** — Documentação gerada por SLM. Requer validação humana pelo Data Steward responsável antes de uso em produção.