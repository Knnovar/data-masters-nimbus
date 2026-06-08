# Dicionário Técnico da Tabela `tb_contratos_credito_non_breaking`

## Visão Geral

A tabela `tb_contratos_credito_non_breaking` contém informações detalhadas sobre contratos de produtos de crédito ativos e encerrados. Ela é alimentada diariamente pelo sistema SISTEMA_CREDITO_SAS em formato SAS7BDAT, com codificação Latin-1 no ambiente Unix. Esta tabela suporta o Sistema de Controle de Risco (SCR) mensalmente e está sob a classificação de dados restrita, com uma retenção obrigatória de 10 anos conforme regulamentações como BACEN_4658 e LGPD.

### Propósito de Negócio

A tabela serve para gerenciar e monitorar contratos de crédito oferecidos pelo banco. Ela é crucial para a análise do risco, conformidade regulatória e gestão de produtos financeiros. A tabela também suporta operações como cobrança automática em caso de atraso nos pagamentos.

### Estrutura da Tabela

Abaixo está uma descrição detalhada das colunas presentes na tabela:

#### `id_contrato`
- **Tipo**: string
- **Nullable**: false
- **Descrição**: Identificador único do contrato gerado pelo sistema de crédito.
- **Comportamento Esperado**: Cada valor deve ser exclusivo, conforme confirmado pelas estatísticas (unique_count = 300).
- **Anomalias Observadas**: Nenhuma.

#### `cd_cliente`
- **Tipo**: string
- **Nullable**: false
- **Descrição**: Referência ao cliente em `tb_clientes`.
- **Comportamento Esperado**: Cada contrato deve referenciar um cliente válido.
- **Anomalias Observadas**: Alta frequência de valores repetidos (top 3 valores com contagem = 4), indicando possíveis duplicatas ou contratos múltiplos para o mesmo cliente.

#### `dt_contrato`
- **Tipo**: string
- **Nullable**: false
- **Descrição**: Data de abertura do contrato.
- **Comportamento Esperado**: Deve ser um valor de data válido e formatado corretamente.
- **Anomalias Observadas**: Tipo de dado é VARCHAR, o que pode indicar inconsistências no formato da data.

#### `vl_limite`
- **Tipo**: string
- **Nullable**: false
- **Descrição**: Limite de crédito aprovado em BRL. Candidato para SCR.
- **Comportamento Esperado**: Deve ser um valor numérico positivo.
- **Anomalias Observadas**: Tipo de dado é VARCHAR, o que pode indicar inconsistências na representação do valor monetário.

#### `vl_utilizado`
- **Tipo**: string
- **Nullable**: false
- **Descrição**: Saldo utilizado atual em BRL. Pode exceder `vl_limite` em produtos com tolerância.
- **Comportamento Esperado**: Deve ser um valor numérico positivo, podendo exceder o limite para certos produtos como cheque especial.
- **Anomalias Observadas**: Tipo de dado é VARCHAR, o que pode indicar inconsistências na representação do valor monetário.

#### `tp_produto`
- **Tipo**: string
- **Nullable**: false
- **Descrição**: Tipo do produto de crédito. Domínio: CARTAO_CREDITO, CHEQUE_ESPECIAL, CREDITO_PESSOAL, FINANCIAMENTO_VEICULO, CONSIGNADO.
- **Comportamento Esperado**: Deve conter apenas valores dentro do domínio especificado.
- **Anomalias

---
> **[AI_METADATA_STATUS: DRAFT]**