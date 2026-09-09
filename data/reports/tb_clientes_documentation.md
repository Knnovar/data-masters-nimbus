# Dicionário Técnico da Tabela `tb_clientes`

## Visão Geral

A tabela `tb_clientes` é um cadastro mestre de clientes pessoa física e jurídica, utilizado por todos os produtos de crédito e relacionamento do banco. A segmentação (`cd_segmento`) determina o produto oferecido e o gestor responsável. A tabela é atualizada diariamente pelo batch noturno do sistema CORE_BANCARIO_TOTVS.

### Propriedades da Tabela

- **Owner**: squad-dados-cadastrais
- **Versão**: 1.0.0
- **Status do Manifesto**: DRAFT
- **Fonte**: Sistema CORE_BANCARIO_TOTVS, formato CSV, codificação UTF-8, sistema operacional Unix, atualização diária.
- **Contato**: squad-dados-cadastrais@banco.com.br
- **Classificação de Dados**: Confidencial
- **Tags Regulatórias**: LGPD, BACEN_4658
- **Período de Retenção**: 10 anos

## Colunas

### `cd_cliente`
- **Tipo**: VARCHAR
- **Nullable**: Não
- **Descrição**: Código único do cliente no sistema legado, gerado sequencialmente pelo CORE_BANCARIO.
- **Comportamento Esperado**: Cada cliente deve ter um código único. Não deve haver valores nulos ou duplicados.
- **Estatísticas**:
  - Percentual de nulos: 0.0%
  - Contagem única: 500
- **Anomalias**: Nenhuma

### `nr_cpf_cnpj`
- **Tipo**: VARCHAR
- **Nullable**: Não
- **Descrição**: CPF (11 dígitos) ou CNPJ (14 dígitos) sem máscara.
- **Comportamento Esperado**: Deve conter um CPF ou CNPJ válido, sem valores nulos.
- **Estatísticas**:
  - Percentual de nulos: 0.0%
  - Contagem única: 500
  - Sensível: Sim
  - Faixa: [MASCARADO]
- **Anomalias**: Nenhuma
- **Implicações de Compliance**: Regulada pela LGPD como LGPD_SENSITIVE.

### `nm_cliente`
- **Tipo**: VARCHAR
- **Nullable**: Não
- **Descrição**: Nome completo do cliente conforme cadastro na Receita Federal.
- **Comportamento Esperado**: Deve conter o nome completo do cliente, sem valores nulos.
- **Estatísticas**:
  - Percentual de nulos: 0.0%
  - Contagem única: 498
  - Sensível: Sim
- **Anomalias**: Existem 2 duplicatas.
- **Implicações de Compliance**: Regulada pela LGPD como LGPD_SENSITIVE.

### `dt_nascimento`
- **Tipo**: VARCHAR
- **Nullable**: Sim
- **Descrição**: Data de nascimento. Nula para clientes PJ.
- **Comportamento Esperado**: Deve conter a data de nascimento para clientes PF, nula para PJ.
- **Estatísticas**:
  - Percentual de nulos: 0.0%
  - Contagem única: 495
  - Sensível: Sim
- **Anomalias**: Nenhuma
- **Implicações de Compliance**: Regulada pela LGPD como LGPD_SENSITIVE.

### `cd_segmento`
- **Tipo**: VARCHAR
- **Nullable**: Não
- **Descrição**: Segmento de relacionamento. Dominio: VAREJO, PRIME, PRIVATE, PJ_PEQUENO, PJ_MEDIO.
- **Comportamento Esperado**: Deve conter um valor válido do domínio especificado.
- **Estatísticas**:
  - Percentual de nulos: 0.0%
  - Contagem única: 5
- **Anomalias**: Nenhuma
- **Regras de Negócio**:
  - PRIME: vl_renda_mensal >= 10000
  - PRIVATE: vl_renda_mensal >= 30000

### `cd_agencia`
- **Tipo**: VARCHAR
- **Nullable**: Não
- **Descrição**: Código numérico de 4 dígitos da agência de relacionamento principal.
- **Comportamento Esperado**: Deve conter um código de agência válido, sem valores nulos.
- **Estatísticas**:
  - Percentual de nulos: 0.0%
  - Contagem única: 473
- **Anomalias**: Existem 27 duplicatas.

### `vl_renda_mensal`
- **Tipo**: VARCHAR
- **Nullable**: Sim
- **Descrição**: Renda mensal declarada em BRL. Nula para clientes PJ.
- **Comportamento Esperado**: Deve ser nulo para segmentos PJ_PEQUENO e PJ_MEDIO.
- **Estatísticas**:
  - Percentual de nulos: 19.2%
  - Contagem única: 369
- **Anomalias**: 
  - Percentual de nulos acima do esperado (25%).
  - Valores nulos para segmentos PJ_PEQUENO e PJ_MEDIO não são garantidos.
- **Implicações de Compliance**: Regulada como SCR_CANDIDATE.

### `fl_ativo`
- **Tipo**: VARCHAR
- **Nullable**: Não
- **Descrição**: Indica se o cliente possui relacionamento ativo com o banco.
- **Comportamento Esperado**: Deve ser verdadeiro ou falso, sem valores nulos.
- **Estatísticas**:
  - Percentual de nulos: 0.0%
  - Contagem única: 2
- **Anomalias**: Nenhuma

### `dt_cadastro`
- **Tipo**: VARCHAR
- **Nullable**: Não
- **Descrição**: Data de abertura do cadastro no sistema.
- **Comportamento Esperado**: Deve conter a data de cadastro, sem valores nulos.
- **Estatísticas**:
  - Percentual de nulos: 0.0%
  - Contagem única: 462
- **Anomalias**: Existem 38 duplicatas.

## Pontos de Atenção

1. **Duplicatas**: Existem duplicatas nas colunas `nm_cliente`, `cd_agencia` e `dt_cadastro`, o que pode afetar a integridade dos dados.
2. **Valores Nulos**: O percentual de nulos na coluna `vl_renda_mensal` é maior que o esperado, e não há garantia de que seja nulo para segmentos PJ_PEQUENO e PJ_MEDIO.
3. **Compliance**: As colunas `nr_cpf_cnpj`, `nm_cliente` e `dt_nascimento` são sensíveis e reguladas pela LGPD, exigindo cuidados adicionais no manuseio.
4. **Regras de Negócio**: As regras de negócio associadas ao `cd_segmento` devem ser validadas para garantir a consistência dos dados.
5. **Atualização Diária**: A tabela é atualizada diariamente, o que requer monitoramento constante para garantir a qualidade dos dados.

> **[AI_METADATA_STATUS: DRAFT]** — Documentação gerada por SLM. Requer validação humana pelo Data Steward responsável antes de uso em produção.