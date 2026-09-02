## Dicionário Técnico do Contrato de Dados: Tabela `tb_clientes`

**Contexto do Negócio:**
A tabela `tb_clientes` serve como o mestre de cadastro para clientes, tanto pessoa física (PF) quanto jurídica (JF), dentro do banco. Esta tabela é essencial para o gerenciamento de relacionamentos e para a definição de produtos de crédito ofertados, com base no segmento do cliente (`cd_segmento`).

**Dados Steward:**
- **Nome:** Data Steward Cadastral
- **Contato:** [squad-dados-cadastrais@banco.com.br](mailto:squad-dados-cadastrais@banco.com.br)

**Manifesto:**
```yaml
table: tb_clientes
description: Cadastro mestre de clientes pessoa física e jurídica.
owner: squad-dados-cadastrais
version: 1.0.0
manifest_status: DRAFT
source:
  system: CORE_BANCARIO_TOTVS
  format: csv
  encoding: utf-8
  os: unix
  update_frequency: daily
  contact: squad-dados-cadastrais@banco.com.br
regulatory:
  tags:
  - LGPD
  - BACEN_4658
  data_classification: confidential
  retention_years: 10
steward:
  name: Data Steward Cadastral
  email: steward-cadastral@banco.com.br
business_context: Tabela mestre de clientes utilizada por todos os produtos de credito
  e relacionamento. A segmentacao (cd_segmento) determina o produto ofertado e o gestor
  responsavel. Atualizada diariamente pelo batch noturno do CORE_BANCARIO_TOTVS.
tolerance:
  max_null_pct: 25
  allow_duplicates: false
dependencies:
- tb_agencias
- tb0_segmentos
sample_queries:
- description: Distribuicao por segmento
  sql: SELECT cd_segmento, COUNT(*) as qtd FROM tb_clientes WHERE fl_ativo = true
    GROUP BY cd_segmento
- description: Clientes ativos com renda acima de 10k
  sql: SELECT cd_cliente, nm_cliente, vl_renda_mensal FROM tb_clientes WHERE fl_ativo
    = true AND vl extrato_renda_mensal > 10000
schema:
- name: cd_cliente
  type: string
  nullable: false
  primary_key: true
  description: Codigo unico do cliente no sistema legado. Gerado sequencialmente pelo
    CORE_BANCARIO.
- name: nr_cpf_cnpj
  type: string
  nullable: false
  description: CPF (11 digitos) ou CNPJ (14 digitos) sem mascara.
  regulatory_flags:
  - LGPD_SENSITIVE
- name: nm_client

---
> **[AI_METADATA_STATUS: DRAFT]**