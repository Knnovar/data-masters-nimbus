# Dicionário Técnico da Tabela `tb_contratos_credito`

## Visão Geral

A tabela `tb_contratos_credito` armazena informações sobre contratos de produtos de crédito ativos e encerrados, conforme descrito no manifesto do contrato. Ela alimenta o Sistema de Controle de Risco (SCR) mensalmente e é gerida pela equipe `squad-credito`. A tabela está em formato SAS (`sas7bdat`) com codificação `latin-1` e atualizações diárias.

### Contexto de Negócio

Os contratos de crédito incluem todos os produtos oferecidos pelo banco. O valor utilizado (`vl_utilizado`) pode exceder o limite aprovado (`vl_limite`) em até 15% para produtos com tolerância, como o cheque especial. Um contrato com status `EM_ATRASO` dispara cobrança automática após D+1.

### Regulamentação

- **Tags Regulatórias**: SCR, BACEN_4658, LGPD
- **Classificação de Dados**: Restrita
- **Período de Retenção**: 10 anos

## Colunas da Tabela

### `id_contrato`
- **Tipo**: String (VARCHAR)
- **Nullable**: Não
- **Descrição**: Identificador único do contrato gerado pelo sistema de crédito.
- **SAS Label**: ID CONTRATO CREDITO
- **Estatísticas**:
  - Nenhum valor nulo (0.0%).
  - Contagem única: 300, indicando que não há duplicatas.

### `cd_cliente`
- **Tipo**: String (VARCHAR)
- **Nullable**: Não
- **Descrição**: Referência ao cliente em `tb_clientes`.
- **Estatísticas**:
  - Nenhum valor nulo (0.0%).
  - Contagem única: 213, sugerindo que alguns clientes têm múltiplos contratos.

### `dt_contrato`
- **Tipo**: String (VARCHAR)
- **Nullable**: Não
- **Descrição**: Data de abertura do contrato.
- **Estatísticas**:
  - Nenhum valor nulo (0.0%).
  - Contagem única: 280, indicando algumas datas repetidas.

### `vl_limite`
- **Tipo**: String (VARCHAR)
- **Nullable**: Não
- **Descrição**: Limite de crédito aprovado em BRL.
- **SAS Label**: VALOR LIMITE APROVADO
- **Regulamentação**: Candidato ao SCR
- **Estatísticas**:
  - Nenhum valor nulo (0.0%).
  - Intervalo: Min = 1211.66, Max = 99512.12, Média = 52578.1934

### `vl_utilizado`
- **Tipo**: String (VARCHAR)
- **Nullable**: Não
- **Descrição**: Saldo utilizado atual em BRL.
- **SAS Label**: VALOR UTILIZADO ATUAL
- **Regulamentação**: Candidato ao SCR
- **Regras de Negócio**:
  - Pode exceder `vl_limite` em até 15% para produtos como CHEQUE_ESPECIAL.
- **Estatísticas**:
  - Nenhum valor nulo (0.0%).
  - Intervalo: Min = 70.63, Max = 109174.48, Média = 31152.5684

### `tp_produto`
- **Tipo**: String (VARCHAR)
- **Nullable**: Não
- **Descrição**: Tipo do produto de crédito.
- **Dominio**: CARTAO

---
> **[AI_METADATA_STATUS: DRAFT]**