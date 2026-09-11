# Dicionário Técnico: tb_contratos_credito

## Visão Geral

A tabela `tb_contratos_credito` contém informações sobre contratos de produtos de crédito ativos e encerrados. Ela alimenta o SCR (Sistema de Controle de Risco) mensalmente e é gerida pela equipe `squad-credito`. A tabela é atualizada diariamente e está armazenada no formato `sas7bdat` no sistema `SISTEMA_CREDITO_SAS`.

### Contexto de Negócio

- **Propósito**: Gerenciar contratos de crédito de todos os produtos ofertados pelo banco.
- **Regulamentações**: A tabela está sujeita a regulamentações como SCR, BACEN 4658 e LGPD.
- **Classificação de Dados**: Restrita, com retenção por 10 anos.
- **Tolerância**: 
  - Máximo de 5% de valores nulos permitidos.
  - Máximo de 1% de valores rejeitados permitidos.
  - Duplicatas não são permitidas.

### Colunas

1. **id_contrato**
   - **Tipo**: `string`
   - **Descrição**: Identificador único do contrato gerado pelo sistema de crédito.
   - **Comportamento Esperado**: Não nulo, chave primária.
   - **Estatísticas**: 299 valores únicos, nenhum nulo.
   - **Observações**: Correspondente ao `SAS_LABEL: ID CONTRATO CREDITO`.

2. **cd_cliente**
   - **Tipo**: `string`
   - **Descrição**: Referência ao cliente em `tb_clientes`.
   - **Comportamento Esperado**: Não nulo.
   - **Estatísticas**: 299 valores únicos, nenhum nulo.

3. **dt_contrato**
   - **Tipo**: `date`
   - **Descrição**: Data de abertura do contrato.
   - **Comportamento Esperado**: Não nulo.
   - **Estatísticas**: 282 valores únicos, nenhum nulo.

4. **vl_limite**
   - **Tipo**: `float`
   - **Descrição**: Limite de crédito aprovado em BRL.
   - **Comportamento Esperado**: Não nulo.
   - **Estatísticas**: Valores variam de 1065.12 a 99779.85, média de 52944.0009.
   - **Observações**: Cada valor é um candidato para SCR.

5. **vl_utilizado**
   - **Tipo**: `float`
   - **Descrição**: Saldo utilizado atual em BRL. Pode exceder `vl_limite` em até 15% para produtos com tolerância (ex: cheque especial).
   - **Comportamento Esperado**: Não nulo.
   - **Estatísticas**: Valores variam de 2455.09 a 92797.21, média de 34978.8.
   - **Observações**: Cada valor é um candidato para SCR.

6. **tp_produto**
   - **Tipo**: `string`
   - **Descrição**: Tipo do produto de crédito. Domínio: `CARTAO_CREDITO`, `CHEQUE_ESPECIAL`, `CREDITO_PESSOAL`, `FINANCIAMENTO_VEICULO`, `CONSIGNADO`.
   - **Comportamento Esperado**: Não nulo.
   - **Estatísticas**: 299 valores únicos, nenhum nulo.

7. **cd_status**
   - **Tipo**: `string`
   - **Descrição**: Status do contrato. Domínio: `ATIVO`, `ENCERRADO`, `EM_ATRASO`, `RENEGOCIADO`.
   - **Comportamento Esperado**: Não nulo.
   - **Estatísticas**: 4 valores únicos, distribuição: `RENEGOCIADO` (76), `EM_ATRASO` (76), `ENCERRADO` (74).
   - **Observações**: `EM_ATRASO` dispara cobrança automática após D+1.

8. **dt_vencimento**
   - **Tipo**: `date`
   - **Descrição**: Data de vencimento da última parcela ou do contrato.
   - **Comportamento Esperado**: Não nulo.
   - **Estatísticas**: 282 valores únicos, nenhum nulo.

9. **nr_parcelas**
   - **Tipo**: `integer`
   - **Descrição**: Número total de parcelas do contrato. 1 para crédito rotativo.
   - **Comportamento Esperado**: Não nulo.
   - **Estatísticas**: Valores variam de 1 a 60, média de 30.4281.

10. **tx_juros_am**
    - **Tipo**: `float`
    - **Descrição**: Taxa de juros ao mês em percentual. Ex: 2.5 = 2,5% a.m.
    - **Comportamento Esperado**: Não nulo.
    - **Estatísticas**: Valores variam de 0.8291 a 8.4105, média de 4.6686.
    - **Observações**: Correspondente ao `SAS_LABEL: TAXA JUROS MENSAL`.

### Anomalias e Observações

- **Duplicatas**: Nenhuma duplicata encontrada, o que está alinhado com a tolerância permitida.
- **Valores Nulos**: Nenhum valor nulo encontrado, o que está dentro da tolerância permitida.
- **Distribuição de Status**: A distribuição de status (`RENEGOCIADO`, `EM_ATRASO`, `ENCERRADO`) é equilibrada, sem anomalias óbvias.

### Implicações de Conformidade

- **SCR**: `vl_limite` e `vl_utilizado` são candidatos para SCR, exigindo monitoramento rigoroso.
- **LGPD**: A tabela contém dados restritos, exigindo medidas de proteção de dados adequadas.
- **BACEN 4658**: Requisitos de retenção de dados e relatórios regulatórios devem ser seguidos.

## Pontos de Atenção

- **Monitoramento de SCR**: Certifique-se de que `vl_limite` e `vl_utilizado` sejam monitorados regularmente para conformidade com SCR.
- **Gestão de Status**: A gestão do status do contrato, especialmente `EM_ATRASO`, deve ser monitorada para garantir a cobrança automática.
- **Proteção de Dados**: Implemente medidas de proteção de dados para cumprir com a LGPD.
- **Validação de Dados**: Verifique regularmente a integridade dos dados para garantir que não haja duplicatas ou valores nulos além do permitido.

---
> **[AI_METADATA_STATUS: DRAFT]** — Documentação gerada por SLM. Requer validação humana pelo Data Steward responsável antes de uso em produção.