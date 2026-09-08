# Dicionário Técnico: tb_contratos_credito

## Visão Geral da Tabela

- **Nome da Tabela**: `tb_contratos_credito`
- **Descrição**: Contratos de produtos de crédito ativos e encerrados.
- **Proprietário**: squad-credito
- **Versão**: 3.0.0
- **Status do Manifesto**: DRAFT
- **Fonte**:
  - **Sistema**: SISTEMA_CREDITO_SAS
  - **Formato**: sas7bdat
  - **Codificação**: latin-1
  - **Sistema Operacional**: unix
  - **Frequência de Atualização**: diária
  - **Contato**: squad-credito@banco.com.br
- **Regulamentação**:
  - **Tags**: SCR, BACEN_4658, LGPD
  - **Classificação de Dados**: restrita
  - **Período de Retenção**: 10 anos
- **Contexto de Negócio**: Contratos de crédito de todos os produtos ofertados pelo banco. Alimenta o SCR mensalmente. `vl_utilizado` pode exceder `vl_limite` em até 15% para produtos com tolerância de limite (cheque especial). `cd_status` EM_ATRASO dispara cobrança automática após D+1.

## Colunas da Tabela

### id_contrato
- **Tipo**: string
- **Nullable**: false
- **Chave Primária**: true
- **Descrição**: Identificador único do contrato gerado pelo sistema de crédito.
- **Etiqueta SAS**: ID CONTRATO CREDITO
- **Estatísticas**:
  - **% de Nulos**: 0.0
  - **Contagem Única**: 299
- **Comportamento Esperado**: Deve ser único e não nulo para cada contrato.

### cd_cliente
- **Tipo**: string
- **Nullable**: false
- **Descrição**: Referência ao cliente em `tb_clientes`.
- **Etiqueta SAS**: CODIGO CLIENTE
- **Estatísticas**:
  - **% de Nulos**: 0.0
  - **Contagem Única**: 299
- **Comportamento Esperado**: Deve ser único e não nulo, referenciando um cliente válido.

### dt_contrato
- **Tipo**: date
- **Nullable**: false
- **Descrição**: Data de abertura do contrato.
- **Estatísticas**:
  - **% de Nulos**: 0.0
  - **Contagem Única**: 282
- **Comportamento Esperado**: Deve ser uma data válida e não nula.

### vl_limite
- **Tipo**: float
- **Nullable**: false
- **Descrição**: Limite de crédito aprovado em BRL.
- **Etiqueta SAS**: VALOR LIMITE APROVADO
- **Estatísticas**:
  - **% de Nulos**: 0.0
  - **Contagem Única**: 299
  - **Mínimo**: 1065.12
  - **Máximo**: 99779.85
  - **Média**: 52944.0009
- **Comportamento Esperado**: Deve ser um valor monetário não nulo.
- **Implicações Regulatórias**: Candidato ao SCR.

### vl_utilizado
- **Tipo**: float
- **Nullable**: false
- **Descrição**: Saldo utilizado atual em BRL. Pode exceder `vl_limite` em produtos com tolerância.
- **Etiqueta SAS**: VALOR UTILIZADO ATUAL
- **Estatísticas**:
  - **% de Nulos**: 0.0
  - **Contagem Única**: 299
- **Comportamento Esperado**: Deve ser um valor monetário não nulo. Pode exceder `vl_limite` em até 15% para cheque especial.
- **Implicações Regulatórias**: Candidato ao SCR.

### tp_produto
- **Tipo**: string
- **Nullable**: false
- **Descrição**: Tipo do produto de crédito. Domínio: CARTAO_CREDITO, CHEQUE_ESPECIAL, CREDITO_PESSOAL, FINANCIAMENTO_VEICULO, CONSIGNADO.
- **Estatísticas**:
  - **% de Nulos**: 0.0
  - **Contagem Única**: 299
- **Comportamento Esperado**: Deve ser um dos valores do domínio especificado.

### cd_status
- **Tipo**: string
- **Nullable**: false
- **Descrição**: Status do contrato. Domínio: ATIVO, ENCERRADO, EM_ATRASO, RENEGOCIADO.
- **Estatísticas**:
  - **% de Nulos**: 0.0
  - **Contagem Única**: 4
  - **Valores Mais Comuns**: RENEGOCIADO (76), EM_ATRASO (76), ENCERRADO (74)
- **Comportamento Esperado**: Deve ser um dos valores do domínio especificado.
- **Regras de Negócio**: EM_ATRASO dispara cobrança automática após D+1.

### dt_vencimento
- **Tipo**: date
- **Nullable**: false
- **Descrição**: Data de vencimento da última parcela ou do contrato.
- **Estatísticas**:
  - **% de Nulos**: 0.0
  - **Contagem Única**: 282
- **Comportamento Esperado**: Deve ser uma data válida e não nula.

### nr_parcelas
- **Tipo**: integer
- **Nullable**: false
- **Descrição**: Número total de parcelas do contrato. 1 para crédito rotativo.
- **Estatísticas**:
  - **% de Nulos**: 0.0
  - **Contagem Única**: 60
  - **Mínimo**: 1.0
  - **Máximo**: 60.0
  - **Média**: 30.4281
- **Comportamento Esperado**: Deve ser um número inteiro não nulo, com 1 indicando crédito rotativo.

### tx_juros_am
- **Tipo**: float
- **Nullable**: false
- **Descrição**: Taxa de juros ao mês em percentual. Ex: 2.5 = 2,5% a.m.
- **Etiqueta SAS**: TAXA JUROS MENSAL
- **Estatísticas**:
  - **% de Nulos**: 0.0
  - **Contagem Única**: 299
  - **Mínimo**: 0.8291
  - **Máximo**: 8.4105
  - **Média**: 4.6686
- **Comportamento Esperado**: Deve ser um valor percentual não nulo.

## Anomalias e Observações

- **Tolerância de Nulos**: 0.0% de nulos para todas as colunas, o que está dentro do limite aceitável.
- **Contagem Única**: Todas as colunas têm contagem única igual ao número de registros (299), indicando ausência de duplicatas.
- **Domínios**: As colunas `tp_produto` e `cd_status` devem ser validadas contra seus respectivos domínios.
- **Valores Excedentes**: `vl_utilizado` pode exceder `vl_limite` em até 15% para cheque especial, conforme regra de negócio.

## Implicações Regulatórias

- **SCR**: `vl_limite` e `vl_utilizado` são candidatos ao SCR, exigindo monitoramento e relatórios regulares.
- **LGPD**: A classificação de dados como restrita implica em medidas de proteção de dados e conformidade com a LGPD.

## Pontos de Atenção

- **

---
> **[AI_METADATA_STATUS: DRAFT]**