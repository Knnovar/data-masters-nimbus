# Dicionário Técnico da Tabela `tb_clientes`

## Visão Geral

A tabela `tb_clientes` representa o cadastro mestre de clientes pessoa física e jurídica. Ela é utilizada por todos os produtos de crédito e relacionamento do banco, com segmentação que determina o produto ofertado e o gestor responsável. A tabela é atualizada diariamente pelo batch noturno do sistema CORE_BANCARIO_TOTVS.

### Propriedades da Tabela

- **Owner**: squad-dados-cadastrais
- **Versão**: 1.0.0
- **Status do Manifesto**: DRAFT
- **Fonte**: Sistema CORE_BANCARIO_TOTVS, formato CSV, codificação UTF-8, sistema operacional Unix, atualização diária.
- **Contato**: squad-dados-cadastrais@banco.com.br
- **Classificação de Dados**: Confidencial
- **Período de Retenção**: 10 anos
- **Tags Regulatórias**: LGPD, BACEN_4658

## Colunas

### `cd_cliente`
- **Tipo**: VARCHAR
- **Descrição**: Código único do cliente no sistema legado, gerado sequencialmente pelo CORE_BANCARIO.
- **Negócio**: Serve como identificador primário para cada cliente.
- **Estatísticas**: 0% de valores nulos, 500 valores únicos.
- **Anomalias**: Nenhuma.

### `nr_cpf_cnpj`
- **Tipo**: VARCHAR
- **Descrição**: CPF (11 dígitos) ou CNPJ (14 dígitos) sem máscara.
- **Negócio**: Identificador único de clientes pessoa física ou jurídica.
- **Estatísticas**: 0% de valores nulos, 500 valores únicos, valores variam entre 1284567958.0 e 98751263491.0.
- **Anomalias**: Nenhuma.
- **Implicações Regulatórias**: Considerado sensível sob a LGPD.

### `nm_cliente`
- **Tipo**: VARCHAR
- **Descrição**: Nome completo do cliente conforme cadastro na Receita Federal.
- **Negócio**: Nome do cliente para identificação.
- **Estatísticas**: 0% de valores nulos, 495 valores únicos.
- **Anomalias**: 5 duplicatas identificadas.
- **Implicações Regulatórias**: Considerado sensível sob a LGPD.

### `dt_nascimento`
- **Tipo**: VARCHAR
- **Descrição**: Data de nascimento. Nula para clientes PJ.
- **Negócio**: Data de nascimento para clientes pessoa física.
- **Estatísticas**: 0% de valores nulos, 495 valores únicos.
- **Anomalias**: Nenhuma.

### `cd_segmento`
- **Tipo**: VARCHAR
- **Descrição**: Segmento de relacionamento. Domínio: VAREJO, PRIME, PRIVATE, PJ_PEQUENO, PJ_MEDIO.
- **Negócio**: Determina o produto ofertado e o gestor responsável.
- **Estatísticas**: 0% de valores nulos, 5 valores únicos.
- **Anomalias**: Nenhuma.
- **Regras de Negócio**: 
  - PRIME: `vl_renda_mensal >= 10000`
  - PRIVATE: `vl_renda_mensal >= 30000`
  - Sempre nulo para `cd_segmento` IN (PJ_PEQUENO, PJ_MEDIO).

### `cd_agencia`
- **Tipo**: VARCHAR
- **Descrição**: Código numérico de 4 dígitos da agência de relacionamento principal.
- **Negócio**: Identifica a agência principal do cliente.
- **Estatísticas**: 0% de valores nulos, 473 valores únicos.
- **Anomalias**: 15 ocorrências do valor "AGENC-???".

### `vl_renda_mensal`
- **Tipo**: VARCHAR
- **Descrição**: Renda mensal declarada em BRL. Nula para clientes PJ.
- **Negócio**: Indica a renda mensal do cliente.
- **Estatísticas**: 20.6% de valores nulos, 397 valores únicos.
- **Anomalias**: Nenhuma.
- **Implicações Regulatórias**: Candidato a SCR (Sensitive Content Review).

### `fl_ativo`
- **Tipo**: VARCHAR
- **Descrição**: Indica se o cliente possui relacionamento ativo com o banco.
- **Negócio**: Status de ativação do cliente.
- **Estatísticas**: 0% de valores nulos, 2 valores únicos (True/False).
- **Anomalias**: Nenhuma.

### `dt_cadastro`
- **Tipo**: VARCHAR
- **Descrição**: Data de abertura do cadastro no sistema.
- **Negócio**: Data de criação do cadastro do cliente.
- **Estatísticas**: 0% de valores nulos, 462 valores únicos.
- **Anomalias**: Nenhuma.

## Pontos de Atenção

- **Duplicatas**: Identificadas no campo `nm_cliente`, o que pode indicar problemas de integridade de dados.
- **Valores Nulos**: `vl_renda_mensal` possui 20.6% de valores nulos, o que pode afetar análises de renda.
- **Valores Anômalos**: Ocorrência de "AGENC-???" no campo `cd_agencia` sugere dados incorretos ou não processados.
- **Compliance LGPD**: Campos `nr_cpf_cnpj`, `nm_cliente`, e `dt_nascimento` são sensíveis e devem ser tratados conforme a LGPD.
- **Regras de Negócio**: Verificar se `vl_renda_mensal` está sempre nulo para `cd_segmento` IN (PJ_PEQUENO, PJ_MEDIO).

---
> **[AI_METADATA_STATUS: DRAFT]** — Documentação gerada por SLM. Requer validação humana pelo Data Steward responsável antes de uso em produção.