# Dicionário Técnico: tb_contratos_credito

## Visão Geral

A tabela `tb_contratos_credito` contém informações sobre contratos de produtos de crédito ativos e encerrados. Ela alimenta o Sistema de Controle de Risco (SCR) mensalmente e é gerida pela equipe `squad-credito`. Os dados são extraídos do sistema `SISTEMA_CREDITO_SAS` em formato `sas7bdat` e são atualizados diariamente.

### Contexto de Negócio

- **Propósito**: Gerenciar e monitorar contratos de crédito de todos os produtos oferecidos pelo banco.
- **Regulamentações**: Os dados estão classificados como restritos e devem ser retidos por 10 anos. As tags regulatórias incluem SCR, BACEN_4658 e LGPD.
- **Regras de Negócio**:
  - `vl_utilizado` pode exceder `vl_limite` em até 15% para produtos com tolerância de limite, como o cheque especial.
  - `cd_status` com valor `EM_ATRASO` dispara cobrança automática após D+1.

### Análise de Colunas

#### id_contrato
- **Tipo**: string
- **Descrição**: Identificador único do contrato gerado pelo sistema de crédito.
- **Comportamento Esperado**: Não nulos, chave primária.
- **Estatísticas**: 299 valores únicos, nenhum nulo.

#### cd_cliente
- **Tipo**: string
- **Descrição**: Referência ao cliente em `tb_clientes`.
- **Comportamento Esperado**: Não nulos.
- **Estatísticas**: 299 valores únicos, nenhum nulo.

#### dt_contrato
- **Tipo**: date
- **Descrição**: Data de abertura do contrato.
- **Comportamento Esperado**: Não nulos.
- **Estatísticas**: 282 valores únicos, nenhum nulo.

#### vl_limite
- **Tipo**: float
- **Descrição**: Limite de crédito aprovado em BRL.
- **Comportamento Esperado**: Não nulos.
- **Estatísticas**: Valores variam de 1065.12 a 99779.85 BRL, nenhum nulo.
- **Implicações Regulatórias**: Candidato ao SCR.

#### vl_utilizado
- **Tipo**: float
- **Descrição**: Saldo utilizado atual em BRL. Pode exceder `vl_limite` em produtos com tolerância.
- **Comportamento Esperado**: Não nulos.
- **Estatísticas**: Valores variam de 92797.21 a 3817.24 BRL, nenhum nulo.
- **Regras de Negócio**: Pode ser até 15% acima de `vl_limite` para `CHEQUE_ESPECIAL`.
- **Implicações Regulatórias**: Candidato ao SCR.

#### tp_produto
- **Tipo**: string
- **Descrição**: Tipo do produto de crédito. Domínio: `CARTAO_CREDITO`, `CHEQUE_ESPECIAL`, `CREDITO_PESSOAL`, `FINANCIAMENTO_VEICULO`, `CONSIGNADO`.
- **Comportamento Esperado**: Não nulos.
- **Estatísticas**: 299 valores únicos, nenhum nulo.

#### cd_status
- **Tipo**: string
- **Descrição**: Status do contrato. Domínio: `ATIVO`, `ENCERRADO`, `EM_ATRASO`, `RENEGOCIADO`.
- **Comportamento Esperado**: Não nulos.
- **Estatísticas**: 4 valores únicos, nenhum nulo.
- **Regras de Negócio**: `EM_ATRASO` dispara cobrança automática após D+1.

#### dt_vencimento
- **Tipo**: date
- **Descrição**: Data de vencimento da última parcela ou do contrato.
- **Comportamento Esperado**: Não nulos.
- **Estatísticas**: 282 valores únicos, nenhum nulo.

#### nr_parcelas
- **Tipo**: integer
- **Descrição**: Número total de parcelas do contrato. 1 para crédito rotativo.
- **Comportamento Esperado**: Não nulos.
- **Estatísticas**: Valores variam de 1 a 60, nenhum nulo.

#### tx_juros_am
- **Tipo**: float
- **Descrição**: Taxa de juros ao mês em percentual. Ex: 2.5 = 2,5% a.m.
- **Comportamento Esperado**: Não nulos.
- **Estatísticas**: Valores variam de 0.8291 a 8.4105, nenhum nulo.
- **Implicações Regulatórias**: Candidato ao SCR.

### Anomalias e Observações

- **Duplicatas**: A tabela não permite duplicatas, conforme a tolerância especificada.
- **Nulos**: Nenhuma coluna excede o limite de 5% de nulos.
- **Valores Fora de Faixa**: Verificar se `vl_utilizado` excede `vl_limite` em mais de 15% para produtos sem tolerância.

### Pontos de Atenção

1. **Compliance Regulatória**: Garantir que os dados sejam tratados conforme as normas SCR, BACEN_4658 e LGPD.
2. **Regras de Negócio**: Monitorar a execução automática de cobranças para contratos em atraso.
3. **Integridade dos Dados**: Assegurar que `vl_utilizado` não exceda `vl_limite` além do permitido para produtos sem tolerância.
4. **Atualização Diária**: Verificar a consistência dos dados após cada atualização diária.

---

> **[AI_METADATA_STATUS: DRAFT]** — Documentação gerada por SLM. Requer validação humana pelo Data Steward responsável antes de uso em produção.