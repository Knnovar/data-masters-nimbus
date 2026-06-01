# Dicionário Técnico da Tabela `tb_clientes`

## Visão Geral

A tabela `tb_clientes` é um cadastro mestre de clientes pessoa física e jurídica, utilizada por todos os produtos de crédito e relacionamento do banco. A segmentação dos clientes determina o produto ofertado e o gestor responsável. Esta tabela é atualizada diariamente pelo batch noturno do sistema CORE_BANCARIO_TOTVS.

### Propriedades da Tabela

- **Owner**: squad-dados-cadastrais
- **Versão**: 1.0.0
- **Status do Manifesto**: DRAFT
- **Fonte**:
  - Sistema: CORE_BANCARIO_TOTVS
  - Formato: CSV
  - Codificação: UTF-8
  - Sistema Operacional: Unix
  - Frequência de Atualização: Diária
  - Contato: squad-dados-cadastrais@banco.com.br

### Regulamentação e Classificação de Dados

- **Tags Regulatórias**: LGPD, BACEN_4658
- **Classificação de Dados**: Confidencial
- **Período de Retenção**: 10 anos

## Colunas da Tabela

### `cd_cliente`

- **Tipo**: String
- **Nullable**: Não
- **Descrição**: Código único do cliente no sistema legado, gerado sequencialmente pelo CORE_BANCARIO.
- **Propósito de Negócio**: Identificação única dos clientes.
- **Comportamento Esperado**: Valor único para cada registro.
- **Estatísticas**:
  - Percentual de Nulos: 0.0%
  - Contagem Única: 500
- **Anomalias**: Nenhuma.

### `nr_cpf_cnpj`

- **Tipo**: String
- **Nullable**: Não
- **Descrição**: CPF (11 dígitos) ou CNPJ (14 dígitos) sem máscara.
- **Propósito de Negócio**: Identificação fiscal dos clientes.
- **Comportamento Esperado**: Valores únicos e formatados corretamente como CPF ou CNPJ.
- **Estatísticas**:
  - Percentual de Nulos: 0.0%
  - Contagem Única: 500
  - Mínimo: 1234895714.0
  - Máximo: 98607321404.0
  - Média: 48891133242.918
- **Anomalias**: Nenhuma.
- **Implicações de Compliance**: Sensível conforme LGPD.

### `nm_cliente`

- **Tipo**: String
- **Nullable**: Não
- **Descrição**: Nome completo do cliente conforme cadastro na Receita Federal.
- **Propósito de Negócio**: Identificação nominal dos clientes.
- **Comportamento Esperado**: Valores únicos, exceto em casos raros de duplicação.
- **Estatísticas**:
  - Percentual de Nulos: 0.0%
  - Contagem Única: 498
- **Anomalias**: Duplicatas observadas (ex.: "Maya Cavalcanti" e "Alexandre Duarte").
- **Implicações de Compliance**: Sensível conforme LGPD.

### `dt_nascimento`

- **Tipo**: String (esperado Date)
- **Nullable**: Sim
- **Descrição**: Data de nascimento. Nula para clientes PJ.
- **Propósito de Negócio**: Informação demográfica dos clientes PF.
- **Comportamento Esperado**: Formato correto de data, nulo para PJ.
- **

---
> **[AI_METADATA_STATUS: DRAFT]**