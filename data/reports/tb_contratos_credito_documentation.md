# Dicionário Técnico da Tabela `tb_contratos_credito`

## Visão Geral

A tabela `tb_contratos_credito` contém informações sobre contratos de produtos de crédito ativos e encerrados. Ela é gerida pela equipe `squad-credito` e está em versão 3.0.0. A tabela é alimentada diariamente pelo sistema `SISTEMA_CREDITO_SAS` e utiliza o formato `sas7bdat` com codificação `latin-1`. O banco de dados está hospedado em um sistema operacional Unix.

### Contexto de Negócio

- **Propósito**: A tabela armazena dados sobre contratos de crédito de todos os produtos oferecidos pelo banco. Ela alimenta o SCR (Score de Crédito Rotativo) mensalmente.
- **Regras de Negócio**:
  - O valor utilizado (`vl_utilizado`) pode exceder o valor limite (`vl_limite`) em até 15% para produtos com tolerância de limite, como o cheque especial.
  - O status `EM_ATRASO` dispara uma cobrança automática após D+1.

### Classificação e Retenção de Dados

- **Classificação de Dados**: Restrita
- **Tags Regulatórias**: SCR, BACEN_4658, LGPD
- **Período de Retenção**: 10 anos

### Dependências

- A tabela depende de `tb_clientes` para referenciar clientes.

## Colunas

### `id_contrato`

- **Tipo**: String
- **Nullable**: Não
- **Descrição**: Identificador único do contrato gerado pelo sistema de crédito.
- **Comportamento Esperado**: Deve ser único para cada contrato.
- **Estatísticas**:
  - 0% de valores nulos
  - 300 valores únicos
- **Anomalias**: Nenhuma

### `cd_cliente`

- **Tipo**: String
- **Nullable**: Não
- **Descrição**: Referência ao cliente em `tb_clientes`.
- **Comportamento Esperado**: Deve corresponder a um cliente válido em `tb_clientes`.
- **Estatísticas**:
  - 0% de valores nulos
  - 213 valores únicos
- **Anomalias**: Alta frequência de valores repetidos (ex: 4 ocorrências para alguns clientes).

### `dt_contrato`

- **Tipo**: String (deveria ser Date)
- **Nullable**: Não
- **Descrição**: Data de abertura do contrato.
- **Comportamento Esperado**: Deve ser uma data válida no formato apropriado.
- **Estatísticas**:
  - 0% de valores nulos
  - 282 valores únicos
- **Anomalias**: Tipo de dado incorreto (VARCHAR em vez de Date).

### `vl_limite`

- **Tipo**: String (deveria ser Float)
- **Nullable**: Não
- **Descrição**: Limite de crédito aprovado em BRL.
- **Comportamento Esperado**: Deve ser um valor monetário positivo.
- **Estatísticas**:
  - 0% de valores nulos
  - 300 valores únicos
  - Mínimo: 1211.66
  - Máximo: 99891.53
  - Média: 51678.3628
- **Anomalias**: Tipo de dado incorreto (VARCHAR em vez de Float).

### `vl_utilizado`

- **Tipo**: String (deveria ser Float)
- **Nullable**: Não
- **Descrição**: Saldo utilizado atual em BRL. Pode exceder `vl_limite` em produtos com tolerância.
- **Comportamento Esperado**: Deve ser um valor monetário positivo.
- **Estatísticas**:
  - 0% de valores nulos
  - 300 valores únicos
  - Mínimo: 92.24
  - Máximo: 109174.48
  - Média: 30026.0736
- **Anomalias**: Tipo de dado incorreto (VARCHAR em vez de Float).

### `tp_produto`

- **Tipo**: String
- **Nullable**: Não
- **Descrição**: Tipo do produto de crédito. Domínio: `CARTAO_CREDITO`, `CHEQUE_ESPECIAL`, `CREDITO_PESSOAL`, `FINANCIAMENTO_VEICULO`, `CONSIGNADO`.
- **Comportamento Esperado**: Deve estar dentro do domínio especificado.
- **Estatísticas**:
  - 0% de valores nulos
  - 5 valores únicos
  - Topo: `CHEQUE_ESPECIAL` (70 ocorrências)
- **Anomalias**: Nenhuma

### `cd_status`

- **Tipo**: String
- **Nullable**: Não
- **Descrição**: Status do contrato. Domínio: `ATIVO`, `ENCERRADO`, `EM_ATRASO`, `RENEGOCIADO`.
- **Comportamento Esperado**: Deve estar dentro do domínio especificado.
- **Estatísticas**:
  - 0% de valores nulos
  - 4 valores únicos
  - Topo: `RENEGOCIADO` (96 ocorrências)
- **Anomalias**: Nenhuma

### `dt_vencimento`

- **Tipo**: String (deveria ser Date)
- **Nullable**: Não
- **Descrição**: Data de vencimento da última parcela ou do contrato.
- **Comportamento Esperado**: Deve ser uma data válida no formato apropriado.
- **Estatísticas**:
  - 0% de valores nulos
  - 281 valores únicos
- **Anomalias**: Tipo de dado incorreto (VARCHAR em vez de Date).

### `nr_parcelas`

- **Tipo**: String (deveria ser Integer)
- **Nullable**: Não
- **Descrição**: Número total de parcelas do contrato. 1 para crédito rotativo.
- **Comportamento Esperado**: Deve ser um número inteiro positivo.
- **Estatísticas**:
  - 0% de valores nulos
  - 60 valores únicos
  - Mínimo: 1.0
  - Máximo: 60.0
  - Média: 30.2033
- **Anomalias**: Tipo de dado incorreto (VARCHAR em vez de Integer).

### `tx_juros_am`

- **Tipo**: String (deveria ser Float)
- **Nullable**: Não
- **Descrição**: Taxa de juros mensal.
- **Comportamento Esperado**: Deve ser um valor percentual positivo.
- **Estatísticas**:
  - 0% de valores nulos
  - 300 valores únicos
  - Mínimo: 0.8133
  - Máximo: 8.4875
  - Média: 4.6799
- **Anomalias**: Tipo de dado incorreto (VARCHAR em vez de Float).

## Considerações Regulatórias

- **SCR**: A tabela é usada para alimentar o SCR, o que implica que os dados devem ser precisos e atualizados.
- **BACEN_4658**: A tabela deve estar em conformidade com as normas do Banco Central do Brasil.
- **LGPD**: A tabela contém dados pessoais restritos, exigindo medidas adequadas de proteção e privacidade.

## Pontos de Atenção

- **Tipos de Dados**: Múltiplas colunas têm tipos de dados incorretos (VARCHAR em vez de Date, Float, Integer).
- **Valores Repetidos**: Alta frequência de valores repetidos em `cd_cliente` e `cd_status`.
- **Compliance**: Garantir que a tabela esteja em conformidade com as normas regulatórias aplicáveis.

---

> **[AI_METADATA_STATUS: DRAFT]** — Documentação gerada por SLM. Requer validação humana pelo Data Steward responsável antes de uso em produção.