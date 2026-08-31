# Dicionário Técnico da Tabela `tb_clientes`

## Visão Geral
A tabela `tb_clientes` é um cadastro mestre de clientes pessoa física e jurídica, utilizado por todos os produtos de crédito e relacionamento do banco. A segmentação dos clientes determina o produto oferecido e o gestor responsável. A tabela é atualizada diariamente pelo batch noturno do sistema CORE_BANCARIO_TOTVS.

## Colunas

### `cd_cliente`
- **Tipo**: `string`
- **Nullable**: `false`
- **Descrição**: Código único do cliente no sistema legado. Gerado sequencialmente pelo CORE_BANCARIO.
- **Propósito de Negócio**: Identificador único para cada cliente.
- **Comportamento Esperado**: Deve ser único e não nulo.
- **Estatísticas**: 499 valores únicos, 0% de nulos.

### `nr_cpf_cnpj`
- **Tipo**: `string`
- **Nullable**: `false`
- **Descrição**: CPF (11 dígitos) ou CNPJ (14 dígitos) sem máscara.
- **Propósito de Negócio**: Identificação fiscal do cliente.
- **Comportamento Esperado**: Deve conter 11 ou 14 dígitos, não nulo.
- **Regulatório**: SENSITIVO conforme LGPD.
- **Anomalias**: Nenhuma anomalia observada.

### `nm_cliente`
- **Tipo**: `string`
- **Nullable**: `false`
- **Descrição**: Nome completo do cliente conforme cadastro na Receita Federal.
- **Propósito de Negócio**: Nome do cliente para identificação.
- **Comportamento Esperado**: Deve ser único e não nulo.
- **Regulatório**: SENSITIVO conforme LGPD.
- **Estatísticas**: 495 valores únicos, 0% de nulos.
- **Anomalias**: 4 duplicatas observadas.

### `dt_nascimento`
- **Tipo**: `date`
- **Nullable**: `true`
- **Descrição**: Data de nascimento. Nula para clientes PJ.
- **Propósito de Negócio**: Informação demográfica do cliente.
- **Comportamento Esperado**: Nulo para clientes PJ.
- **Regulatório**: SENSITIVO conforme LGPD.
- **Anomalias**: Nenhuma anomalia observada.

### `cd_segmento`
- **Tipo**: `string`
- **Nullable**: `false`
- **Descrição**: Segmento de relacionamento. Domínio: VAREJO, PRIME, PRIVATE, PJ_PEQUENO, PJ_MEDIO.
- **Propósito de Negócio**: Determina o produto oferecido e o gestor responsável.
- **Comportamento Esperado**: Deve seguir as regras de negócio associadas a cada segmento.
- **Estatísticas**: 496 valores únicos, 0% de nulos.
- **Anomalias**: 3 duplicatas observadas.

### `cd_agencia`
- **Tipo**: `string`
- **Nullable**: `false`
- **Descrição**: Código numérico de 4 dígitos da agência de relacionamento principal.
- **Propósito de Negócio**: Identificação da agência responsável pelo cliente.
- **Comportamento Esperado**: Deve ser um código numérico de 4 dígitos.
- **Estatísticas**: 473 valores únicos, 0% de nulos.
- **Anomalias**: 26 valores incomuns observados (ex: "AGENC-").

### `vl_renda_mensal`


---
> **[AI_METADATA_STATUS: DRAFT]**