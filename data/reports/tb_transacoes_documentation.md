# Dicionário Técnico da Tabela `tb_transacoes`

## Visão Geral

A tabela `tb_transacoes` registra todas as movimentações financeiras realizadas por diferentes canais de atendimento do banco. Ela é gerida pela equipe `squad-transacoes` e está atualmente em versão `2.3.1`. O sistema de origem é `SWITCH_TRANSACIONAL`, e os dados são armazenados em formato CSV com codificação UTF-8 no sistema operacional Unix. A atualização dos dados é event-driven, e o contato para questões relacionadas é `squad-transacoes@banco.com.br`.

### Contexto de Negócio

O propósito principal da tabela é registrar todas as movimentações financeiras por canal. O campo `fl_suspeita` indica se a transação está sendo analisada pelo motor antifraude. O campo `cd_estabelecimento` pode ser nulo para compras online não identificadas, o que ocorre em aproximadamente 6% dos casos.

### Classificação e Retenção de Dados

Os dados são classificados como confidenciais e devem ser retidos por 7 anos. As tags regulatórias associadas são `BACEN_4658` e `PCI_DSS`, o que implica que a tabela deve cumprir com as normas do Banco Central do Brasil e os padrões de segurança de dados do PCI DSS.

## Esquema da Tabela

### Colunas

1. **id_transacao**
   - **Tipo**: `string`
   - **Nullable**: Não
   - **Descrição**: UUID da transação, gerado pelo switch transacional no momento da operação. Serve como a chave primária da tabela.
   - **Comportamento Esperado**: Deve ser único para cada transação.
   - **Anomalias Observadas**: 0.5% das transações apresentam duplicatas.

2. **cd_cliente**
   - **Tipo**: `string`
   - **Nullable**: Não
   - **Descrição**: Referência ao cliente em `tb_clientes`.
   - **Comportamento Esperado**: Deve corresponder a um cliente existente na tabela `tb_clientes`.

3. **dt_transacao**
   - **Tipo**: `date`
   - **Nullable**: Não
   - **Descrição**: Data da transação no fuso horário America/Sao_Paulo.
   - **Comportamento Esperado**: Deve estar no formato correto e dentro do intervalo de datas esperado.

4. **vl_transacao**
   - **Tipo**: `float`
   - **Nullable**: Não
   - **Descrição**: Valor em BRL. Positivo para débitos, negativo para estornos.
   - **Comportamento Esperado**: Deve ser um número válido e refletir o valor correto da transação.
   - **Anomalias Observadas**: Nenhuma anomalia significativa observada.

5. **tp_transacao**
   - **Tipo**: `string`
   - **Nullable**: Não
   - **Descrição**: Tipo da operação. Dominio: COMPRA, SAQUE, TED, PIX, PAGAMENTO_BOLETO, ESTORNO.
   - **Comportamento Esperado**: Deve corresponder a um dos tipos de operação definidos no domínio.

6. **cd_estabelecimento**
   - **Tipo**: `string`
   - **Nullable**: Sim
   - **Descrição**: CNPJ do estabelecimento. Nulo para compras online não identificadas (~6%).
   - **Comportamento Esperado**: Deve ser um CNPJ válido

---
> **[AI_METADATA_STATUS: DRAFT]**