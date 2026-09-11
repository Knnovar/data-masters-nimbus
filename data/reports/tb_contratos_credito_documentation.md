# Dicionário Técnico da Tabela `tb_contratos_credito`

## Visão Geral

A tabela `tb_contratos_credito` contém informações sobre contratos de produtos de crédito ativos e encerrados. Ela é gerida pela equipe de crédito do banco e alimenta o Sistema de Controle de Risco (SCR) mensalmente. A tabela é atualizada diariamente e é classificada como restrita, com uma retenção de dados de 10 anos. Ela está sujeita a regulamentações como o SCR, a BACEN 4658 e a LGPD.

## Colunas

### `id_contrato`
- **Tipo**: `string`
- **Nullable**: Não
- **Descrição**: Identificador único do contrato gerado pelo sistema de crédito.
- **Comportamento Esperado**: Cada contrato deve ter um ID único. Nenhuma anomalia foi observada, pois o percentual de nulos é 0% e o número de valores únicos é igual ao número total de linhas (300).
- **SAS Label**: ID CONTRATO CREDITO

### `cd_cliente`
- **Tipo**: `string`
- **Nullable**: Não
- **Descrição**: Referência ao cliente em `tb_clientes`.
- **Comportamento Esperado**: Cada contrato deve estar associado a um cliente. O percentual de nulos é 0%, mas há duplicatas, com 213 valores únicos em 300 registros.
- **SAS Label**: CODIGO CLIENTE

### `dt_contrato`
- **Tipo**: `string` (deveria ser `date`)
- **Nullable**: Não
- **Descrição**: Data de abertura do contrato.
- **Comportamento Esperado**: Deve ser uma data válida. O percentual de nulos é 0%, mas o tipo de dado é `VARCHAR`, indicando uma possível anomalia de formatação.
- **SAS Label**: DATA ABERTURA CONTRATO

### `vl_limite`
- **Tipo**: `string` (deveria ser `float`)
- **Nullable**: Não
- **Descrição**: Limite de crédito aprovado em BRL.
- **Comportamento Esperado**: Deve ser um valor numérico positivo. O percentual de nulos é 0%, mas o tipo de dado é `VARCHAR`, indicando uma possível anomalia de formatação.
- **Regulatory Flags**: SCR_CANDIDATE

### `vl_utilizado`
- **Tipo**: `string` (deveria ser `float`)
- **Nullable**: Não
- **Descrição**: Saldo utilizado atual em BRL. Pode exceder `vl_limite` em produtos com tolerância.
- **Comportamento Esperado**: Deve ser um valor numérico positivo. O percentual de nulos é 0%, mas o tipo de dado é `VARCHAR`, indicando uma possível anomalia de formatação.
- **Regulatory Flags**: SCR_CANDIDATE
- **Business Rules**: Pode ser até 15% acima de `vl_limite` para `CHEQUE_ESPECIAL`.

### `tp_produto`
- **Tipo**: `string`
- **Nullable**: Não
- **Descrição**: Tipo do produto de crédito. Domínio: `CARTAO_CREDITO`, `CHEQUE_ESPECIAL`, `CREDITO_PESSOAL`, `FINANCIAMENTO_VEICULO`, `CONSIGNADO`.
- **Comportamento Esperado**: Deve estar dentro do domínio especificado. O percentual de nulos é 0% e há 5 valores únicos, indicando conformidade com o domínio.

### `cd_status`
- **Tipo**: `string`
- **Nullable**: Não
- **Descrição**: Status do contrato. Domínio: `ATIVO`, `ENCERRADO`, `EM_ATRASO`, `RENEGOCIADO`.
- **Comportamento Esperado**: Deve estar dentro do domínio especificado. O percentual de nulos é 0% e há 4 valores únicos, indicando conformidade com o domínio.
- **Business Rules**: `EM_ATRASO` dispara cobrança automática após D+1.

### `dt_vencimento`
- **Tipo**: `string` (deveria ser `date`)
- **Nullable**: Não
- **Descrição**: Data de vencimento da última parcela ou do contrato.
- **Comportamento Esperado**: Deve ser uma data válida. O percentual de nulos é 0%, mas o tipo de dado é `VARCHAR`, indicando uma possível anomalia de formatação.

### `nr_parcelas`
- **Tipo**: `string` (deveria ser `integer`)
- **Nullable**: Não
- **Descrição**: Número total de parcelas do contrato. 1 para crédito rotativo.
- **Comportamento Esperado**: Deve ser um número inteiro positivo. O percentual de nulos é 0%, mas o tipo de dado é `VARCHAR`, indicando uma possível anomalia de formatação.

### `tx_juros_am`
- **Tipo**: `string` (deveria ser `float`)
- **Nullable**: Não
- **Descrição**: Taxa de juros ao mês em percentual. Ex: 2.5 = 2,5% a.m.
- **Comportamento Esperado**: Deve ser um valor numérico positivo. O percentual de nulos é 0%, mas o tipo de dado é `VARCHAR`, indicando uma possível anomalia de formatação.
- **SAS Label**: TAXA JUROS MENSAL

## Regulamentações e Compliance

- **Regulatory Tags**: SCR, BACEN 4658, LGPD
- **Implicações de Compliance**: A tabela é classificada como restrita e deve ser gerida conforme as regulamentações mencionadas. A presença de `SCR_CANDIDATE` em `vl_limite` e `vl_utilizado` indica que esses campos são relevantes para o cálculo de risco.

## Pontos de Atenção

1. **Anomalias de Formatação**: Muitos campos (`dt_contrato`, `vl_limite`, `vl_utilizado`, `dt_vencimento`, `nr_parcelas`, `tx_juros_am`) estão armazenados como `VARCHAR` em vez de tipos numéricos ou de data, indicando uma possível anomalia de formatação que deve ser corrigida.
2. **Duplicatas em `cd_cliente`**: Há duplicatas nos valores de `cd_cliente`, o que pode indicar contratos associados ao mesmo cliente.
3. **Conformidade com Domínio**: Verificar se todos os valores de `tp_produto` e `cd_status` estão dentro dos domínios especificados.
4. **Validação de Dados**: Garantir que `vl_utilizado` não exceda `vl_limite` além do limite permitido para `CHEQUE_ESPECIAL`.

---

> **[AI_METADATA_STATUS: DRAFT]** — Documentação gerada por SLM. Requer validação humana pelo Data Steward responsável antes de uso em produção.