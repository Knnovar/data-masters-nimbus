# Dicionário Técnico da Tabela `tb_contratos_credito`

## Visão Geral

A tabela `tb_contratos_credito` contém informações sobre contratos de produtos de crédito ativos e encerrados. Ela é gerida pela equipe `squad-credito` e é alimentada diariamente pelo sistema `SISTEMA_CREDITO_SAS`. A tabela é classificada como restrita e deve ser mantida por 10 anos, conforme as regulamentações do BACEN e LGPD.

## Colunas

### `id_contrato`
- **Tipo**: `string`
- **Nullable**: Não
- **Descrição**: Identificador único do contrato gerado pelo sistema de crédito.
- **Comportamento Esperado**: Cada contrato deve ter um `id_contrato` único. Não há valores nulos e não há duplicatas.
- **Anomalias**: Nenhuma observada.

### `cd_cliente`
- **Tipo**: `string`
- **Nullable**: Não
- **Descrição**: Referência ao cliente em `tb_clientes`.
- **Comportamento Esperado**: Cada contrato deve ter um `cd_cliente` válido. Não há valores nulos.
- **Anomalias**: Alta frequência de valores repetidos, indicando múltiplos contratos para alguns clientes.

### `dt_contrato`
- **Tipo**: `string` (deveria ser `date`)
- **Nullable**: Não
- **Descrição**: Data de abertura do contrato.
- **Comportamento Esperado**: Deve conter datas válidas de abertura dos contratos. Não há valores nulos.
- **Anomalias**: Tipo de dado incorreto (`VARCHAR` em vez de `date`). Datas futuras observadas, o que pode indicar erros de entrada de dados.

### `vl_limite`
- **Tipo**: `string` (deveria ser `float`)
- **Nullable**: Não
- **Descrição**: Limite de crédito aprovado em BRL.
- **Comportamento Esperado**: Deve conter valores monetários válidos. Não há valores nulos.
- **Anomalias**: Tipo de dado incorreto (`VARCHAR` em vez de `float`). Valores fora de faixa observados, o que pode indicar erros de entrada de dados.

### `vl_utilizado`
- **Tipo**: `string` (deveria ser `float`)
- **Nullable**: Não
- **Descrição**: Saldo utilizado atual em BRL. Pode exceder `vl_limite` em produtos com tolerância.
- **Comportamento Esperado**: Deve conter valores monetários válidos. Não há valores nulos.
- **Anomalias**: Tipo de dado incorreto (`VARCHAR` em vez de `float`). Valores fora de faixa observados, o que pode indicar erros de entrada de dados.

### `tp_produto`
- **Tipo**: `string`
- **Nullable**: Não
- **Descrição**: Tipo do produto de crédito. Dominio: `CARTAO_CREDITO`, `CHEQUE_ESPECIAL`, `CREDITO_PESSOAL`, `FINANCIAMENTO_VEICULO`, `CONSIGNADO`.
- **Comportamento Esperado**: Deve conter apenas valores do domínio especificado. Não há valores nulos.
- **Anomalias**: Nenhuma observada.

### `cd_status`
- **Tipo**: `string`
- **Nullable**: Não
- **Descrição**: Status do contrato. Dominio: `ATIVO`, `ENCERRADO`, `EM_ATRASO`, `RENEGOCIADO`.
- **Comportamento Esperado**: Deve conter apenas valores do domínio especificado. Não há valores nulos.
- **Anomalias**: Nenhuma observada.

### `dt_vencimento`
- **Tipo**: `string` (deveria ser `date`)
- **Nullable**: Não
- **Descrição**: Data de vencimento da última parcela ou do contrato.
- **Comportamento Esperado**: Deve conter datas válidas de vencimento. Não há valores nulos.
- **Anomalias**: Tipo de dado incorreto (`VARCHAR` em vez de `date`). Datas futuras observadas, o que pode indicar erros de entrada de dados.

### `nr_parcelas`
- **Tipo**: `string` (deveria ser `integer`)
- **Nullable**: Não
- **Descrição**: Número total de parcelas do contrato. 1 para crédito rotativo.
- **Comportamento Esperado**: Deve conter valores inteiros válidos. Não há valores nulos.
- **Anomalias**: Tipo de dado incorreto (`VARCHAR` em vez de `integer`).

### `tx_juros_am`
- **Tipo**: `string` (deveria ser `float`)
- **Nullable**: Não
- **Descrição**: Taxa de juros ao mês em percentual.
- **Comportamento Esperado**: Deve conter valores percentuais válidos. Não há valores nulos.
- **Anomalias**: Tipo de dado incorreto (`VARCHAR` em vez de `float`).

## Implicações de Compliance

- **SCR**: A tabela alimenta o SCR mensalmente, sendo candidata a informações relevantes para o SCR.
- **BACEN_4658**: A tabela deve estar em conformidade com as normas do Banco Central.
- **LGPD**: A tabela é classificada como restrita, exigindo medidas de proteção de dados pessoais.

## Pontos de Atenção

1. **Tipos de Dados**: Muitos campos estão incorretamente definidos como `VARCHAR` em vez de seus tipos esperados (`date`, `float`, `integer`). Isso pode afetar a integridade dos dados e a execução de consultas.
2. **Valores Fora de Faixa**: Observados em `vl_limite` e `vl_utilizado`, indicando potenciais erros de entrada de dados.
3. **Duplicatas de Clientes**: Alta frequência de `cd_cliente` repetidos pode indicar múltiplos contratos para alguns clientes, o que deve ser investigado.
4. **Datas Futuras**: Observadas em `dt_contrato` e `dt_vencimento`, o que pode indicar erros de entrada de dados.
5. **Regulamentações**: A tabela deve ser gerida em conformidade com as normas do BACEN e LGPD, considerando sua classificação como restrita.

---

> **[AI_METADATA_STATUS: DRAFT]** — Documentação gerada por SLM. Requer validação humana pelo Data Steward responsável antes de uso em produção.