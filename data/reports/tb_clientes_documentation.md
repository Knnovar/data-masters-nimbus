# Dicionário Técnico da Tabela `tb_clientes`

## Visão Geral

A tabela `tb_clientes` é um cadastro mestre de clientes pessoa física e jurídica. Ela é utilizada por todos os produtos de crédito e relacionamento do banco. A segmentação dos clientes determina o produto oferecido e o gestor responsável. A tabela é atualizada diariamente pelo batch noturno do sistema CORE_BANCARIO_TOTVS.

## Colunas

### `cd_cliente`
- **Tipo**: String
- **Nullable**: Não
- **Descrição**: Código único do cliente no sistema legado. Gerado sequencialmente pelo CORE_BANCARIO.
- **Comportamento Esperado**: Cada cliente deve ter um código único. Não deve haver valores nulos ou duplicados.
- **Estatísticas**:
  - Percentual de nulos: 0.0%
  - Contagem única: 500
- **Anomalias**: Nenhuma observada.

### `nr_cpf_cnpj`
- **Tipo**: String
- **Nullable**: Não
- **Descrição**: CPF (11 dígitos) ou CNPJ (14 dígitos) sem máscara.
- **Comportamento Esperado**: Deve conter um CPF ou CNPJ válido e único para cada cliente.
- **Estatísticas**:
  - Percentual de nulos: 0.0%
  - Contagem única: 500
  - Sensível: Sim
  - Faixa: `[MASCARADO]`
- **Anomalias**: Nenhuma observada.
- **Implicações de Compliance**: Deve ser tratado conforme LGPD devido à sua natureza sensível.

### `nm_cliente`
- **Tipo**: String
- **Nullable**: Não
- **Descrição**: Nome completo do cliente conforme cadastro na Receita Federal.
- **Comportamento Esperado**: Deve conter o nome completo do cliente.
- **Estatísticas**:
  - Percentual de nulos: 0.0%
  - Contagem única: 499
  - Sensível: Sim
- **Anomalias**: 1 duplicata observada.
- **Implicações de Compliance**: Deve ser tratado conforme LGPD devido à sua natureza sensível.

### `dt_nascimento`
- **Tipo**: String
- **Nullable**: Sim
- **Descrição**: Data de nascimento. Nula para clientes PJ.
- **Comportamento Esperado**: Deve conter a data de nascimento para clientes PF. Deve ser nula para clientes PJ.
- **Estatísticas**:
  - Percentual de nulos: 0.0%
  - Contagem única: 495
  - Sensível: Sim
- **Anomalias**: Nenhuma observada.
- **Implicações de Compliance**: Deve ser tratado conforme LGPD devido à sua natureza sensível.

### `cd_segmento`
- **Tipo**: String
- **Nullable**: Não
- **Descrição**: Segmento de relacionamento. Dominio: VAREJO, PRIME, PRIVATE, PJ_PEQUENO, PJ_MEDIO.
- **Comportamento Esperado**: Deve conter um valor válido do domínio especificado.
- **Estatísticas**:
  - Percentual de nulos: 0.0%
  - Contagem única: 5
- **Anomalias**: Nenhuma observada.
- **Regras de Negócio**:
  - PRIME: `vl_renda_mensal >= 10000`
  - PRIVATE: `vl_renda_mensal >= 30000`
  - Sempre nulo para `cd_segmento` IN (PJ_PEQUENO, PJ_MEDIO)

### `cd_agencia`
- **Tipo**: String
- **Nullable**: Não
- **Descrição**: Código numérico de 4 dígitos da agência de relacionamento principal.
- **Comportamento Esperado**: Deve conter um código de agência válido.
- **Estatísticas**:
  - Percentual de nulos: 0.0%
  - Contagem única: 473
- **Anomalias**: 27 duplicatas observadas.

### `vl_renda_mensal`
- **Tipo**: String
- **Nullable**: Sim
- **Descrição**: Renda mensal declarada em BRL. Nula para clientes PJ.
- **Comportamento Esperado**: Deve conter a renda mensal para clientes PF. Deve ser nula para clientes PJ.
- **Estatísticas**:
  - Percentual de nulos: 0.0%
  - Contagem única: 398
- **Anomalias**: 103 valores `nan` observados.
- **Implicações de Compliance**: Candidato a SCR (Sensitive Content Review).

### `fl_ativo`
- **Tipo**: String
- **Nullable**: Não
- **Descrição**: Indica se o cliente possui relacionamento ativo com o banco.
- **Comportamento Esperado**: Deve ser `True` ou `False`.
- **Estatísticas**:
  - Percentual de nulos: 0.0%
  - Contagem única: 2
- **Anomalias**: Nenhuma observada.

### `dt_cadastro`
- **Tipo**: String
- **Nullable**: Não
- **Descrição**: Data de abertura do cadastro no sistema.
- **Comportamento Esperado**: Deve conter a data de cadastro do cliente.
- **Estatísticas**:
  - Percentual de nulos: 0.0%
  - Contagem única: 462
- **Anomalias**: Nenhuma observada.

## Implicações de Compliance

- **LGPD**: A tabela contém dados sensíveis como CPF/CNPJ, nome e data de nascimento, que devem ser tratados conforme a Lei Geral de Proteção de Dados.
- **BACEN 4658**: A tabela deve ser mantida conforme as diretrizes do Banco Central do Brasil.
- **Data Classification**: Confidencial
- **Retenção**: 10 anos

## Pontos de Atenção

1. **Duplicatas**: Observadas nas colunas `nm_cliente` e `cd_agencia`.
2. **Valores `nan`**: Observados na coluna `vl_renda_mensal`.
3. **Compliance**: A tabela contém dados sensíveis que devem ser tratados conforme LGPD e BACEN 4658.
4. **Regras de Negócio**: Verificar a consistência das regras de negócio relacionadas ao segmento e renda mensal.
5. **Atualização Diária**: Garantir que o processo de atualização diária esteja funcionando corretamente para manter a integridade dos dados.

---
> **[AI_METADATA_STATUS: DRAFT]** — Documentação gerada por SLM. Requer validação humana pelo Data Steward responsável antes de uso em produção.