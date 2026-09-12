# Dicionário Técnico da Tabela `tb_transacoes`

## Visão Geral

A tabela `tb_transacoes` registra todas as movimentações financeiras realizadas através de diferentes canais de atendimento. Ela é gerida pela equipe `squad-transacoes` e está em sua versão `2.3.1`. O sistema de origem é o `SWITCH_TRANSACIONAL`, e os dados são armazenados em formato CSV com codificação UTF-8. A atualização dos dados é event-driven, e o contato para suporte é `squad-transacoes@banco.com.br`.

### Contexto de Negócio

O propósito da tabela é documentar todas as transações financeiras por canal. A coluna `fl_suspeita` indica se uma transação está sendo analisada pelo motor antifraude. A coluna `cd_estabelecimento` pode ser nula para compras online não identificadas, o que ocorre em aproximadamente 6% dos casos.

### Classificação Regulatória

A tabela está sujeita às regulamentações `BACEN_4658` e `PCI_DSS`, com classificação de dados como confidencial. Os dados devem ser retidos por 7 anos.

### Tolerância

- **Máximo de Nulos**: 10%
- **Máximo de Rejeições**: 2%
- **Duplicatas**: Não permitidas

### Dependências

- `tb_clientes`

### Consultas de Amostra

1. **Volume Transacionado por Canal no Mês**:
   ```sql
   SELECT cd_canal, COUNT(*) as qtd, SUM(vl_transacao) as total FROM tb_transacoes GROUP BY cd_canal
   ```

2. **Transações Suspeitas Recentes**:
   ```sql
   SELECT * FROM tb_transacoes WHERE fl_suspeita = true ORDER BY dt_transacao DESC LIMIT 100
   ```

## Esquema de Colunas

### `id_transacao`
- **Tipo**: `string`
- **Nullable**: Não
- **Descrição**: UUID da transação, gerado pelo switch transacional no momento da operação.
- **Comportamento Esperado**: Valor único para cada transação.
- **Anomalias**: 0.5% de duplicatas observadas.

### `cd_cliente`
- **Tipo**: `string`
- **Nullable**: Não
- **Descrição**: Referência ao cliente em `tb_clientes`.
- **Comportamento Esperado**: Valor único para cada cliente.
- **Anomalias**: Alta frequência de valores repetidos, indicando múltiplas transações por cliente.

### `dt_transacao`
- **Tipo**: `string` (deveria ser `date`)
- **Nullable**: Não
- **Descrição**: Data da transação no fuso horário America/Sao_Paulo.
- **Comportamento Esperado**: Formato de data válido.
- **Anomalias**: Tipo de dado incorreto (`VARCHAR` em vez de `DATE`).

### `vl_transacao`
- **Tipo**: `string` (deveria ser `float`)
- **Nullable**: Não
- **Descrição**: Valor em BRL. Positivo para débitos, negativo para estornos.
- **Comportamento Esperado**: Números positivos ou negativos representando valores monetários.
- **Anomalias**: Tipo de dado incorreto (`VARCHAR` em vez de `FLOAT`).

### `tp_transacao`
- **Tipo**: `string`
- **Nullable**: Não
- **Descrição**: Tipo da operação. Dominio: COMPRA, SAQUE, TED, PIX, PAGAMENTO_BOLETO, ESTORNO.
- **Comportamento Esperado**: Valores dentro do domínio especificado.
- **Anomalias**: Nenhuma observada.

### `cd_estabelecimento`
- **Tipo**: `string`
- **Nullable**: Sim
- **Descrição**: CNPJ do estabelecimento. Nulo para compras online não identificadas (~6%).
- **Comportamento Esperado**: CNPJ válido ou nulo.
- **Anomalias**: 6.7% de valores nulos, dentro do esperado.

### `fl_suspeita`
- **Tipo**: `string` (deveria ser `boolean`)
- **Nullable**: Não
- **Descrição**: Flag do motor antifraude. True indica transação em análise (~4% do volume).
- **Comportamento Esperado**: Valores `true` ou `false`.
- **Anomalias**: Tipo de dado incorreto (`VARCHAR` em vez de `BOOLEAN`).

### `cd_canal`
- **Tipo**: `string`
- **Nullable**: Não
- **Descrição**: Canal de origem. Dominio: APP, INTERNET, AGENCIA, ATM, POS.
- **Comportamento Esperado**: Valores dentro do domínio especificado.
- **Anomalias**: Nenhuma observada.

## Pontos de Atenção

1. **Tipos de Dados Incorretos**: As colunas `dt_transacao`, `vl_transacao` e `fl_suspeita` têm tipos de dados incorretos (`VARCHAR` em vez de `DATE`, `FLOAT` e `BOOLEAN`, respectivamente). Isso pode afetar a integridade dos dados e a execução de consultas.

2. **Duplicatas em `id_transacao`**: Apesar de ser a chave primária, foram encontradas duplicatas, o que viola a integridade referencial.

3. **Frequência de Valores Repetidos em `cd_cliente`**: Alta frequência de valores repetidos pode indicar múltiplas transações por cliente, mas deve ser monitorada para evitar duplicações não intencionais.

4. **Compliance Regulatória**: A tabela está sujeita a regulamentações `BACEN_4658` e `PCI_DSS`, exigindo que os dados sejam tratados com confidencialidade e segurança.

5. **Retenção de Dados**: Os dados devem ser mantidos por 7 anos, conforme a política de retenção.

---

> **[AI_METADATA_STATUS: DRAFT]** — Documentação gerada por SLM. Requer validação humana pelo Data Steward responsável antes de uso em produção.