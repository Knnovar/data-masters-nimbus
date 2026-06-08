# Dicionário Técnico da Tabela `tb_contratos_credito_breaking`

## Visão Geral

A tabela `tb_contratos_credito_breaking` contém dados sobre contratos de produtos de crédito ativos e encerrados, conforme descrito no contrato YAML. Esses dados alimentam o Sistema de Controle de Risco (SCR) mensalmente e são geridos pela equipe de crédito do banco.

### Propósito de Negócio

A tabela serve para monitorar e analisar contratos de crédito oferecidos pelo banco, incluindo informações sobre limites aprovados, utilização atual, tipos de produtos, status dos contratos e outras métricas financeiras relevantes. Essas informações são cruciais para o gerenciamento de riscos e conformidade regulatória.

### Fonte de Dados

- **Sistema**: SISTEMA_CREDITO_SAS
- **Formato**: sas7bdat
- **Codificação**: latin-1
- **SO**: unix
- **Frequência de Atualização**: diária

### Responsáveis

- **Proprietário**: squad-credito
- **Data Steward**: Data Steward Credito (steward-credito@banco.com.br)

## Colunas da Tabela

### `id_contrato`

- **Tipo**: string
- **Nullable**: false
- **Descrição**: Identificador único do contrato gerado pelo sistema de crédito.
- **Comportamento Esperado**: Deve ser exclusivo para cada registro (não duplicados).
- **Anomalias Observadas**: Nenhuma anomalia detectada; 100% dos valores são únicos.

### `cd_cliente`

- **Tipo**: string
- **Nullable**: false
- **Descrição**: Referência ao cliente em `tb_clientes`.
- **Comportamento Esperado**: Deve corresponder a um identificador válido de cliente.
- **Anomalias Observadas**: 221 valores únicos entre 300 registros, indicando clientes com múltiplos contratos.

### `dt_contrato`

- **Tipo**: string (esperado date)
- **Nullable**: false
- **Descrição**: Data de abertura do contrato.
- **Comportamento Esperado**: Deve ser uma data válida no formato apropriado.
- **Anomalias Observadas**: Tipo de dado está como `VARCHAR`, o que pode indicar problemas na conversão ou formatação.

### `vl_limite`

- **Tipo**: string (esperado float)
- **Nullable**: false
- **Descrição**: Limite de crédito aprovado em BRL.
- **Comportamento Esperado**: Deve ser um valor numérico positivo.
- **Anomalias Observadas**: Tipo de dado está como `VARCHAR`, o que pode indicar problemas na conversão ou formatação.

### `vl_utilizado`

- **Tipo**: string (esperado float)
- **Nullable**: false
- **Descrição**: Saldo utilizado atual em BRL. Pode exceder `vl_limite` em produtos com tolerância.
- **Comportamento Esperado**: Deve ser um valor numérico positivo, podendo exceder o limite para certos produtos.
- **Anomalias Observadas**: Tipo de dado está como `VARCHAR`, o que pode indicar problemas na conversão ou formatação.

### `tp_produto`

- **Tipo**: string
- **Nullable**: false
- **Descrição**: Tipo do produto de crédito. Domínio: CARTAO_CREDITO, CHEQUE_ESPECIAL, CREDITO_PESSOAL, FINANCIAMENTO_VEICULO, CONSIGNADO.
- **

---
> **[AI_METADATA_STATUS: DRAFT]**