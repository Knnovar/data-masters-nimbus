# Dicionário Técnico da Tabela `tb_contratos_credito`

## Visão Geral

A tabela `tb_contratos_credito` armazena informações sobre contratos de produtos de crédito ativos e encerrados oferecidos pelo banco. Ela alimenta o Sistema de Controle de Risco (SCR) mensalmente e é gerida pela equipe `squad-credito`. A versão atual do contrato é 3.0.0, e está em fase de rascunho.

### Contexto de Negócios

Os contratos cobrem todos os produtos de crédito oferecidos pelo banco. Notavelmente:
- O valor utilizado (`vl_utilizado`) pode exceder o limite aprovado (`vl_limite`) até 15% para produtos com tolerância, como o cheque especial.
- Um status de contrato `EM_ATRASO` aciona uma cobrança automática após D+1.

### Regulamentação e Compliance

A tabela possui as seguintes tags regulatórias:
- **SCR**: Candidato ao Sistema de Controle de Risco.
- **BACEN_4658**: Norma do Banco Central do Brasil.
- **LGPD**: Lei Geral de Proteção de Dados.

Os dados são classificados como restritos e têm uma retenção obrigatória de 10 anos. Qualquer análise ou uso deve considerar essas implicações regulatórias.

## Esquema da Tabela

### Colunas

1. **id_contrato**
   - **Tipo**: String
   - **Descrição**: Identificador único do contrato gerado pelo sistema de crédito.
   - **Negócio**: Serve como chave primária e garante unicidade para cada contrato.
   - **Estatísticas**: 0% de valores nulos, 299 entradas únicas.

2. **cd_cliente**
   - **Tipo**: String
   - **Descrição**: Referência ao cliente em `tb_clientes`.
   - **Negócio**: Garante a ligação entre contratos e clientes.
   - **Estatísticas**: 0% de valores nulos, 299 entradas únicas.

3. **dt_contrato**
   - **Tipo**: Date
   - **Descrição**: Data de abertura do contrato.
   - **Negócio**: Usado para rastrear a validade e o histórico dos contratos.
   - **Estatísticas**: 0% de valores nulos, 282 entradas únicas.

4. **vl_limite**
   - **Tipo**: Float
   - **Descrição**: Limite de crédito aprovado em BRL.
   - **Negócio**: Valor máximo que pode ser utilizado pelo cliente sob o contrato.
   - **Estatísticas**: 0% de valores nulos, faixa de 1065.12 a 99779.85, média de 52944.0009.

5. **vl_utilizado**
   - **Tipo**: Float
   - **Descrição**: Saldo utilizado atual em BRL.
   - **Negócio**: Pode exceder `vl_limite` até 15% para produtos com tolerância, como cheque especial.
   - **Estatísticas**: 0% de valores nulos.

6. **tp_produto**
   - **Tipo**: String
   - **Descrição**: Tipo do produto de crédito (ex: CARTAO_CREDITO, CHEQUE_ESPECIAL).
   - **Negócio**: Define o tipo de contrato e suas regras associadas.
   - **Estatísticas**: 0% de valores nulos.

7. **cd_status**
   - **Tipo**: String
   - **Descrição**:

---
> **[AI_METADATA_STATUS: DRAFT]**