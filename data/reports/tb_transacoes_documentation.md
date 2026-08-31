# Dicionário Técnico da Tabela `tb_transacoes`

## Visão Geral

A tabela `tb_transacoes` registra todas as movimentações financeiras realizadas através de diferentes canais de atendimento. Ela é gerida pela equipe `squad-transacoes` e está atualmente em fase de rascunho (DRAFT). A tabela é alimentada por um sistema chamado `SWITCH_TRANSACIONAL` e é armazenada no formato CSV com codificação UTF-8 em um sistema operacional Unix. As atualizações são feitas de forma event-driven.

### Contexto de Negócio

- **Registro de Movimentações**: A tabela captura todas as transações financeiras, incluindo compras, saques, TEDs, PIXs, pagamentos de boletos e estornos.
- **Flag de Transações Suspeitas**: A coluna `fl_suspeita` indica se uma transação está sendo analisada pelo motor antifraude.
- **Estabelecimento Não Identificado**: A coluna `cd_estabelecimento` pode ser nula para compras online não identificadas, o que ocorre em cerca de 6% das transações.

### Considerações de Conformidade

- **Regulatory Tags**: A tabela está sujeita às normas BACEN_4658 e PCI_DSS, o que implica em requisitos rigorosos de segurança e privacidade dos dados.
- **Classificação de Dados**: Os dados são classificados como confidenciais e devem ser retidos por 7 anos.

## Colunas da Tabela

### `id_transacao`

- **Tipo**: `VARCHAR`
- **Nullable**: Não
- **Descrição**: UUID da transação, gerado pelo switch transacional no momento da operação.
- **Estatísticas**:
  - **% de Nulos**: 0.0%
  - **Contagem Única**: 1999
  - **Duplicatas**: Algumas duplicatas observadas, o que é uma anomalia dado que `id_transacao` é a chave primária.

### `cd_cliente`

- **Tipo**: `VARCHAR`
- **Nullable**: Não
- **Descrição**: Referência ao cliente na tabela `tb_clientes`.
- **Estatísticas**: Não fornecidas no perfil de dados.

### `dt_transacao`

- **Tipo**: `DATE`
- **Nullable**: Não
- **Descrição**: Data da transação no fuso horário America/Sao_Paulo.
- **Estatísticas**: Não fornecidas no perfil de dados.

### `vl_transacao`

- **Tipo**: `FLOAT`
- **Nullable**: Não
- **Descrição**: Valor em BRL. Positivo para débitos, negativo para estornos.
- **Estatísticas**: Não fornecidas no perfil de dados.

### `tp_transacao`

- **Tipo**: `VARCHAR`
- **Nullable**: Não
- **Descrição**: Tipo da operação. Domínio: COMPRA, SAQUE, TED, PIX, PAGAMENTO_BOLETO, ESTORNO.
- **Estatísticas**:
  - **% de Nulos**: 0.0%
  - **Contagem Única**: 1999
  - **Valores Comuns**: COMPRA, PAGAMENTO_BOLETO, SAQUE (cada um com 2 ocorrências).

### `cd_estabelecimento`

- **Tipo**: `VARCHAR`
- **Nullable**: Sim
- **Descrição**: CNPJ do estabelecimento. Pode ser nulo para compras online não identificadas (~6%).
- **Estat

---
> **[AI_METADATA_STATUS: DRAFT]**