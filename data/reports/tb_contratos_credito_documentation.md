# Dicionário Técnico: tb_contratos_credito

## Visão Geral

A tabela `tb_contratos_credito` armazena dados sobre contratos de produtos de crédito ativos e encerrados. Ela é gerida pela equipe `squad-credito` e está em versão `3.0.0`. Os dados são extraídos diariamente do sistema `SISTEMA_CREDITO_SAS` em formato `sas7bdat` e codificados em `latin-1`. A tabela alimenta o SCR mensalmente e é classificada como restrita, com uma retenção de 10 anos. As tags regulatórias incluem SCR, BACEN_4658 e LGPD.

## Colunas

### id_contrato
- **Tipo**: string
- **Nullable**: false
- **Descrição**: Identificador único do contrato gerado pelo sistema de crédito.
- **SAS Label**: ID CONTRATO CREDITO
- **Propósito de Negócio**: Serve como chave primária para identificar exclusivamente cada contrato.
- **Comportamento Esperado**: Deve ser único e não nulo para cada registro.
- **Anomalias**: Nenhuma anomalia observada; 100% de unicidade.

### cd_cliente
- **Tipo**: string
- **Nullable**: false
- **Descrição**: Referência ao cliente em `tb_clientes`.
- **SAS Label**: CODIGO CLIENTE
- **Propósito de Negócio**: Liga o contrato ao cliente correspondente.
- **Comportamento Esperado**: Deve ser não nulo e corresponder a um cliente válido na tabela `tb_clientes`.
- **Anomalias**: Nenhuma anomalia observada; 100% de unicidade.

### dt_contrato
- **Tipo**: date
- **Nullable**: false
- **Descrição**: Data de abertura do contrato.
- **SAS Label**: DATA ABERTURA CONTRATO
- **Propósito de Negócio**: Indica quando o contrato foi inicialmente estabelecido.
- **Comportamento Esperado**: Deve ser uma data válida e não nula.
- **Anomalias**: Nenhuma anomalia observada; 282 valores únicos.

### vl_limite
- **Tipo**: float
- **Nullable**: false
- **Descrição**: Limite de crédito aprovado em BRL.
- **SAS Label**: VALOR LIMITE APROVADO
- **Propósito de Negócio**: Define o máximo que pode ser utilizado pelo cliente.
- **Comportamento Esperado**: Deve ser não nulo e positivo.
- **Anomalias**: Nenhuma anomalia observada; valores variam de 1065.12 a 99779.85 BRL.

### vl_utilizado
- **Tipo**: float
- **Nullable**: false
- **Descrição**: Saldo utilizado atual em BRL. Pode exceder `vl_limite` em produtos com tolerância.
- **SAS Label**: VALOR UTILIZADO ATUAL
- **Propósito de Negócio**: Mostra o valor atualmente utilizado do limite de crédito.
- **Comportamento Esperado**: Deve ser não nulo e pode exceder `vl_limite` em até 15% para produtos como cheque especial.
- **Anomalias**: Nenhuma anomalia observada; valores variam de 1065.12 a 99779.85 BRL.

### tp_produto
- **Tipo**: string
- **Nullable**: false
- **Descrição**: Tipo do produto de crédito. Domínio: CARTAO_CREDITO, CHEQUE_ESPECIAL,

---
> **[AI_METADATA_STATUS: DRAFT]**