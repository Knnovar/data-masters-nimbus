# Dicionário Técnico da Tabela `tb_clientes`

## Visão Geral

A tabela `tb_clientes` é o cadastro mestre de clientes pessoa física e jurídica, utilizada por todos os produtos de crédito e relacionamento do banco. A segmentação (`cd_segmento`) determina o produto oferecido e o gestor responsável. A tabela é atualizada diariamente pelo batch noturno do sistema CORE_BANCARIO_TOTVS.

## Colunas

### `cd_cliente`
- **Tipo**: `VARCHAR`
- **Nullable**: Não
- **Descrição**: Código único do cliente no sistema legado, gerado sequencialmente pelo CORE_BANCARIO.
- **Comportamento Esperado**: Cada cliente possui um código único. Não há valores nulos e todos os códigos são distintos.
- **Estatísticas**: 500 valores únicos, sem valores nulos.

### `nr_cpf_cnpj`
- **Tipo**: `VARCHAR`
- **Nullable**: Não
- **Descrição**: CPF (11 dígitos) ou CNPJ (14 dígitos) sem máscara.
- **Comportamento Esperado**: Sempre preenchido, sem valores nulos. Sensível conforme LGPD.
- **Estatísticas**: 500 valores únicos, sem valores nulos. Sensível, valores mascarados com padrão "99999999999".
- **Anomalias**: Nenhuma.

### `nm_cliente`
- **Tipo**: `VARCHAR`
- **Nullable**: Não
- **Descrição**: Nome completo do cliente conforme cadastro na Receita Federal.
- **Comportamento Esperado**: Sempre preenchido, sem valores nulos. Sensível conforme LGPD.
- **Estatísticas**: 496 valores únicos, sem valores nulos. Sensível, valores mascarados com padrões variados.
- **Anomalias**: 4 duplicatas observadas.

### `dt_nascimento`
- **Tipo**: `VARCHAR`
- **Nullable**: Sim
- **Descrição**: Data de nascimento. Nula para clientes PJ.
- **Comportamento Esperado**: Pode ser nulo para clientes PJ. Sensível conforme LGPD.
- **Estatísticas**: 495 valores únicos, sem valores nulos. Sensível, valores mascarados com padrão "9999-99-99".
- **Anomalias**: 5 duplicatas observadas.

### `cd_segmento`
- **Tipo**: `VARCHAR`
- **Nullable**: Não
- **Descrição**: Segmento de relacionamento. Domínio: VAREJO, PRIME, PRIVATE, PJ_PEQUENO, PJ_MEDIO.
- **Comportamento Esperado**: Sempre preenchido, sem valores nulos. Deve seguir regras de negócio para renda mensal.
- **Estatísticas**: 5 valores únicos, sem valores nulos.
- **Anomalias**: Verificar se `vl_renda_mensal` está nulo para `PJ_PEQUENO` e `PJ_MEDIO`.

### `cd_agencia`
- **Tipo**: `VARCHAR`
- **Nullable**: Não
- **Descrição**: Código numérico de 4 dígitos da agência de relacionamento principal.
- **Comportamento Esperado**: Sempre preenchido, sem valores nulos.
- **Estatísticas**: 473 valores únicos, sem valores nulos.
- **Anomalias**: 27 duplicatas observadas.

### `vl_renda_mensal`
- **Tipo**: `VARCHAR`
- **Nullable**: Sim
- **Descrição**: Renda mensal declarada em BRL. Nula para clientes PJ.
- **Comportamento Esperado**: Pode ser nulo para clientes PJ. Sensível conforme SCR.
- **Estatísticas**: 397 valores únicos, 20.6% de valores nulos.
- **Anomalias**: Verificar se está nulo para `cd_segmento` em `PJ_PEQUENO` e `PJ_MEDIO`.

### `fl_ativo`
- **Tipo**: `VARCHAR`
- **Nullable**: Não
- **Descrição**: Indica se o cliente possui relacionamento ativo com o banco.
- **Comportamento Esperado**: Sempre preenchido, sem valores nulos.
- **Estatísticas**: 2 valores únicos (True e False).
- **Anomalias**: Nenhuma.

### `dt_cadastro`
- **Tipo**: `VARCHAR`
- **Nullable**: Não
- **Descrição**: Data de abertura do cadastro no sistema.
- **Comportamento Esperado**: Sempre preenchido, sem valores nulos.
- **Estatísticas**: 462 valores únicos, sem valores nulos.
- **Anomalias**: 38 duplicatas observadas.

## Considerações Regulatórias

- **LGPD**: Dados sensíveis como `nr_cpf_cnpj`, `nm_cliente` e `dt_nascimento` estão sujeitos a regulamentações de proteção de dados.
- **BACEN 4658**: A tabela deve ser mantida conforme as diretrizes do Banco Central.
- **Classificação de Dados**: Confidencial, com retenção de 10 anos.

## Pontos de Atenção

1. **Duplicatas**: Verificar duplicatas em `nm_cliente`, `dt_nascimento`, `cd_agencia` e `dt_cadastro`.
2. **Valores Nulos**: `vl_renda_mensal` tem 20.6% de valores nulos; verificar se está correto para `PJ_PEQUENO` e `PJ_MEDIO`.
3. **Regras de Negócio**: Assegurar que `vl_renda_mensal` está nulo para `cd_segmento` em `PJ_PEQUENO` e `PJ_MEDIO`.
4. **Compliance**: Manter a conformidade com LGPD e BACEN 4658.

---
> **[AI_METADATA_STATUS: DRAFT]** — Documentação gerada por SLM. Requer validação humana pelo Data Steward responsável antes de uso em produção.