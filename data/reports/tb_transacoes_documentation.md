# Dicionário Técnico da Tabela `tb_transacoes`

## Visão Geral

A tabela `tb_transacoes` registra todas as movimentações financeiras realizadas por diferentes canais de atendimento, conforme descrito no contrato de dados. Ela é gerida pela equipe `squad-transacoes` e está atualmente em versão `2.3.1`. O sistema de origem é o `SWITCH_TRANSACIONAL`, e os dados são armazenados no formato CSV com codificação UTF-8.

### Contexto de Negócio

- **Propósito**: Registro de todas as movimentações financeiras por canal.
- **Detalhes Importantes**: 
  - A coluna `fl_suspeita` indica se uma transação está sendo analisada pelo motor antifraude.
  - A coluna `cd_estabelecimento` pode ser nula para compras online não identificadas, o que ocorre em aproximadamente 6% dos casos.

### Regulamentações e Compliance

- **Tags Regulatórias**: 
  - **BACEN_4658**: Normas do Banco Central do Brasil.
  - **PCI_DSS**: Normas de segurança para processamento de dados de cartões de pagamento.
- **Classificação de Dados**: Confidencial.
- **Período de Retenção**: 7 anos.

## Esquema da Tabela

### Colunas

1. **id_transacao**
   - **Tipo**: `string`
   - **Nullable**: Não
   - **Descrição**: UUID da transação, gerado pelo switch transacional no momento da operação.
   - **Comportamento Esperado**: Valor único por transação.
   - **Anomalias**: 2% de duplicatas observadas.

2. **cd_cliente**
   - **Tipo**: `string`
   - **Nullable**: Não
   - **Descrição**: Referência ao cliente em `tb_clientes`.
   - **Comportamento Esperado**: Valor único por cliente.
   - **Anomalias**: Alta frequência de valores repetidos.

3. **dt_transacao**
   - **Tipo**: `string` (deveria ser `date`)
   - **Nullable**: Não
   - **Descrição**: Data da transação no fuso horário America/Sao_Paulo.
   - **Comportamento Esperado**: Formato de data válido.
   - **Anomalias**: Dados armazenados como `VARCHAR`, o que pode causar problemas de validação de formato.

4. **vl_transacao**
   - **Tipo**: `string` (deveria ser `float`)
   - **Nullable**: Não
   - **Descrição**: Valor em BRL. Positivo para débitos, negativo para estornos.
   - **Comportamento Esperado**: Valores numéricos.
   - **Anomalias**: Dados armazenados como `VARCHAR`, o que pode causar problemas de cálculo.

5. **tp_transacao**
   - **Tipo**: `string`
   - **Nullable**: Não
   - **Descrição**: Tipo da operação. Dominio: COMPRA, SAQUE, TED, PIX, PAGAMENTO_BOLETO, ESTORNO.
   - **Comportamento Esperado**: Valores dentro do domínio especificado.

6. **cd_estabelecimento**
   - **Tipo**: `string`
   - **Nullable**: Sim
   - **Descrição**: CNPJ do estabelecimento. Nulo para compras online não identificadas (~6%).
   - **Comportamento Esperado**: CNPJ válido ou nulo.
   - **Anomalias**: 6.7% de valores nulos, dentro da expectativa.

7. **fl_suspeita**
   - **Tipo**: `string` (deveria ser `boolean`)
   - **Nullable**: Não
   - **Descrição**: Flag do motor antifraude. True indica transação em análise (~4% do volume).
   - **Comportamento Esperado**: Valores booleanos (`true` ou `false`).
   - **Anomalias**: Dados armazenados como `VARCHAR`, o que pode causar problemas de interpretação.

8. **cd_canal**
   - **Tipo**: `string`
   - **Nullable**: Não
   - **Descrição**: Canal de origem. Dominio: APP, INTERNET, AGENCIA, ATM, POS.
   - **Comportamento Esperado**: Valores dentro do domínio especificado.

## Pontos de Atenção

- **Duplicatas**: A coluna `id_transacao` apresenta duplicatas, o que viola a restrição de unicidade.
- **Tipos de Dados**: As colunas `dt_transacao`, `vl_transacao` e `fl_suspeita` estão armazenadas como `VARCHAR` em vez de `date`, `float` e `boolean`, respectivamente. Isso pode causar problemas de validação e cálculo.
- **Frequência de Valores Repetidos**: A coluna `cd_cliente` apresenta uma alta frequência de valores repetidos, o que pode indicar problemas na integração com `tb_clientes`.
- **Período de Retenção**: A tabela contém dados confidenciais que devem ser mantidos por 7 anos, exigindo políticas de retenção e exclusão adequadas.

---

> **[AI_METADATA_STATUS: DRAFT]** — Documentação gerada por SLM. Requer validação humana pelo Data Steward responsável antes de uso em produção.