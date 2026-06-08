# Dicionário Técnico da Tabela `tb_contratos_credito`

## Visão Geral

A tabela `tb_contratos_credito` contém informações sobre contratos de produtos de crédito ativos e encerrados, conforme descrito no contrato YAML fornecido. Ela é gerida pela equipe `squad-credito` e alimenta o Sistema de Controle de Risco (SCR) mensalmente.

### Fonte de Dados

- **Sistema**: SISTEMA_CREDITO_SAS
- **Formato**: sas7bdat
- **Codificação**: latin-1
- **SO**: Unix
- **Frequência de Atualização**: Diária
- **Contato**: squad-credito@banco.com.br

### Contexto Regulatório e de Negócios

- **Tags Regulatórias**: SCR, BACEN_4658, LGPD
- **Classificação de Dados**: Restrita
- **Período de Retenção**: 10 anos

#### Contexto de Negócio

Os contratos de crédito abrangem todos os produtos oferecidos pelo banco. O valor utilizado (`vl_utilizado`) pode exceder o limite aprovado (`vl_limite`) em até 15% para produtos com tolerância, como o cheque especial. Um status de contrato `EM_ATRASO` desencadeia cobrança automática após D+1.

### Estrutura da Tabela

| Nome da Coluna       | Tipo    | Nulo Permitido | Descrição                                                                                      |
|----------------------|---------|----------------|------------------------------------------------------------------------------------------------|
| id_contrato          | string  | Não            | Identificador único do contrato gerado pelo sistema de crédito.                                |
| cd_cliente           | string  | Não            | Referência ao cliente em `tb_clientes`.                                                         |
| dt_contrato          | date    | Não            | Data de abertura do contrato.                                                                  |
| vl_limite            | float   | Não            | Limite de crédito aprovado em BRL.                                                              |
| vl_utilizado         | float   | Não            | Saldo utilizado atual em BRL. Pode exceder `vl_limite` em produtos com tolerância.              |
| tp_produto           | string  | Não            | Tipo do produto de crédito: CARTAO_CREDITO, CHEQUE_ESPECIAL, CREDITO_PESSOAL, FINANCIAMENTO_VEICULO, CONSIGNADO. |
| cd_status            | string  | Não            | Status do contrato: ATIVO, ENCERRADO, EM_ATRASO, RENEGOCIADO.                                   |
| dt_vencimento        | date    | Não            | Data de vencimento da última parcela ou do contrato.                                           |
| nr_parcelas          | integer | Não            | Número total de parcelas do contrato. 1 para crédito rotativo.                                  |
| tx_juros_am          | float   | Não            | Taxa de juros ao mês em percentual (ex: 2.5 = 2,5% a.m.).                                      |

### Análise das Estatísticas

#### id_contrato
- **Tipo**: VARCHAR
- **Percentual Nulo**: 0%
- **Contagem Única**: 300
- **Observação**: Cada contrato possui um identificador único conforme esperado.

#### cd_cliente
- **Tipo**: VARCHAR
- **Percentual Nulo**: 0%
- **Contagem Única**: 213
- **Anomalia**: Existem clientes com múltiplos contratos, o que é esperado em operações bancárias normais.

#### dt

---
> **[AI_METADATA_STATUS: DRAFT]**