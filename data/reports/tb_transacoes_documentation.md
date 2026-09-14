# Dicionário Técnico da Tabela `tb_transacoes`

## Visão Geral

A tabela `tb_transacoes` registra todas as movimentações financeiras realizadas através de diferentes canais de atendimento do banco. Ela é gerida pela equipe `squad-transacoes` e está em sua versão 2.3.1. O sistema de origem é o `SWITCH_TRANSACIONAL`, e os dados são armazenados em formato CSV com codificação UTF-8 no sistema operacional Unix. A atualização dos dados é feita de forma event-driven, e o contato para suporte é `squad-transacoes@banco.com.br`.

### Contexto de Negócio

- **Registro de Movimentações**: A tabela captura todas as transações financeiras por canal.
- **Flag de Transações Suspeitas**: A coluna `fl_suspeita` indica se uma transação está sendo analisada pelo motor antifraude.
- **Estabelecimento Nulo**: A coluna `cd_estabelecimento` pode ser nula para compras online não identificadas, o que ocorre em aproximadamente 6% das transações.

### Regulamentações e Classificação de Dados

- **Tags Regulatórias**: A tabela está sujeita às normas `BACEN_4658` e `PCI_DSS`, o que implica em requisitos específicos de segurança e privacidade dos dados.
- **Classificação de Dados**: Os dados são classificados como confidenciais e devem ser retidos por 7 anos.

## Esquema da Tabela

### Colunas

1. **id_transacao**
   - **Tipo**: String
   - **Nullable**: Não
   - **Descrição**: UUID da transação, gerado no momento da operação.
   - **Comportamento Esperado**: Valor único para cada transação.
   - **Anomalias**: 2% de duplicatas observadas.

2. **cd_cliente**
   - **Tipo**: String
   - **Nullable**: Não
   - **Descrição**: Referência ao cliente em `tb_clientes`.
   - **Comportamento Esperado**: Valor único por cliente.
   - **Anomalias**: Alta concentração de transações por alguns clientes.

3. **dt_transacao**
   - **Tipo**: String (deveria ser Date)
   - **Nullable**: Não
   - **Descrição**: Data da transação no fuso horário America/Sao_Paulo.
   - **Comportamento Esperado**: Formato de data válido.
   - **Anomalias**: Tipo de dado incorreto (VARCHAR).

4. **vl_transacao**
   - **Tipo**: String (deveria ser Float)
   - **Nullable**: Não
   - **Descrição**: Valor em BRL. Positivo para débitos, negativo para estornos.
   - **Comportamento Esperado**: Valor numérico dentro do intervalo de 15.07 a 24986.13.
   - **Anomalias**: Tipo de dado incorreto (VARCHAR).

5. **tp_transacao**
   - **Tipo**: String
   - **Nullable**: Não
   - **Descrição**: Tipo da operação. Dominio: COMPRA, SAQUE, TED, PIX, PAGAMENTO_BOLETO, ESTORNO.
   - **Comportamento Esperado**: Valores dentro do domínio especificado.

6. **cd_estabelecimento**
   - **Tipo**: String
   - **Nullable**: Sim
   - **Descrição**: CNPJ do estabelecimento. Nulo para compras online não identificadas (~6%).
   - **Comportamento Esperado**: CNPJ válido ou nulo.
   - **Anomalias**: 6.5% de valores nulos, o que está dentro do esperado.

7. **fl_suspeita**
   - **Tipo**: String (deveria ser Boolean)
   - **Nullable**: Não
   - **Descrição**: Flag do motor antifraude. True indica transação em análise (~4% do volume).
   - **Comportamento Esperado**: Valores booleanos (True/False).
   - **Anomalias**: Tipo de dado incorreto (VARCHAR).

8. **cd_canal**
   - **Tipo**: String
   - **Nullable**: Não
   - **Descrição**: Canal de origem. Dominio: APP, INTERNET, AGENCIA, ATM, POS.
   - **Comportamento Esperado**: Valores dentro do domínio especificado.

### Anomalias e Observações

- **Duplicatas**: A coluna `id_transacao` apresenta duplicatas, o que é uma anomalia crítica dado que é a chave primária.
- **Tipos de Dados**: As colunas `dt_transacao`, `vl_transacao` e `fl_suspeita` têm tipos de dados incorretos (VARCHAR em vez de Date, Float e Boolean, respectivamente).
- **Concentração de Transações**: Algumas contas de clientes têm um volume significativo de transações, o que pode indicar padrões de uso ou necessidade de análise adicional.

## Pontos de Atenção

- **Validação de Tipos de Dados**: Corrigir os tipos de dados incorretos para garantir a integridade e a precisão dos dados.
- **Duplicatas na Chave Primária**: Investigar e resolver as duplicatas na coluna `id_transacao`.
- **Conformidade Regulatória**: Assegurar que todas as práticas de armazenamento e processamento de dados estejam em conformidade com as normas `BACEN_4658` e `PCI_DSS`.
- **Monitoramento de Transações Suspeitas**: Manter um monitoramento contínuo das transações marcadas como suspeitas para prevenir fraudes.

---

> **[AI_METADATA_STATUS: DRAFT]** — Documentação gerada por SLM. Requer validação humana pelo Data Steward responsável antes de uso em produção.