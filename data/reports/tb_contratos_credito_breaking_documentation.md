# Dicionário Técnico da Tabela `tb_contratos_credito_breaking`

## Visão Geral

A tabela `tb_contratos_credito_breaking` contém dados sobre contratos de produtos de crédito ativos e encerrados, conforme descrito no contrato YAML. Ela alimenta o Sistema de Controle de Risco (SCR) mensalmente e está sujeita a regulamentações específicas, incluindo SCR, BACEN 4658 e LGPD.

### Propriedades da Tabela

- **Owner**: squad-credito
- **Versão**: 3.0.0
- **Status do Manifesto**: DRAFT
- **Fonte**:
  - Sistema: SISTEMA_CREDITO_SAS
  - Formato: sas7bdat
  - Codificação: latin-1
  - SO: unix
  - Frequência de Atualização: diária
- **Contato**: squad-credito@banco.com.br

### Contexto Regulatório e de Negócios

- **Tags Regulatórias**:
  - SCR
  - BACEN_4658
  - LGPD
- **Classificação de Dados**: restrita
- **Período de Retenção**: 10 anos

## Colunas da Tabela

### `id_contrato` (string)

- **Descrição**: Identificador único do contrato gerado pelo sistema de crédito.
- **Propósito de Negócio**: Serve como chave primária para identificar exclusivamente cada contrato.
- **Tipo**: string
- **Comportamento Esperado**: Não nulos, valores únicos em todas as linhas.
- **Anomalias Observadas**: Nenhuma anomalia relatada.

### `cd_cliente` (string)

- **Descrição**: Referência ao cliente na tabela `tb_clientes`.
- **Propósito de Negócio**: Liga o contrato a um cliente específico.
- **Tipo**: string
- **Comportamento Esperado**: Não nulos, valores únicos em todas as linhas.
- **Anomalias Observadas**: Nenhuma anomalia relatada.

### `dt_contrato` (string)

- **Descrição**: Data de abertura do contrato.
- **Propósito de Negócio**: Registra quando o contrato foi inicialmente estabelecido.
- **Tipo**: string
- **Comportamento Esperado**: Não nulos, deve ser uma data válida.
- **Anomalias Observadas**: Nenhuma anomalia relatada.

### `vl_limite` (string)

- **Descrição**: Limite de crédito aprovado em BRL.
- **Propósito de Negócio**: Indica o valor máximo disponível para uso sob o contrato.
- **Tipo**: string
- **Comportamento Esperado**: Não nulos, valores numéricos positivos.
- **Anomalias Observadas**: Nenhuma anomalia relatada.

### `vl_utilizado` (string)

- **Descrição**: Saldo utilizado atual em BRL. Pode exceder `vl_limite` para produtos com tolerância.
- **Propósito de Negócio**: Monitora o uso do limite de crédito pelo cliente.
- **Tipo**: string
- **Comportamento Esperado**: Não nulos, valores numéricos positivos ou negativos permitidos conforme regras de negócios.
- **Anomalias Observadas**: Nenhuma anomalia relatada.

### `tp_produto` (string)

- **Descrição**: Tipo do produto de crédito. Domínio: CARTAO_CREDITO, CHEQUE_ESPECIAL, CREDITO_PESSOAL, FINANCI

---
> **[AI_METADATA_STATUS: DRAFT]**