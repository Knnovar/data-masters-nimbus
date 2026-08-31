# Dicionário Técnico da Tabela `tb_contratos_credito`

## Visão Geral

A tabela `tb_contratos_credito` armazena informações sobre contratos de produtos de crédito ativos e encerrados. Ela é gerida pela equipe `squad-credito` e está em versão `3.0.0`. O sistema de origem é o `SISTEMA_CREDITO_SAS`, e os dados são atualizados diariamente. A tabela é classificada como restrita e deve ser retenida por 10 anos, conforme as regulamentações `SCR`, `BACEN_4658` e `LGPD`.

## Colunas

### `id_contrato`
- **Tipo**: `string`
- **Nullable**: `false`
- **Descrição**: Identificador único do contrato gerado pelo sistema de crédito.
- **Propósito de Negócio**: Serve como chave primária para identificar cada contrato de forma única.
- **Comportamento Esperado**: Não deve conter valores nulos, garantindo a unicidade em todas as entradas.
- **Anomalias**: Nenhuma anomalia observada, já que `null_pct` é 0.0 e `unique_count` é 299.

### `cd_cliente`
- **Tipo**: `string`
- **Nullable**: `false`
- **Descrição**: Referência ao cliente em `tb_clientes`.
- **Propósito de Negócio**: Liga o contrato ao cliente correspondente.
- **Comportamento Esperado**: Não deve conter valores nulos, garantindo a integridade referencial com `tb_clientes`.
- **Anomalias**: Nenhuma anomalia observada, já que `null_pct` é 0.0 e `unique_count` é 299.

### `dt_contrato`
- **Tipo**: `date`
- **Nullable**: `false`
- **Descrição**: Data de abertura do contrato.
- **Propósito de Negócio**: Registra o início do contrato.
- **Comportamento Esperado**: Não deve conter valores nulos, refletindo a data exata de abertura.
- **Anomalias**: Nenhuma anomalia observada, já que `null_pct` é 0.0 e `unique_count` é 282.

### `vl_limite`
- **Tipo**: `float`
- **Nullable**: `false`
- **Descrição**: Limite de crédito aprovado em BRL.
- **Propósito de Negócio**: Define o valor máximo que pode ser utilizado pelo cliente.
- **Comportamento Esperado**: Não deve conter valores nulos, refletindo o limite aprovado.
- **Anomalias**: Nenhuma anomalia observada, já que `null_pct` é 0.0. Valores variam de 1065.12 a 99779.85 BRL.

### `vl_utilizado`
- **Tipo**: `float`
- **Nullable**: `false`
- **Descrição**: Saldo utilizado atual em BRL. Pode exceder `vl_limite` em produtos com tolerância.
- **Propósito de Negócio**: Monitora o uso atual do crédito pelo cliente.
- **Comportamento Esperado**: Não deve conter valores nulos, refletindo o saldo utilizado.
- **Anomalias**: Nenhuma anomalia observada, já que `null_pct` é 0.0. Valores variam de 92797.21 a 3817.24 BRL.

### `tp_produto`
- **Tipo**: `string`
- **Nullable**: `false`
- **Descrição**: Tipo do produto de crédito. Domínio: `CART

---
> **[AI_METADATA_STATUS: DRAFT]**