# Dicionário Técnico da Tabela `tb_transacoes`

## Visão Geral

A tabela `tb_transacoes` registra todas as movimentações financeiras realizadas por diferentes canais de atendimento do banco. Ela é gerida pela equipe `squad-transacoes` e está atualmente em versão `2.3.1`. A tabela é alimentada de forma event-driven pelo sistema `SWITCH_TRANSACIONAL` e armazena dados em formato CSV com codificação UTF-8.

### Contexto de Negócio

- **Registro de Movimentações**: Cada linha representa uma transação financeira, incluindo detalhes como o cliente, valor, tipo de transação e canal de origem.
- **Análise Antifraude**: A coluna `fl_suspeita` indica se a transação está sendo analisada pelo motor antifraude.
- **Estabelecimento**: O campo `cd_estabelecimento` pode ser nulo para transações online não identificadas, o que ocorre em aproximadamente 6% dos casos.

### Regulamentações e Classificação de Dados

- **Tags Regulatórias**: A tabela está sujeita às normas `BACEN_4658` e `PCI_DSS`, exigindo conformidade com regulamentos financeiros e de segurança de dados.
- **Classificação de Dados**: Os dados são classificados como confidenciais e devem ser retidos por 7 anos.

## Esquema da Tabela

### Colunas

1. **id_transacao**
   - **Tipo**: `string`
   - **Nullable**: Não
   - **Descrição**: UUID da transação, gerado no momento da operação. Serve como chave primária.
   - **Comportamento Esperado**: Deve ser único para cada transação.

2. **cd_cliente**
   - **Tipo**: `string`
   - **Nullable**: Não
   - **Descrição**: Referência ao cliente na tabela `tb_clientes`.
   - **Comportamento Esperado**: Deve corresponder a um cliente existente na tabela `tb_clientes`.

3. **dt_transacao**
   - **Tipo**: `date`
   - **Nullable**: Não
   - **Descrição**: Data da transação no fuso horário America/Sao_Paulo.
   - **Comportamento Esperado**: Deve estar no formato correto e refletir a data real da transação.

4. **vl_transacao**
   - **Tipo**: `float`
   - **Nullable**: Não
   - **Descrição**: Valor da transação em BRL. Positivo para débitos, negativo para estornos.
   - **Comportamento Esperado**: Deve refletir o valor monetário da transação.

5. **tp_transacao**
   - **Tipo**: `string`
   - **Nullable**: Não
   - **Descrição**: Tipo da operação. Domínio: COMPRA, SAQUE, TED, PIX, PAGAMENTO_BOLETO, ESTORNO.
   - **Comportamento Esperado**: Deve corresponder a um dos tipos de transação definidos.

6. **cd_estabelecimento**
   - **Tipo**: `string`
   - **Nullable**: Sim
   - **Descrição**: CNPJ do estabelecimento. Pode ser nulo para compras online não identificadas.
   - **Comportamento Esperado**: Deve ser um CNPJ válido quando preenchido.

7. **fl_suspeita**
   - **Tipo**: `boolean`
   - **Nullable**: Não
   - **Descrição**: Indica se a transação está

---
> **[AI_METADATA_STATUS: DRAFT]**