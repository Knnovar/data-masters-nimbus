# Dicionário Técnico: tb_contratos_credito

## Visão Geral

A tabela `tb_contratos_credito` armazena informações sobre contratos de produtos de crédito ativos e encerrados. Ela é gerida pela equipe `squad-credito` e está atualizada diariamente. A tabela alimenta o SCR (Sistema de Controle de Risco) mensalmente e é classificada como restrita, com uma retenção de dados de 10 anos. Ela está sujeita a regulamentações como SCR, BACEN 4658 e LGPD.

## Colunas

### id_contrato
- **Tipo**: string
- **Nullable**: false
- **Descrição**: Identificador único do contrato gerado pelo sistema de crédito.
- **SAS Label**: ID CONTRATO CREDITO
- **Comportamento Esperado**: Cada contrato deve ter um identificador único. Não deve haver valores nulos ou duplicados.
- **Anomalias**: Nenhuma anomalia observada, pois todos os valores são únicos e não nulos.

### cd_cliente
- **Tipo**: string
- **Nullable**: false
- **Descrição**: Referência ao cliente em `tb_clientes`.
- **SAS Label**: CODIGO CLIENTE
- **Comportamento Esperado**: Cada contrato deve estar associado a um cliente válido. Não deve haver valores nulos ou duplicados.
- **Anomalias**: Nenhuma anomalia observada, pois todos os valores são únicos e não nulos.

### dt_contrato
- **Tipo**: date
- **Nullable**: false
- **Descrição**: Data de abertura do contrato.
- **SAS Label**: DATA ABERTURA CONTRATO
- **Comportamento Esperado**: Deve conter a data de abertura de cada contrato. Não deve haver valores nulos.
- **Anomalias**: Nenhuma anomalia observada, pois todos os valores são não nulos.

### vl_limite
- **Tipo**: float
- **Nullable**: false
- **Descrição**: Limite de crédito aprovado em BRL.
- **SAS Label**: VALOR LIMITE APROVADO
- **Regulatory Flags**: SCR_CANDIDATE
- **Comportamento Esperado**: Deve conter o valor do limite aprovado para cada contrato. Não deve haver valores nulos.
- **Anomalias**: Nenhuma anomalia observada, pois todos os valores são não nulos.

### vl_utilizado
- **Tipo**: float
- **Nullable**: false
- **Descrição**: Saldo utilizado atual em BRL. Pode exceder `vl_limite` em produtos com tolerância.
- **SAS Label**: VALOR UTILIZADO ATUAL
- **Regulatory Flags**: SCR_CANDIDATE
- **Business Rules**: Pode ser até 15% acima de `vl_limite` para `CHEQUE_ESPECIAL`.
- **Comportamento Esperado**: Deve conter o saldo utilizado atual. Não deve haver valores nulos.
- **Anomalias**: Nenhuma anomalia observada, pois todos os valores são não nulos.

### tp_produto
- **Tipo**: string
- **Nullable**: false
- **Descrição**: Tipo do produto de crédito. Dominio: `CARTAO_CREDITO`, `CHEQUE_ESPECIAL`, `CREDITO_PESSOAL`, `FINANCIAMENTO_VEICULO`, `CONSIGNADO`.
- **Comportamento Esperado**: Deve conter um tipo de produto válido. Não deve haver valores nulos.
- **Anomalias**: Nenhuma anomalia observada, pois todos os valores são não nulos.

### cd_status
- **Tipo**: string
- **Nullable**: false
- **Descrição**: Status do contrato. Dominio: `ATIVO`, `ENCERRADO`, `EM_ATRASO`, `RENEGOCIADO`.
- **Business Rules**: `EM_ATRASO` dispara cobrança automática após D+1.
- **Comportamento Esperado**: Deve conter um status válido. Não deve haver valores nulos.
- **Anomalias**: Nenhuma anomalia observada, pois todos os valores são não nulos.

### dt_vencimento
- **Tipo**: date
- **Nullable**: false
- **Descrição**: Data de vencimento da última parcela ou do contrato.
- **Comportamento Esperado**: Deve conter a data de vencimento. Não deve haver valores nulos.
- **Anomalias**: Nenhuma anomalia observada, pois todos os valores são não nulos.

### nr_parcelas
- **Tipo**: integer
- **Nullable**: false
- **Descrição**: Número total de parcelas do contrato. 1 para crédito rotativo.
- **Comportamento Esperado**: Deve conter o número de parcelas. Não deve haver valores nulos.
- **Anomalias**: Nenhuma anomalia observada, pois todos os valores são não nulos.

### tx_juros_am
- **Tipo**: float
- **Nullable**: false
- **Descrição**: Taxa de juros ao mês em percentual. Ex: 2.5 = 2,5% a.m.
- **SAS Label**: TAXA JUROS MENSAL
- **Comportamento Esperado**: Deve conter a taxa de juros ao mês. Não deve haver valores nulos.
- **Anomalias**: Nenhuma anomalia observada, pois todos os valores são não nulos.

## Implicações de Compliance

- **SCR**: A tabela é candidata ao SCR, o que implica em monitoramento rigoroso de riscos associados aos contratos de crédito.
- **BACEN 4658**: Deve cumprir as normas de segurança da informação estabelecidas pelo Banco Central.
- **LGPD**: A classificação de dados como restrita exige medidas de proteção adequadas para garantir a privacidade e segurança dos dados pessoais.

## Pontos de Atenção

1. **Integridade dos Dados**: Garantir que todos os campos obrigatórios estejam preenchidos e que não haja duplicatas.
2. **Monitoramento de Anomalias**: Embora não sejam observadas atualmente, monitorar constantemente por valores fora de faixa, especialmente em `vl_utilizado` para `CHEQUE_ESPECIAL`.
3. **Compliance Regulatório**: Manter a conformidade com SCR, BACEN 4658 e LGPD, especialmente considerando a classificação de dados como restrita.
4. **Atualização Diária**: Assegurar que a tabela seja atualizada diariamente para refletir as mudanças nos contratos de crédito.

---
> **[AI_METADATA_STATUS: DRAFT]** — Documentação gerada por SLM. Requer validação humana pelo Data Steward responsável antes de uso em produção.