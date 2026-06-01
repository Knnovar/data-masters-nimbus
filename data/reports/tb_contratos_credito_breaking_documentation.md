# Dicionário Técnico da Tabela `tb_contratos_credito_breaking`

## Visão Geral

A tabela `tb_contratos_credito_breaking` contém informações sobre contratos de produtos de crédito ativos e encerrados, conforme descrito no contrato YAML. Ela alimenta o SCR (Score de Crédito) mensalmente e é gerida pela equipe `squad-credito`. A tabela está em formato SAS7BDAT com codificação Latin-1 e atualiza-se diariamente.

### Contexto de Negócio

Os contratos de crédito incluem todos os produtos oferecidos pelo banco. O valor utilizado (`vl_utilizado`) pode exceder o valor limite (`vl_limite`) em até 15% para produtos com tolerância, como o cheque especial. Um status de contrato `EM_ATRASO` desencadeia cobrança automática após D+1.

### Implicações Regulatórias

- **Tags Regulatórias**: SCR, BACEN_4658, LGPD.
- **Classificação de Dados**: Restrita.
- **Período de Retenção**: 10 anos.

## Esquema da Tabela

| Nome da Coluna     | Tipo       | Nullable | Descrição                                                                                       |
|--------------------|------------|----------|-------------------------------------------------------------------------------------------------|
| `id_contrato`      | string     | Não      | Identificador único do contrato gerado pelo sistema de crédito.                                  |
| `cd_cliente`       | string     | Não      | Referência ao cliente em `tb_clientes`.                                                          |
| `dt_contrato`      | date       | Não      | Data de abertura do contrato.                                                                    |
| `vl_limite`        | float      | Não      | Limite de crédito aprovado em BRL.                                                               |
| `vl_utilizado`     | float      | Não      | Saldo utilizado atual em BRL. Pode exceder `vl_limite` em produtos com tolerância.                |
| `tp_produto`       | string     | Não      | Tipo do produto de crédito: CARTAO_CREDITO, CHEQUE_ESPECIAL, CREDITO_PESSOAL, FINANCIAMENTO_VEICULO, CONSIGNADO. |
| `cd_status`        | string     | Não      | Status do contrato: ATIVO, ENCERRADO, EM_ATRASO, RENEGOCIADO.                                     |
| `dt_vencimento`    | date       | Não      | Data de vencimento da última parcela ou do contrato.                                             |
| `nr_parcelas`      | integer    | Não      | Número total de parcelas do contrato. 1 para crédito rotativo.                                    |
| `tx_juros_am`      | float      | Não      | Taxa de juros ao mês em percentual (ex: 2.5 = 2,5% a.m.).                                        |

## Análise das Estatísticas

### `id_contrato`
- **Tipo**: VARCHAR
- **Null Pct**: 0%
- **Únicos**: 300
- **Observação**: Cada contrato possui um identificador único conforme esperado.

### `cd_cliente`
- **Tipo**: VARCHAR
- **Null Pct**: 0%
- **Únicos**: 221
- **Observação**: Existem duplicatas nos códigos de clientes, indicando múltiplos contratos por cliente. Isso não é um problema se os dados forem corretos.

### `dt_contrato`
- **Tipo**: VARCHAR (Deveria ser DATE)
- **Null Pct**: 0%
- **Únicos**: 282
- **Observação**: A

---
> **[AI_METADATA_STATUS: DRAFT]**