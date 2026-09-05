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
- **Período de Retenção**: 10 anos
- **Regulamentos**: LGPD, BACEN 4658

## Colunas

### `cd_cliente`
- **Tipo**: VARCHAR
- **Descrição**: Código único do cliente no sistema legado, gerado sequencialmente pelo CORE_BANCARIO.
- **Negócio**: Serve como chave primária para identificar exclusivamente cada cliente.
- **Estatísticas**:
  - Nulo: 0.0%
  - Únicos: 500
- **Anomalias**: Nenhuma

### `nr_cpf_cnpj`
- **Tipo**: VARCHAR
- **Descrição**: CPF (11 dígitos) ou CNPJ (14 dígitos) sem máscara.
- **Negócio**: Identificador único de clientes pessoa física ou jurídica.
- **Estatísticas**:
  - Nulo: 0.0%
  - Únicos: 500
  - Mínimo: 1395764875.0
  - Máximo: 98763240556.0
  - Média: 51333586223.13
- **Anomalias**: Nenhuma
- **Implicações de Compliance**: Dados sensíveis sob LGPD.

### `nm_cliente`
- **Tipo**: VARCHAR
- **Descrição**: Nome completo do cliente conforme cadastro na Receita Federal.
- **Negócio**: Nome para identificação e comunicação com o cliente.
- **Estatísticas**:
  - Nulo: 0.0%
  - Únicos: 494
- **Anomalias**: Duplicatas observadas (ex.: "Leandro Moura", "Juan Pires", "Alice Correia").
- **Implicações de Compliance**: Dados sensíveis sob LGPD.

### `dt_nascimento`
- **Tipo**: VARCHAR
- **Descrição**: Data de nascimento. Nula para clientes PJ.
- **Negócio**: Usada para cálculo de idade e segmentação de clientes pessoa física.
- **Estatísticas**:
  - Nulo: 0.0%
  - Únicos: 495
- **Anomalias**: Nenhuma
- **Implicações de Compliance**: Dados sensíveis sob LGPD.

### `cd_segmento`
- **Tipo**: VARCHAR
- **Descrição**: Segmento de relacionamento. Dominio: VAREJO, PRIME, PRIVATE, PJ_PEQUENO, PJ_MEDIO.
- **Negócio**: Determina o produto oferecido e o gestor responsável.
- **Estatísticas**:
  - Nulo: 0.0%
  - Únicos: 5
  - Top Values: PJ_PEQUENO (110), PRIVATE (108), PJ_MEDIO (101)
- **Anomalias**: Nenhuma
- **Regras de Negócio**:
  - PRIME: `vl_renda_mensal >= 10000`
  - PRIVATE: `vl_renda_mensal >= 30000`
  - Sempre nulo para `cd_segmento` IN (PJ_PEQUENO, PJ_MEDIO)

### `cd_agencia`
- **Tipo**: VARCHAR
- **Descrição**: Código numérico de 4 dígitos da agência de relacionamento principal.
- **Negócio**: Identifica a agência responsável pelo relacionamento com o cliente.
- **Estatísticas**:
  - Nulo: 0.0%
  - Únicos: 473
  - Mínimo: 1027.0
  - Máximo: 9984.0
  - Média: 5541.2062
- **Anomalias**: Valores incomuns observados (ex.: "AGENC-???").

### `vl_renda_mensal`
- **Tipo**: VARCHAR
- **Descrição**: Renda mensal declarada em BRL. Nula para clientes PJ.
- **Negócio**: Usada para segmentação e análise de crédito.
- **Estatísticas**:
  - Nulo: 20.6%
  - Únicos: 397
  - Mínimo: 1669.2
  - Máximo: 79966.43
  - Média: 41564.8931
- **Anomalias**: Nulo para `cd_segmento` IN (PJ_PEQUENO, PJ_MEDIO), conforme regra de negócio.
- **Implicações de Compliance**: Candidato a SCR (Sistema de Controle de Risco).

### `fl_ativo`
- **Tipo**: VARCHAR
- **Descrição**: Indica se o cliente possui relacionamento ativo com o banco.
- **Negócio**: Usado para filtrar clientes ativos em análises e relatórios.
- **Estatísticas**:
  - Nulo: 0.0%
  - Únicos: 2
  - Top Values: False (253), True (247)
- **Anomalias**: Nenhuma

### `dt_cadastro`
- **Tipo**: VARCHAR
- **Descrição**: Data de abertura do cadastro no sistema.
- **Negócio**: Usada para análise de tempo de relacionamento e histórico de clientes.
- **Estatísticas**:
  - Nulo: 0.0%
  - Únicos: 462
- **Anomalias**: Nenhuma

## Pontos de Atenção

1. **Duplicatas**: Existem duplicatas no campo `nm_cliente`, o que pode indicar problemas de integridade de dados.
2. **Valores Nulos**: `vl_renda_mensal` tem 20.6% de valores nulos, o que pode impactar análises de crédito.
3. **Valores Incomuns**: O campo `cd_agencia` contém valores incomuns como "AGENC-???", que precisam ser investigados.
4. **Compliance**: Dados sensíveis sob LGPD requerem cuidados adicionais com proteção e acesso.
5. **Regras de Negócio**: Verificar se as regras de negócio para `cd_segmento` e `vl_renda_mensal` estão sendo respeitadas.

> **[AI_METADATA_STATUS: DRAFT]** — Documentação gerada por SLM. Requer validação humana pelo Data Steward responsável antes de uso em produção.