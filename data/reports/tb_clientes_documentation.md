# Dicionário Técnico da Tabela `tb_clientes`

## Visão Geral

A tabela `tb_clientes` é um cadastro mestre de clientes pessoa física e jurídica. Ela é utilizada por todos os produtos de crédito e relacionamento do banco. A segmentação (`cd_segmento`) determina o produto ofertado e o gestor responsável. A tabela é atualizada diariamente pelo batch noturno do sistema CORE_BANCARIO_TOTVS.

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
- **Nullable**: false
- **Descrição**: Código único do cliente no sistema legado. Gerado sequencialmente pelo CORE_BANCARIO.
- **Comportamento Esperado**: Cada cliente deve ter um código único. Não deve haver valores nulos ou duplicados.
- **Estatísticas**: 500 valores únicos, 0% de valores nulos.
- **Anomalias**: Nenhuma.

### `nr_cpf_cnpj`
- **Tipo**: string
- **Nullable**: false
- **Descrição**: CPF (11 dígitos) ou CNPJ (14 dígitos) sem máscara.
- **Comportamento Esperado**: Deve conter um CPF ou CNPJ válido, sem valores nulos.
- **Estatísticas**: 500 valores únicos, 0% de valores nulos.
- **Anomalias**: Nenhuma.
- **Implicações Regulatórias**: Sensível conforme LGPD.

### `nm_cliente`
- **Tipo**: string
- **Nullable**: false
- **Descrição**: Nome completo do cliente conforme cadastro na Receita Federal.
- **Comportamento Esperado**: Deve conter o nome completo do cliente, sem valores nulos.
- **Estatísticas**: 497 valores únicos, 0% de valores nulos.
- **Anomalias**: 3 duplicatas identificadas.
- **Implicações Regulatórias**: Sensível conforme LGPD.

### `dt_nascimento`
- **Tipo**: string (deveria ser date)
- **Nullable**: true
- **Descrição**: Data de nascimento. Nula para clientes PJ.
- **Comportamento Esperado**: Deve conter a data de nascimento para clientes PF, nulo para PJ.
- **Estatísticas**: 495 valores únicos, 0% de valores nulos.
- **Anomalias**: 5 duplicatas identificadas. Tipo de dado deve ser `date`.
- **Implicações Regulatórias**: Sensível conforme LGPD.

### `cd_segmento`
- **Tipo**: string
- **Nullable**: false
- **Descrição**: Segmento de relacionamento. Domínio: VAREJO, PRIME, PRIVATE, PJ_PEQUENO, PJ_MEDIO.
- **Comportamento Esperado**: Deve seguir as regras de negócio para segmentação.
- **Estatísticas**: 5 valores únicos, 0% de valores nulos.
- **Anomalias**: 
  - `vl_renda_mensal` deve ser nulo para `cd_segmento` em (PJ_PEQUENO, PJ_MEDIO).
  - Alta concentração de clientes em segmentos PJ.

### `cd_agencia`
- **Tipo**: string
- **Nullable**: false
- **Descrição**: Código numérico de 4 dígitos da agência de relacionamento principal.
- **Comportamento Esperado**: Deve conter um código válido de agência, sem valores nulos.
- **Estatísticas**: 473 valores únicos, 0% de valores nulos.
- **Anomalias**: 27 duplicatas identificadas.

### `vl_renda_mensal`
- **Tipo**: string (deveria ser float)
- **Nullable**: true
- **Descrição**: Renda mensal declarada em BRL. Nula para clientes PJ.
- **Comportamento Esperado**: Deve ser nulo para clientes PJ e seguir as regras de negócio para segmentação.
- **Estatísticas**: 397 valores únicos, 20.6% de valores nulos.
- **Anomalias**: 
  - Tipo de dado deve ser `float`.
  - 110 clientes PJ_PEQUENO e 101 clientes PJ_MEDIO têm renda mensal não nula.
- **Implicações Regulatórias**: Candidato a SCR.

### `fl_ativo`
- **Tipo**: string (deveria ser boolean)
- **Nullable**: false
- **Descrição**: Indica se o cliente possui relacionamento ativo com o banco.
- **Comportamento Esperado**: Deve ser `true` ou `false`, sem valores nulos.
- **Estatísticas**: 2 valores únicos, 0% de valores nulos.
- **Anomalias**: Tipo de dado deve ser `boolean`.

### `dt_cadastro`
- **Tipo**: string (deveria ser date)
- **Nullable**: false
- **Descrição**: Data de abertura do cadastro no sistema.
- **Comportamento Esperado**: Deve conter a data de cadastro, sem valores nulos.
- **Estatísticas**: 462 valores únicos, 0% de valores nulos.
- **Anomalias**: Tipo de dado deve ser `date`.

## Pontos de Atenção

1. **Tipo de Dados**: Algumas colunas (`dt_nascimento`, `vl_renda_mensal`, `fl_ativo`, `dt_cadastro`) têm tipos de dados incorretos conforme as estatísticas.
2. **Duplicatas**: Existem duplicatas em `nm_cliente`, `cd_agencia`, e `dt_nascimento`.
3. **Regras de Negócio**: 
   - `vl_renda_mensal` não é nulo para clientes PJ, contrariando as regras de negócio.
   - Alta concentração de clientes em segmentos PJ.
4. **Regulamentação**: 
   - Colunas sensíveis conforme LGPD (`nr_cpf_cnpj`, `nm_cliente`, `dt_nascimento`) devem ser tratadas com cuidado.
   - `vl_renda_mensal` é um candidato a SCR, exigindo monitoramento adicional.
5. **Tolerância**: A porcentagem de valores nulos em `vl_renda_mensal` está acima do limite de tolerância de 25%.

---

> **[AI_METADATA_STATUS: DRAFT]** — Documentação gerada por SLM. Requer validação humana pelo Data Steward responsável antes de uso em produção.