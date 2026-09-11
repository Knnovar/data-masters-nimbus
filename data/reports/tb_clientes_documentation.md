# Dicionário Técnico da Tabela `tb_clientes`

## Visão Geral

A tabela `tb_clientes` é um cadastro mestre de clientes pessoa física e jurídica. Ela é utilizada por todos os produtos de crédito e relacionamento do banco. A segmentação dos clientes determina o produto ofertado e o gestor responsável. A tabela é atualizada diariamente pelo batch noturno do sistema CORE_BANCARIO_TOTVS.

### Propriedades da Tabela

- **Owner**: squad-dados-cadastrais
- **Versão**: 1.0.0
- **Status do Manifesto**: DRAFT
- **Fonte**: Sistema CORE_BANCARIO_TOTVS, formato CSV, codificação UTF-8, sistema operacional Unix, atualização diária.
- **Contato**: squad-dados-cadastrais@banco.com.br
- **Classificação de Dados**: Confidencial
- **Período de Retenção**: 10 anos
- **Regulamentações**: LGPD, BACEN_4658
- **Tolerância**:
  - Máximo de nulos: 25%
  - Máximo de rejeições: 1%
  - Duplicatas não permitidas

### Dependências

- `tb_agencias`
- `tb_segmentos`

## Colunas

### `cd_cliente`

- **Tipo**: String
- **Nullable**: Não
- **Chave Primária**: Sim
- **Descrição**: Código único do cliente no sistema legado. Gerado sequencialmente pelo CORE_BANCARIO.
- **Estatísticas**:
  - Percentual de nulos: 0.0%
  - Contagem única: 500
- **Comportamento Esperado**: Cada cliente deve ter um código único e não nulo.

### `nr_cpf_cnpj`

- **Tipo**: String
- **Nullable**: Não
- **Descrição**: CPF (11 dígitos) ou CNPJ (14 dígitos) sem máscara.
- **Regulamentações**: LGPD_SENSITIVE
- **Estatísticas**:
  - Percentual de nulos: 0.0%
  - Contagem única: 500
  - Sensível: Sim
  - Faixa: [MASCARADO]
  - Formato: 99999999999
- **Comportamento Esperado**: Deve conter um CPF ou CNPJ válido e único para cada cliente.

### `nm_cliente`

- **Tipo**: String
- **Nullable**: Não
- **Descrição**: Nome completo do cliente conforme cadastro na Receita Federal.
- **Regulamentações**: LGPD_SENSITIVE
- **Estatísticas**:
  - Percentual de nulos: 0.0%
  - Contagem única: 500
  - Sensível: Sim
  - Formato: AA. AAAAAA AA AAAAA
- **Comportamento Esperado**: Deve conter o nome completo do cliente e ser único.

### `dt_nascimento`

- **Tipo**: String (Deveria ser Date)
- **Nullable**: Sim
- **Descrição**: Data de nascimento. Nula para clientes PJ.
- **Regulamentações**: LGPD_SENSITIVE
- **Estatísticas**:
  - Percentual de nulos: 5.0%
  - Contagem única: 495
  - Sensível: Sim
  - Formato: 9999-99-99
- **Comportamento Esperado**: Deve conter a data de nascimento para clientes PF e ser nula para PJ.

### `cd_segmento`

- **Tipo**: String
- **Nullable**: Não
- **Descrição**: Segmento de relacionamento. Domínio: VAREJO, PRIME, PRIVATE, PJ_PEQUENO, PJ_MEDIO.
- **Regras de Negócio**:
  - PRIME: `vl_renda_mensal >= 10000`
  - PRIVATE: `vl_renda_mensal >= 30000`
- **Estatísticas**:
  - Percentual de nulos: 0.0%
  - Contagem única: 5
  - Valores mais comuns: PJ_PEQUENO, PRIVATE, PJ_MEDIO
- **Comportamento Esperado**: Deve seguir as regras de negócio associadas a cada segmento.

### `cd_agencia`

- **Tipo**: String
- **Nullable**: Não
- **Descrição**: Código numérico de 4 dígitos da agência de relacionamento principal.
- **Estatísticas**:
  - Percentual de nulos: 0.0%
  - Contagem única: 473
  - Mínimo: 1027.0
  - Máximo: 9984.0
  - Média: 5541.2062
- **Comportamento Esperado**: Deve conter um código de agência válido e único.

### `vl_renda_mensal`

- **Tipo**: String (Deveria ser Float)
- **Nullable**: Sim
- **Descrição**: Renda mensal declarada em BRL. Nula para clientes PJ.
- **Regras de Negócio**: Sempre nulo para `cd_segmento` IN (PJ_PEQUENO, PJ_MEDIO)
- **Regulamentações**: SCR_CANDIDATE
- **Estatísticas**:
  - Percentual de nulos: 20.6%
  - Contagem única: 397
  - Mínimo: 1669.2
  - Máximo: 79966.43
  - Média: 41564.8931
- **Comportamento Esperado**: Deve ser nulo para segmentos PJ e seguir as regras de negócio.

### `fl_ativo`

- **Tipo**: String (Deveria ser Boolean)
- **Nullable**: Não
- **Descrição**: Indica se o cliente possui relacionamento ativo com o banco.
- **Estatísticas**:
  - Percentual de nulos: 0.0%
  - Contagem única: 2
  - Valores mais comuns: False (253), True (247)
- **Comportamento Esperado**: Deve ser um valor booleano indicando o status do relacionamento.

### `dt_cadastro`

- **Tipo**: String (Deveria ser Date)
- **Nullable**: Não
- **Descrição**: Data de abertura do cadastro no sistema.
- **Estatísticas**:
  - Percentual de nulos: 0.0%
  - Contagem única: 462
  - Valores mais comuns: 2018-03-31, 2016-01-18
- **Comportamento Esperado**: Deve conter a data de cadastro do cliente.

## Anomalias e Pontos de Atenção

- **Tipo de Dados**: Algumas colunas (`dt_nascimento`, `vl_renda_mensal`, `fl_ativo`, `dt_cadastro`) estão listadas como VARCHAR, mas deveriam ser de tipos mais apropriados (Date, Float, Boolean).
- **Percentual de Nulos**: `vl_renda_mensal` tem 20.6% de nulos, o que pode indicar inconsistências, especialmente para segmentos PJ.
- **Duplicatas**: A tabela não deve conter duplicatas, mas não há informações sobre verificações de integridade referente a isso.
- **Segmentação**: Verificar se as regras de negócio para segmentação estão sendo aplicadas corretamente.
- **Regulamentações**: A tabela contém dados sensíveis (LGPD_SENSITIVE), exigindo cuidados adicionais com a proteção de dados.

---

> **[AI_METADATA_STATUS: DRAFT]** — Documentação gerada por SLM. Requer validação humana pelo Data Steward responsável antes de uso em produção.