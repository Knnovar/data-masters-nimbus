# Dicionário Técnico da Tabela `tb_clientes`

## Visão Geral

A tabela `tb_clientes` é a base de dados mestre de clientes, tanto pessoas físicas quanto jurídicas, utilizada por todos os produtos de crédito e relacionamento do banco. A segmentação dos clientes determina os produtos oferecidos e o gestor responsável. A tabela é atualizada diariamente pelo batch noturno do sistema CORE_BANCARIO_TOTVS.

### Propriedades da Tabela

- **Owner**: squad-dados-cadastrais
- **Versão**: 1.0.0
- **Status do Manifesto**: VALIDADO
- **Fonte**: Sistema CORE_BANCARIO_TOTVS, formato CSV, codificação UTF-8, sistema operacional Unix, atualização diária.
- **Contato**: squad-dados-cadastrais@banco.com.br
- **Classificação de Dados**: Confidencial
- **Retenção de Dados**: 10 anos
- **Tags Regulatórias**: LGPD, BACEN_4658
- **Validado por**: Renan Apolinario em 12 de setembro de 2026

## Colunas

### cd_cliente
- **Tipo**: string
- **Nullable**: false
- **Descrição**: Código único do cliente no sistema legado, gerado sequencialmente pelo CORE_BANCARIO.
- **Comportamento Esperado**: Cada cliente deve ter um código único. Não deve haver valores nulos ou duplicados.
- **Estatísticas**: 500 valores únicos, 0% de valores nulos.

### nr_cpf_cnpj
- **Tipo**: string
- **Nullable**: false
- **Descrição**: CPF (11 dígitos) ou CNPJ (14 dígitos) sem máscara.
- **Comportamento Esperado**: Deve conter um CPF ou CNPJ válido, sem valores nulos.
- **Estatísticas**: 500 valores únicos, 0% de valores nulos.
- **Implicações de Compliance**: Sensível conforme LGPD.
- **Formato**: 11 ou 14 dígitos.

### nm_cliente
- **Tipo**: string
- **Nullable**: false
- **Descrição**: Nome completo do cliente conforme cadastro na Receita Federal.
- **Comportamento Esperado**: Deve conter o nome completo do cliente, sem valores nulos.
- **Estatísticas**: 497 valores únicos, 0% de valores nulos.
- **Implicações de Compliance**: Sensível conforme LGPD.
- **Formato**: Nome completo.

### dt_nascimento
- **Tipo**: string
- **Nullable**: true
- **Descrição**: Data de nascimento. Nula para clientes PJ.
- **Comportamento Esperado**: Deve conter a data de nascimento para clientes PF, nula para PJ.
- **Estatísticas**: 495 valores únicos, 0% de valores nulos.
- **Implicações de Compliance**: Sensível conforme LGPD.
- **Formato**: AAAA-MM-DD.

### cd_segmento
- **Tipo**: string
- **Nullable**: false
- **Descrição**: Segmento de relacionamento. Dominio: VAREJO, PRIME, PRIVATE, PJ_PEQUENO, PJ_MEDIO.
- **Comportamento Esperado**: Deve seguir as regras de negócio associadas a cada segmento.
- **Estatísticas**: 5 valores únicos, 0% de valores nulos.
- **Regras de Negócio**:
  - PRIME: vl_renda_mensal >= 10000
  - PRIVATE: vl_renda_mensal >= 30000
- **Anomalias**: Alta concentração de clientes nos segmentos PJ_PEQUENO e PJ_MEDIO.

### cd_agencia
- **Tipo**: string
- **Nullable**: false
- **Descrição**: Código numérico de 4 dígitos da agência de relacionamento principal.
- **Comportamento Esperado**: Deve conter um código válido de agência, sem valores nulos.
- **Estatísticas**: 473 valores únicos, 0% de valores nulos.
- **Anomalias**: Algumas agências têm múltiplos clientes associados, o que pode indicar duplicatas.

### vl_renda_mensal
- **Tipo**: string
- **Nullable**: true
- **Descrição**: Renda mensal declarada em BRL. Nula para clientes PJ.
- **Comportamento Esperado**: Deve ser nulo para segmentos PJ_PEQUENO e PJ_MEDIO.
- **Estatísticas**: 369 valores únicos, 19.2% de valores nulos.
- **Implicações de Compliance**: Candidato a SCR.
- **Anomalias**: 19.2% de valores nulos, o que está dentro do limite de tolerância de 25%.

### fl_ativo
- **Tipo**: string
- **Nullable**: false
- **Descrição**: Indica se o cliente possui relacionamento ativo com o banco.
- **Comportamento Esperado**: Deve ser booleano, sem valores nulos.
- **Estatísticas**: 2 valores únicos, 0% de valores nulos.

### dt_cadastro
- **Tipo**: string
- **Nullable**: false
- **Descrição**: Data de abertura do cadastro no sistema.
- **Comportamento Esperado**: Deve conter a data de cadastro, sem valores nulos.
- **Estatísticas**: 462 valores únicos, 0% de valores nulos.

## Pontos de Atenção

1. **Segmentação de Clientes**: Alta concentração de clientes nos segmentos PJ_PEQUENO e PJ_MEDIO pode indicar uma necessidade de revisão das regras de negócio ou da coleta de dados.
2. **Renda Mensal**: A porcentagem de valores nulos (19.2%) está dentro do limite de tolerância, mas deve ser monitorada para garantir a qualidade dos dados.
3. **Agências**: A presença de múltiplos clientes associados a algumas agências pode indicar duplicatas, o que é proibido conforme as regras de tolerância.
4. **Compliance LGPD**: As colunas sensíveis (nr_cpf_cnpj, nm_cliente, dt_nascimento) devem ser tratadas com cuidado para garantir a conformidade com a LGPD.
5. **Validação de Dados**: A tabela deve ser validada regularmente para garantir a integridade e a qualidade dos dados.

---
> **[AI_METADATA_STATUS: DRAFT]** — Documentação gerada por SLM. Requer validação humana pelo Data Steward responsável antes de uso em produção.