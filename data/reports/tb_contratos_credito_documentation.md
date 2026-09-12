# Dicionário Técnico: tb_contratos_credito

## Visão Geral

A tabela `tb_contratos_credito` contém informações sobre contratos de produtos de crédito ativos e encerrados. Ela é gerida pela equipe `squad-credito` e alimenta o SCR mensalmente. A tabela é atualizada diariamente e é extraída do sistema `SISTEMA_CREDITO_SAS` no formato `sas7bdat`. A classificação de dados é restrita, com uma retenção de 10 anos, e está sujeita a regulamentações como SCR, BACEN_4658 e LGPD.

## Colunas

### id_contrato
- **Tipo**: string
- **Nullable**: false
- **Descrição**: Identificador único do contrato gerado pelo sistema de crédito.
- **SAS Label**: ID CONTRATO CREDITO
- **Comportamento Esperado**: Deve ser único para cada contrato.
- **Estatísticas**: 300 valores únicos, 0% nulos.

### cd_cliente
- **Tipo**: string
- **Nullable**: false
- **Descrição**: Referência ao cliente em `tb_clientes`.
- **Comportamento Esperado**: Deve corresponder a um cliente válido em `tb_clientes`.
- **Estatísticas**: 213 valores únicos, 0% nulos. Algumas duplicatas observadas, indicando múltiplos contratos por cliente.

### dt_contrato
- **Tipo**: string (esperado como date)
- **Nullable**: false
- **Descrição**: Data de abertura do contrato.
- **Comportamento Esperado**: Deve ser uma data válida no formato apropriado.
- **Estatísticas**: 282 valores únicos, 0% nulos. O tipo de dado é VARCHAR, indicando uma anomalia.

### vl_limite
- **Tipo**: string (esperado como float)
- **Nullable**: false
- **Descrição**: Limite de crédito aprovado em BRL.
- **Comportamento Esperado**: Deve ser um valor numérico positivo.
- **Estatísticas**: 300 valores únicos, 0% nulos. O tipo de dado é VARCHAR, indicando uma anomalia.
- **Implicações de Compliance**: Candidato ao SCR.

### vl_utilizado
- **Tipo**: string (esperado como float)
- **Nullable**: false
- **Descrição**: Saldo utilizado atual em BRL. Pode exceder `vl_limite` em produtos com tolerância.
- **Comportamento Esperado**: Deve ser um valor numérico positivo. Para `CHEQUE_ESPECIAL`, pode ser até 15% acima de `vl_limite`.
- **Estatísticas**: 300 valores únicos, 0% nulos. O tipo de dado é VARCHAR, indicando uma anomalia.
- **Implicações de Compliance**: Candidato ao SCR.

### tp_produto
- **Tipo**: string
- **Nullable**: false
- **Descrição**: Tipo do produto de crédito. Domínio: `CARTAO_CREDITO`, `CHEQUE_ESPECIAL`, `CREDITO_PESSOAL`, `FINANCIAMENTO_VEICULO`, `CONSIGNADO`.
- **Comportamento Esperado**: Deve ser um dos valores do domínio especificado.
- **Estatísticas**: 5 valores únicos, 0% nulos.

### cd_status
- **Tipo**: string
- **Nullable**: false
- **Descrição**: Status do contrato. Domínio: `ATIVO`, `ENCERRADO`, `EM_ATRASO`, `RENEGOCIADO`.
- **Comportamento Esperado**: Deve ser um dos valores do domínio especificado. `EM_ATRASO` dispara cobrança automática após D+1.
- **Estatísticas**: 4 valores únicos, 0% nulos.

### dt_vencimento
- **Tipo**: string (esperado como date)
- **Nullable**: false
- **Descrição**: Data de vencimento da última parcela ou do contrato.
- **Comportamento Esperado**: Deve ser uma data válida no formato apropriado.
- **Estatísticas**: 281 valores únicos, 0% nulos. O tipo de dado é VARCHAR, indicando uma anomalia.

### nr_parcelas
- **Tipo**: string (esperado como integer)
- **Nullable**: false
- **Descrição**: Número total de parcelas do contrato. 1 para crédito rotativo.
- **Comportamento Esperado**: Deve ser um número inteiro positivo.
- **Estatísticas**: 60 valores únicos, 0% nulos. O tipo de dado é VARCHAR, indicando uma anomalia.

### tx_juros_am
- **Tipo**: string (esperado como float)
- **Nullable**: false
- **Descrição**: Taxa de juros ao mês em percentual. Ex: 2.5 = 2,5% a.m.
- **Comportamento Esperado**: Deve ser um valor numérico positivo.
- **Estatísticas**: 300 valores únicos, 0% nulos. O tipo de dado é VARCHAR, indicando uma anomalia.
- **SAS Label**: TAXA JUROS MENSAL

## Anomalias Observadas

1. **Tipos de Dados**: Muitas colunas esperadas como numéricas ou datas estão armazenadas como VARCHAR, indicando uma anomalia na extração ou no armazenamento dos dados.
2. **Duplicatas**: A coluna `cd_cliente` apresenta duplicatas, sugerindo múltiplos contratos por cliente, o que é esperado, mas deve ser monitorado para consistência.
3. **Domínios**: Verificar se os valores de `tp_produto` e `cd_status` estão dentro dos domínios especificados.

## Implicações de Compliance

- **SCR**: `vl_limite` e `vl_utilizado` são candidatos ao SCR, exigindo precisão e integridade dos dados.
- **LGPD**: A tabela contém dados restritos, exigindo medidas de proteção de dados adequadas.

## Pontos de Atenção

- **Tipos de Dados**: Corrigir os tipos de dados das colunas `dt_contrato`, `vl_limite`, `vl_utilizado`, `dt_vencimento`, `nr_parcelas` e `tx_juros_am` para refletir os tipos esperados.
- **Domínios**: Validar os valores de `tp_produto` e `cd_status` para garantir que estejam dentro dos domínios permitidos.
- **Integridade de Dados**: Monitorar a integridade dos dados, especialmente para `cd_cliente`, garantindo que as referências sejam consistentes com `tb_clientes`.
- **Compliance**: Assegurar que as práticas de proteção de dados estejam alinhadas com a LGPD e que os dados candidatos ao SCR sejam precisos e confiáveis.

---

> **[AI_METADATA_STATUS: DRAFT]** — Documentação gerada por SLM. Requer validação humana pelo Data Steward responsável antes de uso em produção.