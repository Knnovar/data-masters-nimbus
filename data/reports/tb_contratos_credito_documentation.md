# Dicionário Técnico: `tb_contratos_credito`

## Visão Geral
A tabela `tb_contratos_credito` armazena informações sobre contratos de produtos de crédito ativos e encerrados. Ela é gerida pela equipe `squad-credito` e é alimentada diariamente pelo sistema `SISTEMA_CREDITO_SAS`. A tabela é crucial para o cumprimento do SCR (Serviço de Proteção ao Crédito) e está sujeita a regulamentações como a LGPD (Lei Geral de Proteção de Dados) e a BACEN 4658.

## Colunas

### `id_contrato`
- **Tipo**: `string`
- **Nullable**: Não
- **Descrição**: Identificador único do contrato gerado pelo sistema de crédito.
- **Comportamento Esperado**: Cada contrato deve ter um ID único.
- **Estatísticas**:
  - 0% de valores nulos
  - 300 valores únicos
- **Anomalias**: Nenhuma

### `cd_cliente`
- **Tipo**: `string`
- **Nullable**: Não
- **Descrição**: Referência ao cliente em `tb_clientes`.
- **Comportamento Esperado**: Deve corresponder a um cliente válido na tabela `tb_clientes`.
- **Estatísticas**:
  - 0% de valores nulos
  - 213 valores únicos
- **Anomalias**: Alta frequência de valores repetidos, indicando múltiplos contratos por cliente.

### `dt_contrato`
- **Tipo**: `string` (esperado `date`)
- **Nullable**: Não
- **Descrição**: Data de abertura do contrato.
- **Comportamento Esperado**: Deve ser uma data válida no formato `YYYY-MM-DD`.
- **Estatísticas**:
  - 0% de valores nulos
  - 284 valores únicos
- **Anomalias**: Tipo de dado `VARCHAR` em vez de `date`, o que pode causar problemas de validação e comparação.

### `vl_limite`
- **Tipo**: `string` (esperado `float`)
- **Nullable**: Não
- **Descrição**: Limite de crédito aprovado em BRL.
- **Comportamento Esperado**: Deve ser um valor numérico positivo.
- **Estatísticas**:
  - 0% de valores nulos
  - 300 valores únicos
  - Mínimo: 1211.66
  - Máximo: 99891.53
  - Média: 51460.0778
- **Anomalias**: Tipo de dado `VARCHAR` em vez de `float`, o que pode causar problemas de cálculo.

### `vl_utilizado`
- **Tipo**: `string` (esperado `float`)
- **Nullable**: Não
- **Descrição**: Saldo utilizado atual em BRL. Pode exceder `vl_limite` em produtos com tolerância.
- **Comportamento Esperado**: Deve ser um valor numérico positivo, podendo exceder `vl_limite` em até 15% para produtos como cheque especial.
- **Estatísticas**:
  - 0% de valores nulos
  - 300 valores únicos
  - Mínimo: 92.24
  - Máximo: 109174.48
  - Média: 30068.852
- **Anomalias**: Tipo de dado `VARCHAR` em vez de `float`, o que pode causar problemas de cálculo.

### `tp_produto`
- **Tipo**: `string`
- **Nullable**: Não
- **Descrição**: Tipo do produto de crédito. Domínio: `CARTAO_CREDITO`, `CHEQUE_ESPECIAL`, `CREDITO_PESSOAL`, `FINANCIAMENTO_VEICULO`, `CONSIGNADO`.
- **Comportamento Esperado**: Deve corresponder a um dos valores do domínio especificado.
- **Estatísticas**:
  - 0% de valores nulos
  - 5 valores únicos
  - Maior frequência: `CHEQUE_ESPECIAL` (71)
- **Anomalias**: Nenhuma

### `cd_status`
- **Tipo**: `string`
- **Nullable**: Não
- **Descrição**: Status do contrato. Domínio: `ATIVO`, `ENCERRADO`, `EM_ATRASO`, `RENEGOCIADO`.
- **Comportamento Esperado**: Deve corresponder a um dos valores do domínio especificado. `EM_ATRASO` dispara cobrança automática após D+1.
- **Estatísticas**:
  - 0% de valores nulos
  - 4 valores únicos
  - Maior frequência: `RENEGOCIADO` (92)
- **Anomalias**: Nenhuma

### `dt_vencimento`
- **Tipo**: `string` (esperado `date`)
- **Nullable**: Não
- **Descrição**: Data de vencimento da última parcela ou do contrato.
- **Comportamento Esperado**: Deve ser uma data válida no formato `YYYY-MM-DD`.
- **Estatísticas**:
  - 0% de valores nulos
  - 279 valores únicos
- **Anomalias**: Tipo de dado `VARCHAR` em vez de `date`, o que pode causar problemas de validação e comparação.

### `nr_parcelas`
- **Tipo**: `string` (esperado `integer`)
- **Nullable**: Não
- **Descrição**: Número total de parcelas do contrato. 1 para crédito rotativo.
- **Comportamento Esperado**: Deve ser um número inteiro positivo.
- **Estatísticas**:
  - 0% de valores nulos
  - 60 valores únicos
  - Mínimo: 1.0
  - Máximo: 60.0
  - Média: 30.2033
- **Anomalias**: Tipo de dado `VARCHAR` em vez de `integer`, o que pode causar problemas de cálculo.

### `tx_juros_am`
- **Tipo**: `string` (esperado `float`)
- **Nullable**: Não
- **Descrição**: Taxa de juros ao mês em percentual. Ex: 2.5 = 2.5%.
- **Comportamento Esperado**: Deve ser um valor numérico positivo.
- **Estatísticas**:
  - 0% de valores nulos
  - 300 valores únicos
  - Mínimo: 0.8133
  - Máximo: 8.4875
  - Média: 4.6433
- **Anomalias**: Tipo de dado `VARCHAR` em vez de `float`, o que pode causar problemas de cálculo.

## Regulamentações e Considerações
- **SCR**: A tabela é usada para alimentar o Serviço de Proteção ao Crédito.
- **LGPD**: A tabela contém dados pessoais e deve ser gerida conforme a Lei Geral de Proteção de Dados.
- **BACEN 4658**: A tabela deve estar em conformidade com a regulamentação do Banco Central.

## Anomalias e Ações Recomendadas
- **Tipos de Dados**: Muitas colunas estão armazenadas como `VARCHAR` em vez dos tipos esperados (`date`, `float`, `integer`). Isso pode causar problemas de validação, comparação e cálculo. Recomenda-se converter essas colunas para os tipos corretos.
- **Frequência de Valores**: Alta frequência de valores repetidos em `cd_cliente` e `cd_status` pode indicar padrões que devem ser investigados para garantir a integridade dos dados.

---
> **[AI_METADATA_STATUS: DRAFT]** — Documentação gerada por SLM. Requer validação humana pelo Data Steward responsável antes de uso em produção.