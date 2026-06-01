# Dicionário Técnico da Tabela `tb_transacoes_non_breaking`

## Visão Geral

A tabela `tb_transacoes_non_breaking` registra todas as movimentações financeiras por canal, conforme descrito no contrato YAML. Ela é gerida pela equipe `squad-transacoes` e está em conformidade com os regulamentos BACEN_4658 e PCI_DSS. A classificação de dados é confidencial, com um período de retenção de 7 anos.

## Colunas

### id_transacao
- **Propósito de Negócio**: Identificador único para cada transação.
- **Tipo**: `VARCHAR`
- **Comportamento Esperado**: Não nulo e deve ser único. No entanto, foram encontradas duplicatas (2% dos registros).
- **Anomalias**:
  - Duplicatas observadas: ~2% de duplicidade.

### cd_cliente
- **Propósito de Negócio**: Referência ao cliente na tabela `tb_clientes`.
- **Tipo**: `VARCHAR`
- **Comportamento Esperado**: Não nulo.
- **Anomalias**:
  - Alta concentração em poucos clientes, indicando potencialmente transações repetidas ou erros de entrada.

### dt_transacao
- **Propósito de Negócio**: Data da transação no fuso horário America/Sao_Paulo.
- **Tipo**: `VARCHAR`
- **Comportamento Esperado**: Não nulo e deve ser uma data válida. No entanto, o tipo é incorreto; deveria ser `DATE`.
- **Anomalias**:
  - Tipo de dado incorreto: Deveria ser `DATE`.

### vl_transacao
- **Propósito de Negócio**: Valor da transação em BRL.
- **Tipo**: `VARCHAR`
- **Comportamento Esperado**: Não nulo e deve representar valores monetários válidos. No entanto, o tipo é incorreto; deveria ser `FLOAT`.
- **Anomalias**:
  - Tipo de dado incorreto: Deveria ser `FLOAT`.

### tp_transacao
- **Propósito de Negócio**: Tipo da operação (COMPRA, SAQUE, TED, PIX, PAGAMENTO_BOLETO, ESTORNO).
- **Tipo**: `VARCHAR`
- **Comportamento Esperado**: Não nulo e deve corresponder aos domínios especificados.
- **Anomalias**:
  - Nenhum valor fora do domínio observado.

### cd_estabelecimento
- **Propósito de Negócio**: CNPJ do estabelecimento. Pode ser nulo para compras online não identificadas.
- **Tipo**: `VARCHAR`
- **Comportamento Esperado**: Pode ser nulo, com ~6% esperados como nulos conforme o contexto de negócios.
- **Anomalias**:
  - Percentual de valores nulos ligeiramente acima do esperado (~5.86%).

### fl_suspeita
- **Propósito de Negócio**: Flag indicando se a transação está sendo analisada pelo motor antifraude.
- **Tipo**: `VARCHAR`
- **Comportamento Esperado**: Não nulo e deve ser booleano (True/False). No entanto, o tipo é incorreto; deveria ser `BOOLEAN`.
- **Anomalias**:
  - Tipo de dado incorreto: Deveria ser `BOOLEAN`.

### cd_canal
- **Propósito de Negócio**: Canal de origem da transação (APP, INTERNET, AGENCIA, ATM, POS).
- **Tipo**: `VARCHAR`


---
> **[AI_METADATA_STATUS: DRAFT]**