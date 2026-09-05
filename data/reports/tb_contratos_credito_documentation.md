# Dicionário Técnico: tb_contratos_credito

## Visão Geral
A tabela `tb_contratos_credito` contém informações sobre contratos de produtos de crédito ativos e encerrados. Ela é gerida pela equipe `squad-credito` e é alimentada diariamente pelo sistema `SISTEMA_CREDITO_SAS`. A tabela é essencial para o cálculo do Score de Crédito (SCR) e está sujeita a regulamentações como a LGPD e a BACEN 4658, com uma classificação de dados restrita e um período de retenção de 10 anos.

## Colunas

### id_contrato
- **Tipo**: string
- **Nullable**: false
- **Descrição**: Identificador único do contrato gerado pelo sistema de crédito.
- **Propósito de Negócio**: Serve como chave primária para identificar exclusivamente cada contrato.
- **Comportamento Esperado**: Deve ser único para cada registro.
- **Anomalias**: Nenhuma anomalia observada; 100% de unicidade.

### cd_cliente
- **Tipo**: string
- **Nullable**: false
- **Descrição**: Referência ao cliente em `tb_clientes`.
- **Propósito de Negócio**: Liga o contrato ao cliente correspondente.
- **Comportamento Esperado**: Deve corresponder a um cliente válido na tabela `tb_clientes`.
- **Anomalias**: Alta frequência de valores repetidos, indicando múltiplos contratos por cliente.

### dt_contrato
- **Tipo**: string (esperado como date)
- **Nullable**: false
- **Descrição**: Data de abertura do contrato.
- **Propósito de Negócio**: Registra quando o contrato foi iniciado.
- **Comportamento Esperado**: Deve ser uma data válida e formatada corretamente.
- **Anomalias**: Armazenado como string, o que pode causar problemas de análise de dados.

### vl_limite
- **Tipo**: string (esperado como float)
- **Nullable**: false
- **Descrição**: Limite de crédito aprovado em BRL.
- **Propósito de Negócio**: Define o valor máximo que pode ser utilizado pelo cliente.
- **Comportamento Esperado**: Deve ser um número positivo.
- **Anomalias**: Armazenado como string, o que pode causar problemas de cálculo.
- **Implicações de Compliance**: Candidato ao SCR, exigindo precisão nos valores.

### vl_utilizado
- **Tipo**: string (esperado como float)
- **Nullable**: false
- **Descrição**: Saldo utilizado atual em BRL. Pode exceder `vl_limite` em produtos com tolerância.
- **Propósito de Negócio**: Indica o valor atualmente utilizado pelo cliente.
- **Comportamento Esperado**: Deve ser um número positivo; pode exceder `vl_limite` em até 15% para cheque especial.
- **Anomalias**: Armazenado como string, o que pode causar problemas de cálculo.
- **Implicações de Compliance**: Candidato ao SCR, exigindo precisão nos valores.

### tp_produto
- **Tipo**: string
- **Nullable**: false
- **Descrição**: Tipo do produto de crédito. Domínio: `CARTAO_CREDITO`, `CHEQUE_ESPECIAL`, `CREDITO_PESSOAL`, `FINANCIAMENTO_VEICULO`, `CONSIGNADO`.
- **Propósito de Negócio**: Identifica o tipo de produto de crédito associado ao contrato.
- **Comportamento Esperado**: Deve ser um valor válido dentro do domínio especificado.
- **Anomalias**: Nenhuma anomalia observada.

### cd_status
- **Tipo**: string
- **Nullable**: false
- **Descrição**: Status do contrato. Domínio: `ATIVO`, `ENCERRADO`, `EM_ATRASO`, `RENEGOCIADO`.
- **Propósito de Negócio**: Indica o estado atual do contrato.
- **Comportamento Esperado**: Deve ser um valor válido dentro do domínio especificado.
- **Anomalias**: Nenhuma anomalia observada.
- **Regras de Negócio**: `EM_ATRASO` dispara cobrança automática após D+1.

### dt_vencimento
- **Tipo**: string (esperado como date)
- **Nullable**: false
- **Descrição**: Data de vencimento da última parcela ou do contrato.
- **Propósito de Negócio**: Indica quando o contrato ou a última parcela deve ser paga.
- **Comportamento Esperado**: Deve ser uma data válida e formatada corretamente.
- **Anomalias**: Armazenado como string, o que pode causar problemas de análise de dados.

### nr_parcelas
- **Tipo**: string (esperado como integer)
- **Nullable**: false
- **Descrição**: Número total de parcelas do contrato. 1 para crédito rotativo.
- **Propósito de Negócio**: Indica quantas parcelas o contrato é dividido.
- **Comportamento Esperado**: Deve ser um número inteiro positivo.
- **Anomalias**: Armazenado como string, o que pode causar problemas de cálculo.

### tx_juros_am
- **Tipo**: string (esperado como float)
- **Nullable**: false
- **Descrição**: Taxa de juros ao mês em percentual. Ex: 2.5 = 2,5% a.m.
- **Propósito de Negócio**: Define a taxa de juros aplicada ao contrato.
- **Comportamento Esperado**: Deve ser um número positivo.
- **Anomalias**: Armazenado como string, o que pode causar problemas de cálculo.

## Implicações de Compliance
- **SCR**: A tabela é candidata ao SCR, exigindo precisão e integridade nos dados financeiros.
- **LGPD**: Como os dados são classificados como restritos, é crucial garantir a proteção e o uso adequado dos dados pessoais.
- **BACEN 4658**: A tabela deve estar em conformidade com as normas de relatórios ao Banco Central.

## Pontos de Atenção
1. **Tipos de Dados**: Muitas colunas estão armazenadas como strings, o que pode causar problemas de análise e cálculo. É recomendável converter essas colunas para seus tipos esperados (float, date, integer).
2. **Dupla Referência de Clientes**: Alta frequência de valores repetidos em `cd_cliente` sugere múltiplos contratos por cliente, o que deve ser verificado para evitar inconsistências.
3. **Precisão dos Dados**: Como a tabela é candidata ao SCR, é essencial garantir a precisão dos valores financeiros.
4. **Validação de Dados**: Implementar validações para garantir que os valores estejam dentro dos domínios esperados e que as regras de negócio sejam respeitadas.
5. **Conformidade Regulatória**: Manter a conformidade com LGPD e BACEN 4658 é crucial, especialmente considerando a classificação de dados restritos.

---
> **[AI_METADATA_STATUS: DRAFT]** — Documentação gerada por SLM. Requer validação humana pelo Data Steward responsável antes de uso em produção.