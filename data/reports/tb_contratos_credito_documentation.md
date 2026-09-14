# Dicionário Técnico da Tabela `tb_contratos_credito`

## Visão Geral

A tabela `tb_contratos_credito` contém informações sobre contratos de produtos de crédito ativos e encerrados. Ela alimenta o Sistema de Controle de Risco (SCR) mensalmente e é gerida pela equipe `squad-credito`. A tabela está em formato `sas7bdat` e é atualizada diariamente pelo sistema `SISTEMA_CREDITO_SAS`.

### Contexto de Negócio

Os contratos de crédito incluem todos os produtos oferecidos pelo banco. O valor utilizado (`vl_utilizado`) pode exceder o valor limite (`vl_limite`) em até 15% para produtos com tolerância de limite, como o cheque especial. O status `EM_ATRASO` dispara uma cobrança automática após D+1.

### Regulamentação

A tabela está sujeita a regulamentações como o SCR, BACEN 4658 e LGPD, com classificação de dados restrita e retenção por 10 anos.

## Colunas

### `id_contrato`
- **Tipo**: `string`
- **Nullable**: Não
- **Descrição**: Identificador único do contrato gerado pelo sistema de crédito.
- **Estatísticas**: 0% de valores nulos, 300 valores únicos.
- **Observações**: Atende ao requisito de chave primária.

### `cd_cliente`
- **Tipo**: `string`
- **Nullable**: Não
- **Descrição**: Referência ao cliente em `tb_clientes`.
- **Estatísticas**: 0% de valores nulos, 213 valores únicos.
- **Observações**: Alta frequência de valores repetidos, indicando múltiplos contratos por cliente.

### `dt_contrato`
- **Tipo**: `string` (esperado `date`)
- **Nullable**: Não
- **Descrição**: Data de abertura do contrato.
- **Estatísticas**: 0% de valores nulos, 282 valores únicos.
- **Observações**: Tipo de dado esperado é `date`, mas está como `string`. Requer correção.

### `vl_limite`
- **Tipo**: `string` (esperado `float`)
- **Nullable**: Não
- **Descrição**: Limite de crédito aprovado em BRL.
- **Estatísticas**: 0% de valores nulos, valores entre 1211.66 e 99891.53.
- **Observações**: Tipo de dado esperado é `float`, mas está como `string`. Requer correção.

### `vl_utilizado`
- **Tipo**: `string` (esperado `float`)
- **Nullable**: Não
- **Descrição**: Saldo utilizado atual em BRL. Pode exceder `vl_limite` em produtos com tolerância.
- **Estatísticas**: 0% de valores nulos, valores entre 92.24 e 109174.48.
- **Observações**: Tipo de dado esperado é `float`, mas está como `string`. Requer correção.

### `tp_produto`
- **Tipo**: `string`
- **Nullable**: Não
- **Descrição**: Tipo do produto de crédito. Domínio: `CARTAO_CREDITO`, `CHEQUE_ESPECIAL`, `CREDITO_PESSOAL`, `FINANCIAMENTO_VEICULO`, `CONSIGNADO`.
- **Estatísticas**: 0% de valores nulos, 5 valores únicos.
- **Observações**: `CHEQUE_ESPECIAL` é o tipo mais comum.

### `cd_status`
- **Tipo**: `string`
- **Nullable**: Não
- **Descrição**: Status do contrato. Domínio: `ATIVO`, `ENCERRADO`, `EM_ATRASO`, `RENEGOCIADO`.
- **Estatísticas**: 0% de valores nulos, 4 valores únicos.
- **Observações**: `RENEGOCIADO` e `EM_ATRASO` são os status mais comuns.

### `dt_vencimento`
- **Tipo**: `string` (esperado `date`)
- **Nullable**: Não
- **Descrição**: Data de vencimento da última parcela ou do contrato.
- **Estatísticas**: 0% de valores nulos, 281 valores únicos.
- **Observações**: Tipo de dado esperado é `date`, mas está como `string`. Requer correção.

### `nr_parcelas`
- **Tipo**: `string` (esperado `integer`)
- **Nullable**: Não
- **Descrição**: Número total de parcelas do contrato. 1 para crédito rotativo.
- **Estatísticas**: 0% de valores nulos, valores entre 1 e 60.
- **Observações**: Tipo de dado esperado é `integer`, mas está como `string`. Requer correção.

### `tx_juros_am`
- **Tipo**: `string` (esperado `float`)
- **Nullable**: Não
- **Descrição**: Taxa de juros ao mês em percentual. Ex: 2.5 = 2,5% a.m.
- **Estatísticas**: 0% de valores nulos, valores entre 0.8133 e 8.4875.
- **Observações**: Tipo de dado esperado é `float`, mas está como `string`. Requer correção.

## Anomalias e Implicações de Compliance

- **Tipos de Dados**: Múltiplas colunas (`dt_contrato`, `vl_limite`, `vl_utilizado`, `dt_vencimento`, `nr_parcelas`, `tx_juros_am`) estão como `string` em vez dos tipos esperados (`date`, `float`, `integer`). Isso pode afetar a precisão dos cálculos e a integridade dos dados.
- **Regulamentação**: As colunas `vl_limite` e `vl_utilizado` são candidatas ao SCR, exigindo monitoramento rigoroso para garantir conformidade com os limites de crédito.
- **Duplicatas**: A coluna `cd_cliente` apresenta duplicatas, indicando múltiplos contratos por cliente, o que é esperado, mas deve ser monitorado para evitar inconsistências.

## Pontos de Atenção

1. **Correção de Tipos de Dados**: É crucial corrigir os tipos de dados das colunas `dt_contrato`, `vl_limite`, `vl_utilizado`, `dt_vencimento`, `nr_parcelas` e `tx_juros_am` para os tipos esperados.
2. **Monitoramento de Duplicatas**: Embora duplicatas em `cd_cliente` sejam esperadas, é importante garantir que não haja inconsistências nos dados dos clientes.
3. **Conformidade Regulamentar**: As colunas `vl_limite` e `vl_utilizado` devem ser monitoradas continuamente para garantir conformidade com os regulamentos do SCR.
4. **Validação de Dados**: Implementar validações para garantir que os valores de `vl_utilizado` não excedam os limites permitidos para produtos com tolerância de limite.

---

> **[AI_METADATA_STATUS: DRAFT]** — Documentação gerada por SLM. Requer validação humana pelo Data Steward responsável antes de uso em produção.