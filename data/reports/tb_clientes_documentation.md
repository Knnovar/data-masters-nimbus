# Dicionário Técnico da Tabela `tb_clientes`

## Visão Geral

A tabela `tb_clientes` é um cadastro mestre de clientes pessoa física e jurídica, utilizada por todos os produtos de crédito e relacionamento do banco. A segmentação dos clientes determina o produto oferecido e o gestor responsável. A tabela é atualizada diariamente pelo batch noturno do sistema CORE_BANCARIO_TOTVS.

## Colunas

### `cd_cliente`
- **Tipo**: `string`
- **Nullable**: Não
- **Descrição**: Código único do cliente no sistema legado, gerado sequencialmente pelo CORE_BANCARIO.
- **Propósito de Negócio**: Identificação única de cada cliente.
- **Comportamento Esperado**: Cada valor deve ser único e não nulo.
- **Anomalias**: Nenhuma anomalia observada, pois todos os valores são únicos e não nulos.

### `nr_cpf_cnpj`
- **Tipo**: `string`
- **Nullable**: Não
- **Descrição**: CPF (11 dígitos) ou CNPJ (14 dígitos) sem máscara.
- **Propósito de Negócio**: Identificação fiscal do cliente.
- **Comportamento Esperado**: Deve conter 11 ou 14 dígitos, nunca nulo.
- **Anomalias**: Nenhuma anomalia observada, pois todos os valores são únicos e não nulos.
- **Implicações de Compliance**: Sensível conforme LGPD.

### `nm_cliente`
- **Tipo**: `string`
- **Nullable**: Não
- **Descrição**: Nome completo do cliente conforme cadastro na Receita Federal.
- **Propósito de Negócio**: Nome do cliente para identificação.
- **Comportamento Esperado**: Deve ser único e não nulo.
- **Anomalias**: Algumas duplicatas observadas (ex: "Elisa Pereira", "Ísis Moraes", "Heitor Viana").
- **Implicações de Compliance**: Sensível conforme LGPD.

### `dt_nascimento`
- **Tipo**: `date`
- **Nullable**: Sim
- **Descrição**: Data de nascimento. Nula para clientes PJ.
- **Propósito de Negócio**: Informação demográfica do cliente.
- **Comportamento Esperado**: Nula para clientes PJ, não nula para PF.
- **Anomalias**: Nenhuma anomalia observada.

### `cd_segmento`
- **Tipo**: `string`
- **Nullable**: Não
- **Descrição**: Segmento de relacionamento. Domínio: VAREJO, PRIME, PRIVATE, PJ_PEQUENO, PJ_MEDIO.
- **Propósito de Negócio**: Determina o produto oferecido e o gestor responsável.
- **Comportamento Esperado**: Deve seguir as regras de negócio associadas a cada segmento.
- **Anomalias**: Valores fora de domínio observados (ex: "PRIME" e "PJ_MEDIO" misturados).

### `cd_agencia`
- **Tipo**: `string`
- **Nullable**: Não
- **Descrição**: Código numérico de 4 dígitos da agência de relacionamento principal.
- **Propósito de Negócio**: Identificação da agência responsável pelo cliente.
- **Comportamento Esperado**: Deve ser um código numérico de 4 dígitos.
- **Anomalias**: Valores inválidos observados (ex: "AGENC-").

### `vl_renda_mensal`
- **Tipo**: `float`
- **Nullable**: Sim
- **Descrição**: Renda mensal declarada em BRL. Nula para clientes PJ.
- **Propósito de Negócio**: Informação financeira do cliente.
- **Comportamento Esperado**: Nula para segmentos PJ_PEQUENO e PJ_MEDIO.
- **Anomalias**: Nenhuma anomalia observada.
- **Implicações de Compliance**: Candidato a SCR.

### `fl_ativo`
- **Tipo**: `boolean`
- **Nullable**: Não
- **Descrição**: Indica se o cliente possui relacionamento ativo com o banco.
- **Propósito de Negócio**: Status de ativação do cliente.
- **Comportamento Esperado**: Deve ser verdadeiro ou falso.

### `dt_cadastro`
- **Tipo**: `date`
- **Nullable**: Não
- **Descrição**: Data de abertura do cadastro no sistema.
- **Propósito de Negócio**: Registro da data de cadastro do cliente.
- **Comportamento Esperado**: Deve ser uma data válida e não nula.

## Regras de Negócio

- **PRIME**: `vl_renda_mensal >= 10000`
- **PRIVATE**: `vl_renda_mensal >= 30000`
- **Sempre nulo para `cd_segmento` IN (PJ_PEQUENO, PJ_MEDIO)**

## Anomalias Observadas

- Duplicatas nos nomes de clientes.
- Valores fora de domínio no `cd_segmento`.
- Valores inválidos no `cd_agencia`.

## Implicações de Compliance

- **LGPD**: Dados sensíveis como `nr_cpf_cnpj`, `nm_cliente`, e `dt_nascimento` são classificados como sensíveis.
- **BACEN_4658**: Classificação de dados como confidencial com retenção de 10 anos.

## Pontos de Atenção

1. **Duplicatas de Nomes**: Verificar a causa das duplicatas nos nomes de clientes.
2. **Valores Fora de Domínio**: Corrigir os valores fora de domínio no `cd_segmento`.
3. **Valores Inválidos**: Investigar e corrigir os valores inválidos no `cd_agencia`.
4. **Compliance LGPD**: Assegurar que os dados sensíveis estão protegidos conforme a LGPD.
5. **Regras de Negócio**: Garantir que as regras de negócio associadas aos segmentos estão sendo respeitadas.

---

> **[AI_METADATA_STATUS: DRAFT]** — Documentação gerada por SLM. Requer validação humana pelo Data Steward responsável antes de uso em produção.