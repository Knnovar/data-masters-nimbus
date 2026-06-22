# Dicionário Técnico da Tabela `tb_transacoes_non_breaking`

## Visão Geral

A tabela `tb_transacoes_non_breaking` registra todas as movimentações financeiras realizadas através dos diversos canais de atendimento do banco, conforme descrito no contrato YAML. Ela é gerida pela equipe `squad-transacoes` e está em conformidade com os regulamentos BACEN_4658 e PCI_DSS.

### Propósito de Negócio

A tabela serve para documentar todas as transações financeiras por canal, incluindo informações sobre suspeitas de fraude. O campo `fl_suspeita` indica se uma transação está sendo analisada pelo motor antifraude.

## Colunas da Tabela

### 1. id_transacao
- **Tipo**: VARCHAR
- **Nullable**: Não
- **Descrição**: UUID da transação, gerado no momento da operação.
- **Comportamento Esperado**: Cada valor deve ser único e não nulo.
- **Estatísticas Observadas**:
  - Percentual de valores nulos: 0.0%
  - Contagem única: 1999
  - Duplicatas observadas: Sim, com algumas transações repetidas.

### 2. cd_cliente
- **Tipo**: VARCHAR (mapeado para `5993.48PIX`)
- **Nullable**: Não
- **Descrição**: Referência ao cliente em `tb_clientes`.
- **Comportamento Esperado**: Cada valor deve ser único e não nulo.
- **Estatísticas Observadas**:
  - Percentual de valores nulos: 0.0%
  - Contagem única: 1999
  - Duplicatas observadas: Sim, com algumas transações repetidas.

### 3. dt_transacao
- **Tipo**: Não especificado diretamente nas estatísticas (assumido como VARCHAR)
- **Nullable**: Não
- **Descrição**: Data da transação no fuso horário America/Sao_Paulo.
- **Comportamento Esperado**: Deve conter datas válidas e não nulas.

### 4. vl_transacao
- **Tipo**: VARCHAR (mapeado para `62180753000183`)
- **Nullable**: Não
- **Descrição**: Valor em BRL, positivo para débitos, negativo para estornos.
- **Comportamento Esperado**: Deve conter valores numéricos válidos e não nulos.
- **Estatísticas Observadas**:
  - Percentual de valores nulos: 6.06%
  - Contagem única: 1875
  - Valores fora da faixa esperada podem estar presentes, considerando o tipo VARCHAR.

### 5. tp_transacao
- **Tipo**: VARCHAR (mapeado para `FATM`)
- **Nullable**: Não
- **Descrição**: Tipo da operação, domínio: COMPRA, SAQUE, TED, PIX, PAGAMENTO_BOLETO, ESTORNO.
- **Comportamento Esperado**: Deve conter apenas valores dentro do domínio especificado.
- **Estatísticas Observadas**:
  - Percentual de valores nulos: 0.0%
  - Contagem única: 10
  - Valores dominantes: FPOS, FAPP, FINTERNET.

### 6. cd_estabelecimento
- **Tipo**: Não especificado diretamente nas estatísticas (assumido como VARCHAR)
- **Nullable**: Sim
- **Descrição**: CNPJ do estabelecimento. Pode ser nulo para compras online não identificadas.
- **Comportamento Esperado**:

---
> **[AI_METADATA_STATUS: DRAFT]**