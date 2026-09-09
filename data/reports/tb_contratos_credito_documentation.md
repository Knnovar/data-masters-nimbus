# Dicionário Técnico: tb_contratos_credito

## Visão Geral
A tabela `tb_contratos_credito` contém informações sobre contratos de produtos de crédito ativos e encerrados. Ela alimenta o Sistema de Controle de Risco (SCR) mensalmente e é gerida pela equipe `squad-credito`. Os dados são extraídos do sistema `SISTEMA_CREDITO_SAS` em formato `sas7bdat`, com codificação `latin-1`, e são atualizados diariamente.

### Contexto de Negócio
Os contratos de crédito incluem todos os produtos oferecidos pelo banco. O valor utilizado (`vl_utilizado`) pode exceder o valor limite (`vl_limite`) em até 15% para produtos com tolerância de limite, como o cheque especial. O status `EM_ATRASO` dispara uma cobrança automática após D+1.

### Regulamentação
A tabela está classificada como restrita, com tags regulatórias incluindo SCR, BACEN_4658 e LGPD. Os dados devem ser retidos por 10 anos.

## Colunas

### id_contrato
- **Tipo**: String
- **Descrição**: Identificador único do contrato gerado pelo sistema de crédito.
- **Comportamento Esperado**: Não nulo, chave primária, 300 valores únicos.
- **Anomalias**: Nenhuma.

### cd_cliente
- **Tipo**: String
- **Descrição**: Referência ao cliente em `tb_clientes`.
- **Comportamento Esperado**: Não nulo, 213 valores únicos.
- **Anomalias**: Alta duplicação de valores (ex.: 4 ocorrências para "C931F2C4-5E0").

### dt_contrato
- **Tipo**: String (esperado Date)
- **Descrição**: Data de abertura do contrato.
- **Comportamento Esperado**: Não nulo, 284 valores únicos.
- **Anomalias**: Tipo de dado esperado é `date`, mas está como `VARCHAR`.

### vl_limite
- **Tipo**: String (esperado Float)
- **Descrição**: Limite de crédito aprovado em BRL.
- **Comportamento Esperado**: Não nulo, 300 valores únicos.
- **Anomalias**: Tipo de dado esperado é `float`, mas está como `VARCHAR`.

### vl_utilizado
- **Tipo**: String (esperado Float)
- **Descrição**: Saldo utilizado atual em BRL. Pode exceder `vl_limite` em produtos com tolerância.
- **Comportamento Esperado**: Não nulo, 300 valores únicos.
- **Anomalias**: Tipo de dado esperado é `float`, mas está como `VARCHAR`.

### tp_produto
- **Tipo**: String
- **Descrição**: Tipo do produto de crédito. Domínio: CARTAO_CREDITO, CHEQUE_ESPECIAL, CREDITO_PESSOAL, FINANCIAMENTO_VEICULO, CONSIGNADO.
- **Comportamento Esperado**: Não nulo, 5 valores únicos.
- **Anomalias**: Nenhuma.

### cd_status
- **Tipo**: String
- **Descrição**: Status do contrato. Domínio: ATIVO, ENCERRADO, EM_ATRASO, RENEGOCIADO.
- **Comportamento Esperado**: Não nulo, 4 valores únicos.
- **Anomalias**: Nenhuma.

### dt_vencimento
- **Tipo**: String (esperado Date)
- **Descrição**: Data de vencimento da última parcela ou do contrato.
- **Comportamento Esperado**: Não nulo, 279 valores únicos.
- **Anomalias**: Tipo de dado esperado é `date`, mas está como `VARCHAR`.

### nr_parcelas
- **Tipo**: String (esperado Integer)
- **Descrição**: Número total de parcelas do contrato. 1 para crédito rotativo.
- **Comportamento Esperado**: Não nulo, 60 valores únicos.
- **Anomalias**: Tipo de dado esperado é `integer`, mas está como `VARCHAR`.

### tx_juros_am
- **Tipo**: String (esperado Float)
- **Descrição**: Taxa de juros ao mês em percentual.
- **Comportamento Esperado**: Não nulo, 300 valores únicos.
- **Anomalias**: Tipo de dado esperado é `float`, mas está como `VARCHAR`.

## Implicações de Compliance
- **SCR**: A tabela é candidata para o SCR, exigindo precisão e integridade dos dados.
- **LGPD**: Como os dados são classificados como restritos, é crucial garantir a proteção e o tratamento adequado dos dados pessoais.

## Pontos de Atenção
1. **Tipos de Dados**: Múltiplas colunas (`dt_contrato`, `vl_limite`, `vl_utilizado`, `dt_vencimento`, `nr_parcelas`, `tx_juros_am`) estão registradas como `VARCHAR` em vez dos tipos esperados (`date`, `float`, `integer`).
2. **Duplicação de Clientes**: Alta duplicação de valores na coluna `cd_cliente`, indicando potencial problema de integridade de dados.
3. **Compliance**: Garantir conformidade com SCR e LGPD, especialmente dado o status restrito dos dados.
4. **Validação de Dados**: Verificar se `vl_utilizado` realmente não excede `vl_limite` em mais de 15% para produtos com tolerância.
5. **Atualização de Dados**: A tabela é atualizada diariamente, exigindo monitoramento constante para garantir a integridade dos dados.

---
> **[AI_METADATA_STATUS: DRAFT]** — Documentação gerada por SLM. Requer validação humana pelo Data Steward responsável antes de uso em produção.