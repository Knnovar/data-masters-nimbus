# Dicionário Técnico da Tabela `tb_clientes`

## Visão Geral

A tabela `tb_clientes` é o cadastro mestre de clientes pessoa física e jurídica. Ela é utilizada por todos os produtos de crédito e relacionamento do banco. A segmentação dos clientes determina o produto oferecido e o gestor responsável. A tabela é atualizada diariamente pelo batch noturno do sistema CORE_BANCARIO_TOTVS.

## Colunas

### `cd_cliente`
- **Tipo**: `string`
- **Nullable**: Não
- **Descrição**: Código único do cliente no sistema legado. Gerado sequencialmente pelo CORE_BANCARIO.
- **Propósito de Negócio**: Identificador único para cada cliente.
- **Comportamento Esperado**: Deve ser único e não nulo.
- **Estatísticas Observadas**: 499 valores únicos, 0% de nulos.

### `nr_cpf_cnpj`
- **Tipo**: `string`
- **Nullable**: Não
- **Descrição**: CPF (11 dígitos) ou CNPJ (14 dígitos) sem máscara.
- **Propósito de Negócio**: Identificação fiscal do cliente.
- **Comportamento Esperado**: Deve conter 11 ou 14 dígitos, sem máscara.
- **Regulamentação**: Considerado sensível conforme LGPD.
- **Estatísticas Observadas**: Não aplicável diretamente, mas deve ser validado conforme descrição.

### `nm_cliente`
- **Tipo**: `string`
- **Nullable**: Não
- **Descrição**: Nome completo do cliente conforme cadastro na Receita Federal.
- **Propósito de Negócio**: Nome para identificação do cliente.
- **Comportamento Esperado**: Deve ser único e não nulo.
- **Regulamentação**: Considerado sensível conforme LGPD.
- **Estatísticas Observadas**: 496 valores únicos, 0% de nulos. Anomalia: 3 duplicatas observadas.

### `dt_nascimento`
- **Tipo**: `date`
- **Nullable**: Sim
- **Descrição**: Data de nascimento. Nula para clientes PJ.
- **Propósito de Negócio**: Informação demográfica do cliente.
- **Comportamento Esperado**: Nulo para clientes PJ.
- **Regulamentação**: Considerado sensível conforme LGPD.
- **Estatísticas Observadas**: Não aplicável diretamente, mas deve ser validado conforme descrição.

### `cd_segmento`
- **Tipo**: `string`
- **Nullable**: Não
- **Descrição**: Segmento de relacionamento. Domínio: VAREJO, PRIME, PRIVATE, PJ_PEQUENO, PJ_MEDIO.
- **Propósito de Negócio**: Determina o produto oferecido e o gestor responsável.
- **Comportamento Esperado**: Deve seguir as regras de negócio para renda mensal.
- **Estatísticas Observadas**: 496 valores únicos, 0% de nulos. Anomalia: Valores fora de domínio observados.

### `cd_agencia`
- **Tipo**: `string`
- **Nullable**: Não
- **Descrição**: Código numérico de 4 dígitos da agência de relacionamento principal.
- **Propósito de Negócio**: Identificação da agência responsável pelo cliente.
- **Comportamento Esperado**: Deve ser um código válido de 4 dígitos.
- **Estatísticas Observadas**: 473 valores únicos, 0% de nulos. Anomalia: Valores

---
> **[AI_METADATA_STATUS: DRAFT]**