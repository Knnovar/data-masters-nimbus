# Dicionário Técnico: tb_contratos_credito

## Visão Geral

A tabela `tb_contratos_credito` armazena informações sobre contratos de produtos de crédito ativos e encerrados. Ela é gerida pela equipe `squad-credito` e é alimentada diariamente pelo sistema `SISTEMA_CREDITO_SAS`. A tabela é essencial para o cumprimento do SCR (Serviço de Proteção ao Crédito) e está sujeita a regulamentações como a LGPD (Lei Geral de Proteção de Dados) e a BACEN_4658.

### Propósito de Negócio

- **Contratos de Crédito**: Inclui todos os produtos de crédito oferecidos pelo banco.
- **Alimentação do SCR**: A tabela alimenta o SCR mensalmente.
- **Regras de Negócio**: `vl_utilizado` pode exceder `vl_limite` em até 15% para produtos com tolerância de limite (ex: cheque especial). `cd_status` EM_ATRASO dispara cobrança automática após D+1.

### Regulamentações e Classificação de Dados

- **Regulatory Tags**: SCR, BACEN_4658, LGPD.
- **Classificação de Dados**: Restrita.
- **Período de Retenção**: 10 anos.

## Colunas

### id_contrato
- **Tipo**: String
- **Nullable**: Não
- **Descrição**: Identificador único do contrato gerado pelo sistema de crédito.
- **Comportamento Esperado**: Valor único por contrato.
- **Anomalias**: Nenhuma observada (0% nulos, 100% únicos).

### cd_cliente
- **Tipo**: String
- **Nullable**: Não
- **Descrição**: Referência ao cliente em `tb_clientes`.
- **Comportamento Esperado**: Valor único por cliente.
- **Anomalias**: Alta frequência de valores repetidos (213 únicos em 300 registros).

### dt_contrato
- **Tipo**: String (deveria ser Date)
- **Nullable**: Não
- **Descrição**: Data de abertura do contrato.
- **Comportamento Esperado**: Formato de data válido.
- **Anomalias**: Tipo de dado incorreto (VARCHAR em vez de DATE).

### vl_limite
- **Tipo**: String (deveria ser Float)
- **Nullable**: Não
- **Descrição**: Limite de crédito aprovado em BRL.
- **Comportamento Esperado**: Valor numérico positivo.
- **Anomalias**: Tipo de dado incorreto (VARCHAR em vez de FLOAT).

### vl_utilizado
- **Tipo**: String (deveria ser Float)
- **Nullable**: Não
- **Descrição**: Saldo utilizado atual em BRL. Pode exceder `vl_limite` em produtos com tolerância.
- **Comportamento Esperado**: Valor numérico positivo.
- **Anomalias**: Tipo de dado incorreto (VARCHAR em vez de FLOAT).

### tp_produto
- **Tipo**: String
- **Nullable**: Não
- **Descrição**: Tipo do produto de crédito. Domínio: CARTAO_CREDITO, CHEQUE_ESPECIAL, CREDITO_PESSOAL, FINANCIAMENTO_VEICULO, CONSIGNADO.
- **Comportamento Esperado**: Valores dentro do domínio especificado.
- **Anomalias**: Nenhuma observada.

### cd_status
- **Tipo**: String
- **Nullable**: Não
- **Descrição**: Status do contrato. Domínio: ATIVO, ENCERRADO, EM_ATRASO, RENEGOCIADO.
- **Comportamento Esperado**: Valores dentro do domínio especificado.
- **Anomalias**: Nenhuma observada.

### dt_vencimento
- **Tipo**: String (deveria ser Date)
- **Nullable**: Não
- **Descrição**: Data de vencimento da última parcela ou do contrato.
- **Comportamento Esperado**: Formato de data válido.
- **Anomalias**: Tipo de dado incorreto (VARCHAR em vez de DATE).

### nr_parcelas
- **Tipo**: String (deveria ser Integer)
- **Nullable**: Não
- **Descrição**: Número total de parcelas do contrato. 1 para crédito rotativo.
- **Comportamento Esperado**: Valor numérico inteiro positivo.
- **Anomalias**: Tipo de dado incorreto (VARCHAR em vez de INTEGER).

### tx_juros_am
- **Tipo**: String (deveria ser Float)
- **Nullable**: Não
- **Descrição**: Taxa de juros ao mês em percentual. Ex: 2.5 = 2,5% a.m.
- **Comportamento Esperado**: Valor numérico positivo.
- **Anomalias**: Tipo de dado incorreto (VARCHAR em vez de FLOAT).

## Pontos de Atenção

1. **Tipos de Dados Incorretos**: Múltiplas colunas (`dt_contrato`, `vl_limite`, `vl_utilizado`, `dt_vencimento`, `nr_parcelas`, `tx_juros_am`) estão armazenadas como VARCHAR em vez dos tipos esperados (Date, Float, Integer).

2. **Duplicatas de Clientes**: Alta frequência de valores repetidos em `cd_cliente`, indicando potencial duplicação de registros de clientes.

3. **Compliance Regulatório**: A tabela contém dados restritos e deve ser gerenciada conforme as regulamentações LGPD e BACEN_4658.

4. **Regras de Negócio**: Garantir que `vl_utilizado` não exceda `vl_limite` além do permitido para produtos específicos.

5. **Atualização de Dados**: A tabela é atualizada diariamente, exigindo monitoramento constante para garantir a integridade e precisão dos dados.

---

> **[AI_METADATA_STATUS: DRAFT]** — Documentação gerada por SLM. Requer validação humana pelo Data Steward responsável antes de uso em produção.