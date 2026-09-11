# Dicionário Técnico da Tabela `tb_clientes`

## Visão Geral

A tabela `tb_clientes` é o cadastro mestre de clientes pessoa física e jurídica, utilizada por todos os produtos de crédito e relacionamento do banco. A segmentação (`cd_segmento`) determina o produto ofertado e o gestor responsável. A tabela é atualizada diariamente pelo batch noturno do sistema `CORE_BANCARIO_TOTVS`.

### Propriedades da Tabela

- **Owner**: squad-dados-cadastrais
- **Versão**: 1.0.0
- **Status do Manifesto**: DRAFT
- **Fonte**: Sistema `CORE_BANCARIO_TOTVS`, formato CSV, codificação UTF-8, sistema operacional Unix, atualização diária.
- **Contato**: squad-dados-cadastrais@banco.com.br
- **Classificação de Dados**: Confidencial
- **Período de Retenção**: 10 anos
- **Regulamentações**: LGPD, BACEN 4658

### Tolerâncias

- **Máximo de Nulos**: 25%
- **Máximo de Rejeições**: 1%
- **Duplicatas Permitidas**: Não

### Dependências

- `tb_agencias`
- `tb_segmentos`

## Colunas

### `cd_cliente`

- **Tipo**: String
- **Nullable**: Não
- **Chave Primária**: Sim
- **Descrição**: Código único do cliente no sistema legado. Gerado sequencialmente pelo `CORE_BANCARIO`.
- **Estatísticas**:
  - **% de Nulos**: 0%
  - **Contagem Única**: 499
- **Comportamento Esperado**: Deve ser único e não nulo.

### `nr_cpf_cnpj`

- **Tipo**: String
- **Nullable**: Não
- **Descrição**: CPF (11 dígitos) ou CNPJ (14 dígitos) sem máscara.
- **Regulamentações**: LGPD_SENSITIVE
- **Estatísticas**: Não disponíveis no perfil de dados.
- **Comportamento Esperado**: Deve ser único e não nulo, seguindo o padrão de CPF ou CNPJ.

### `nm_cliente`

- **Tipo**: String
- **Nullable**: Não
- **Descrição**: Nome completo do cliente conforme cadastro na Receita Federal.
- **Regulamentações**: LGPD_SENSITIVE
- **Estatísticas**:
  - **% de Nulos**: 0%
  - **Contagem Única**: 495
  - **Valores Comuns**: "Juan Rocha", "João Miguel da Luz", "Clarice Pires" (cada um com 2 ocorrências)
- **Comportamento Esperado**: Deve ser único e não nulo.

### `dt_nascimento`

- **Tipo**: Date
- **Nullable**: Sim
- **Descrição**: Data de nascimento. Nula para clientes PJ.
- **Regulamentações**: LGPD_SENSITIVE
- **Estatísticas**: Não disponíveis no perfil de dados.
- **Comportamento Esperado**: Deve ser nulo para clientes PJ.

### `cd_segmento`

- **Tipo**: String
- **Nullable**: Não
- **Descrição**: Segmento de relacionamento. Domínio: VAREJO, PRIME, PRIVATE, PJ_PEQUENO, PJ_MEDIO.
- **Regras de Negócio**:
  - PRIME: `vl_renda_mensal >= 10000`
  - PRIVATE: `vl_renda_mensal >= 30000`
- **Estatísticas**:
  - **% de Nulos**: 0%
  - **Contagem Única**: 496
  - **Valores Comuns**: "PJ_MEDIO" (com múltiplas ocorrências)
- **Comportamento Esperado**: Deve seguir as regras de negócio associadas a cada segmento.

### `cd_agencia`

- **Tipo**: String
- **Nullable**: Não
- **Descrição**: Código numérico de 4 dígitos da agência de relacionamento principal.
- **Estatísticas**:
  - **% de Nulos**: 0%
  - **Contagem Única**: 473
  - **Valores Comuns**: "AGENC-" (15 ocorrências)
- **Comportamento Esperado**: Deve ser um código numérico válido de 4 dígitos.

### `vl_renda_mensal`

- **Tipo**: Float
- **Nullable**: Sim
- **Descrição**: Renda mensal declarada em BRL. Nula para clientes PJ.
- **Regras de Negócio**: Sempre nulo para `cd_segmento` IN (PJ_PEQUENO, PJ_MEDIO)
- **Regulamentações**: SCR_CANDIDATE
- **Estatísticas**: Não disponíveis no perfil de dados.
- **Comportamento Esperado**: Deve ser nulo para segmentos PJ_PEQUENO e PJ_MEDIO.

### `fl_ativo`

- **Tipo**: Boolean
- **Nullable**: Não
- **Descrição**: Indica se o cliente possui relacionamento ativo com o banco.
- **Estatísticas**: Não disponíveis no perfil de dados.
- **Comportamento Esperado**: Deve ser verdadeiro ou falso.

### `dt_cadastro`

- **Tipo**: Date
- **Nullable**: Não
- **Descrição**: Data de abertura do cadastro no sistema.
- **Estatísticas**: Não disponíveis no perfil de dados.
- **Comportamento Esperado**: Deve ser uma data válida.

## Anomalias Observadas

- **Duplicatas de Nome**: O nome "Juan Rocha", "João Miguel da Luz" e "Clarice Pires" aparecem mais de uma vez, o que pode indicar duplicatas.
- **Código de Agência**: O valor "AGENC-" aparece 15 vezes, o que pode indicar dados incorretos ou incompletos.

## Implicações de Compliance

- **LGPD**: Dados sensíveis como CPF/CNPJ, nome e data de nascimento estão sujeitos a regulamentações de proteção de dados.
- **BACEN 4658**: Requisitos de segurança e privacidade de dados financeiros.

## Pontos de Atenção

1. **Duplicatas de Nome**: Verificar e corrigir duplicatas nos nomes dos clientes.
2. **Código de Agência**: Investigar a presença do código "AGENC-" para garantir a integridade dos dados.
3. **Segmentação de Renda**: Assegurar que a segmentação de renda esteja correta conforme as regras de negócio.
4. **Dados Sensíveis**: Manter a conformidade com a LGPD para dados sensíveis.
5. **Atualização Diária**: Garantir que a atualização diária do batch noturno esteja funcionando corretamente para manter a precisão dos dados.

---

> **[AI_METADATA_STATUS: DRAFT]** — Documentação gerada por SLM. Requer validação humana pelo Data Steward responsável antes de uso em produção.