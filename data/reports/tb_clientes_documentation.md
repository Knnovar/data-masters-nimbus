# Dicionário Técnico da Tabela `tb_clientes`

## Visão Geral

A tabela `tb_clientes` é um cadastro mestre de clientes pessoa física e jurídica. Ela é utilizada por todos os produtos de crédito e relacionamento do banco. A segmentação (`cd_segmento`) determina o produto ofertado e o gestor responsável. A tabela é atualizada diariamente pelo batch noturno do sistema CORE_BANCARIO_TOTVS.

### Propriedades da Tabela

- **Owner**: squad-dados-cadastrais
- **Versão**: 1.0.0
- **Status do Manifesto**: DRAFT
- **Fonte**: Sistema CORE_BANCARIO_TOTVS, formato CSV, codificação UTF-8, sistema operacional Unix, atualização diária.
- **Contato**: squad-dados-cadastrais@banco.com.br
- **Classificação de Dados**: Confidencial
- **Período de Retenção**: 10 anos
- **Regulamentações**: LGPD, BACEN 4658
- **Tolerância**: Máximo de 25% de valores nulos permitidos, duplicatas não permitidas.

## Colunas

### `cd_cliente`
- **Tipo**: VARCHAR
- **Descrição**: Código único do cliente no sistema legado. Gerado sequencialmente pelo CORE_BANCARIO.
- **Negócio**: Identificador primário do cliente.
- **Comportamento Esperado**: Não nulo, único para cada cliente.
- **Estatísticas**: 0% de valores nulos, 500 valores únicos.
- **Anomalias**: Nenhuma.

### `nr_cpf_cnpj`
- **Tipo**: VARCHAR
- **Descrição**: CPF (11 dígitos) ou CNPJ (14 dígitos) sem máscara.
- **Negócio**: Identificador único de pessoa física ou jurídica.
- **Comportamento Esperado**: Não nulo, deve ser único e corresponder ao formato CPF ou CNPJ.
- **Estatísticas**: 0% de valores nulos, 500 valores únicos.
- **Anomalias**: Nenhuma.
- **Implicações de Compliance**: Sensível à LGPD.

### `nm_cliente`
- **Tipo**: VARCHAR
- **Descrição**: Nome completo do cliente conforme cadastro na Receita Federal.
- **Negócio**: Nome do cliente para identificação.
- **Comportamento Esperado**: Não nulo, deve ser único, exceto em casos de duplicação de nomes.
- **Estatísticas**: 0% de valores nulos, 497 valores únicos.
- **Anomalias**: Duplicação de nomes observada (ex: "Olívia Oliveira" aparece 2 vezes).
- **Implicações de Compliance**: Sensível à LGPD.

### `dt_nascimento`
- **Tipo**: VARCHAR
- **Descrição**: Data de nascimento. Nula para clientes PJ.
- **Negócio**: Data de nascimento para clientes pessoa física.
- **Comportamento Esperado**: Pode ser nulo para clientes jurídicos.
- **Estatísticas**: 0% de valores nulos, 495 valores únicos.
- **Anomalias**: Nenhuma, mas o tipo de dado deve ser corrigido para DATE.

### `cd_segmento`
- **Tipo**: VARCHAR
- **Descrição**: Segmento de relacionamento. Domínio: VAREJO, PRIME, PRIVATE, PJ_PEQUENO, PJ_MEDIO.
- **Negócio**: Determina o produto ofertado e o gestor responsável.
- **Comportamento Esperado**: Não nulo, deve seguir as regras de negócio para renda mensal.
- **Estatísticas**: 0% de valores nulos, 5 valores únicos.
- **Anomalias**: Nenhuma, mas a validação das regras de negócio deve ser verificada (ex: renda mensal para segmentos PJ_PEQUENO e PJ_MEDIO deve ser nula).

### `cd_agencia`
- **Tipo**: VARCHAR
- **Descrição**: Código numérico de 4 dígitos da agência de relacionamento principal.
- **Negócio**: Identificador da agência associada ao cliente.
- **Comportamento Esperado**: Não nulo.
- **Estatísticas**: 0% de valores nulos, 473 valores únicos.
- **Anomalias**: Valores como "AGENC-???" indicam potenciais erros de entrada de dados.

### `vl_renda_mensal`
- **Tipo**: VARCHAR
- **Descrição**: Renda mensal declarada em BRL. Nula para clientes PJ.
- **Negócio**: Indicador de capacidade financeira do cliente.
- **Comportamento Esperado**: Pode ser nulo para clientes PJ, deve ser numérico.
- **Estatísticas**: 20.6% de valores nulos, 397 valores únicos.
- **Anomalias**: Tipo de dado deve ser corrigido para FLOAT, nulos observados para segmentos PJ_PEQUENO e PJ_MEDIO, conforme regras de negócio.

### `fl_ativo`
- **Tipo**: VARCHAR
- **Descrição**: Indica se o cliente possui relacionamento ativo com o banco.
- **Negócio**: Status de ativação do cliente.
- **Comportamento Esperado**: Não nulo, deve ser booleano.
- **Estatísticas**: 0% de valores nulos, 2 valores únicos (True, False).
- **Anomalias**: Tipo de dado deve ser corrigido para BOOLEAN.

### `dt_cadastro`
- **Tipo**: VARCHAR
- **Descrição**: Data de abertura do cadastro no sistema.
- **Negócio**: Data de início do relacionamento do cliente com o banco.
- **Comportamento Esperado**: Não nulo.
- **Estatísticas**: 0% de valores nulos, 462 valores únicos.
- **Anomalias**: Tipo de dado deve ser corrigido para DATE.

## Pontos de Atenção

1. **Tipos de Dados**: Múltiplas colunas (`dt_nascimento`, `vl_renda_mensal`, `fl_ativo`, `dt_cadastro`) estão definidas como VARCHAR, mas devem ser corrigidas para os tipos apropriados (DATE, FLOAT, BOOLEAN).

2. **Duplicação de Nomes**: A coluna `nm_cliente` apresenta duplicação de nomes, o que pode indicar problemas de integridade de dados.

3. **Valores de Agência**: A presença de valores como "AGENC-???" na coluna `cd_agencia` sugere erros de entrada de dados que precisam ser investigados.

4. **Regras de Negócio**: A validação das regras de negócio para `cd_segmento` e `vl_renda_mensal` deve ser realizada para garantir conformidade com as expectativas de segmentação.

5. **Compliance LGPD**: Dados sensíveis como `nr_cpf_cnpj`, `nm_cliente` e `dt_nascimento` requerem tratamento especial para garantir conformidade com a LGPD.

6. **Duplicatas**: A tabela não deve conter duplicatas, conforme a tolerância definida, e deve ser verificada regularmente.

7. **Valores Nulos**: A coluna `vl_renda_mensal` apresenta um percentual de nulos acima do esperado, o que deve ser investigado para garantir a integridade dos dados.

---

> **[AI_METADATA_STATUS: DRAFT]** — Documentação gerada por SLM. Requer validação humana pelo Data Steward responsável antes de uso em produção.