# Dicionário Técnico da Tabela `tb_transacoes`

## Visão Geral

A tabela `tb_transacoes` registra todas as movimentações financeiras realizadas por diferentes canais de atendimento do banco. Ela é gerida pela equipe `squad-transacoes` e está atualmente em fase de rascunho (DRAFT). A tabela é alimentada por um sistema chamado `SWITCH_TRANSACIONAL` e está classificada como confidencial, com uma retenção de dados de 7 anos. As transações são registradas em formato CSV com codificação UTF-8.

### Contexto de Negócio

- **Registro de Movimentações**: A tabela captura todas as transações financeiras, incluindo compras, saques, TEDs, PIXs, pagamentos de boletos e estornos.
- **Fl_suspeita**: Indica se uma transação está sendo analisada pelo motor antifraude.
- **cd_estabelecimento**: Pode ser nulo para compras online não identificadas, o que ocorre em aproximadamente 6% das transações.

### Regulamentações

- **Tags Regulatórias**: BACEN_4658 e PCI_DSS.
- **Implicações de Compliance**: A tabela deve atender aos requisitos do Banco Central e PCI DSS, garantindo a proteção de dados sensíveis e a integridade das transações financeiras.

## Esquema da Tabela

### Colunas

1. **id_transacao**
   - **Tipo**: String
   - **Nullable**: Não
   - **Descrição**: UUID da transação, gerado no momento da operação.
   - **Propósito de Negócio**: Identificador único para cada transação.
   - **Comportamento Esperado**: Deve ser único e não nulo.
   - **Anomalias**: Duplicatas observadas (2 registros duplicados).

2. **cd_cliente**
   - **Tipo**: String
   - **Nullable**: Não
   - **Descrição**: Referência ao cliente em `tb_clientes`.
   - **Propósito de Negócio**: Identifica o cliente associado à transação.
   - **Comportamento Esperado**: Deve ser único e não nulo.

3. **dt_transacao**
   - **Tipo**: Date
   - **Nullable**: Não
   - **Descrição**: Data da transação no fuso horário America/Sao_Paulo.
   - **Propósito de Negócio**: Registra a data e hora da transação.
   - **Comportamento Esperado**: Deve ser uma data válida e não nula.

4. **vl_transacao**
   - **Tipo**: Float
   - **Nullable**: Não
   - **Descrição**: Valor em BRL. Positivo para débitos, negativo para estornos.
   - **Propósito de Negócio**: Valor monetário da transação.
   - **Comportamento Esperado**: Deve ser um número válido e não nulo.

5. **tp_transacao**
   - **Tipo**: String
   - **Nullable**: Não
   - **Descrição**: Tipo da operação. Dominio: COMPRA, SAQUE, TED, PIX, PAGAMENTO_BOLETO, ESTORNO.
   - **Propósito de Negócio**: Define o tipo de transação.
   - **Comportamento Esperado**: Deve estar dentro do domínio especificado.

6. **cd_estabelecimento**
   - **Tipo**: String
   - **Nullable**: Sim
   - **Descrição**: CNPJ do estabelecimento. Nulo para compras online não identificadas (~6%).
   - **Propósito de Negócio**: Identifica o estabelecimento associado à transação.
   - **Comportamento Esperado**: Pode ser nulo para transações online não identificadas.
   - **Anomalias**: 6.41% de valores nulos, conforme esperado.

7. **fl_suspeita**
   - **Tipo**: Boolean
   - **Nullable**: Não
   - **Descrição**: Flag do motor antifraude. True indica transação em análise (~4% do volume).
   - **Propósito de Negócio**: Indica se a transação está sendo analisada por fraude.
   - **Comportamento Esperado**: Deve ser verdadeiro ou falso.

8. **cd_canal**
   - **Tipo**: String
   - **Nullable**: Não
   - **Descrição**: Canal de origem. Dominio: APP, INTERNET, AGENCIA, ATM, POS.
   - **Propósito de Negócio**: Identifica o canal através do qual a transação foi realizada.
   - **Comportamento Esperado**: Deve estar dentro do domínio especificado.

### Anomalias Observadas

- **Duplicatas**: A coluna `id_transacao` apresenta duplicatas, o que é uma anomalia crítica dado que é a chave primária.
- **Valores Nulos**: A coluna `cd_estabelecimento` tem 6.41% de valores nulos, o que está dentro do esperado para compras online não identificadas.

## Pontos de Atenção

- **Duplicatas na Chave Primária**: A presença de duplicatas na coluna `id_transacao` é uma anomalia crítica que precisa ser investigada e corrigida.
- **Valores Nulos em `cd_estabelecimento`**: Embora esperado, o percentual de valores nulos deve ser monitorado para garantir que não ultrapasse o limite aceitável.
- **Compliance Regulatória**: A tabela deve ser constantemente auditada para garantir conformidade com BACEN_4658 e PCI DSS.
- **Monitoramento de Transações Suspeitas**: A coluna `fl_suspeita` deve ser monitorada para identificar e mitigar riscos de fraude.

---

> **[AI_METADATA_STATUS: DRAFT]** — Documentação gerada por SLM. Requer validação humana pelo Data Steward responsável antes de uso em produção.