# Dicionário Técnico da Tabela `tb_clientes`

## Descrição Geral

A tabela `tb_clientes` é o cadastro mestre de clientes pessoa física e jurídica, gerenciada pela squad-dados-cadastrais. Ela contém informações essenciais para a identificação e segmentação dos clientes do banco.

### Versão
- **Versão:** 1.0.0

## Colunas da Tabela

### `cd_cliente`
- **Tipo:** String
- **Nullable:** Não
- **Propósito de Negócio:** Identificador único do cliente.
- **Comportamento Esperado:** Deve ser exclusivo e não nulo para cada registro.
- **Estatísticas Observadas:**
  - Percentual de Nulos: 0.0%
  - Contagem Única: 500
- **Anomalias:** Nenhuma.

### `nr_cpf_cnpj`
- **Tipo:** String
- **Nullable:** Não
- **Propósito de Negócio:** Número do CPF (pessoa física) ou CNPJ (pessoa jurídica).
- **Comportamento Esperado:** Deve ser único e não nulo.
- **Estatísticas Observadas:**
  - Percentual de Nulos: 0.0%
  - Contagem Única: 500
- **Anomalias:** Nenhuma.

### `nm_cliente`
- **Tipo:** String
- **Nullable:** Não
- **Propósito de Negócio:** Nome completo do cliente.
- **Comportamento Esperado:** Deve ser único, exceto em casos de nomes iguais.
- **Estatísticas Observadas:**
  - Percentual de Nulos: 0.0%
  - Contagem Única: 498
- **Anomalias:** Existem valores duplicados para alguns nomes.

### `dt_nascimento`
- **Tipo:** String (esperado Date)
- **Nullable:** Sim
- **Propósito de Negócio:** Data de nascimento do cliente.
- **Comportamento Esperado:** Deve ser uma data válida, permitindo nulos.
- **Estatísticas Observadas:**
  - Percentual de Nulos: 0.0%
  - Contagem Única: 495
- **Anomalias:** Valores duplicados e formato incorreto (string).

### `cd_segmento`
- **Tipo:** String
- **Nullable:** Não
- **Propósito de Negócio:** Segmentação do cliente (e.g., PJ_PEQUENO, PRIVATE).
- **Comportamento Esperado:** Deve ser um valor válido dentro dos segmentos definidos.
- **Estatísticas Observadas:**
  - Percentual de Nulos: 0.0%
  - Contagem Única: 5
- **Anomalias:** Nenhuma.

### `cd_agencia`
- **Tipo:** String
- **Nullable:** Não
- **Propósito de Negócio:** Código da agência bancária associada ao cliente.
- **Comportamento Esperado:** Deve ser um código válido e não nulo.
- **Estatísticas Observadas:**
  - Percentual de Nulos: 0.0%
  - Contagem Única: 473
- **Anomalias:** Existem valores incomuns como "AGENC-???".

### `vl_renda_mensal`
- **Tipo:** String (esperado Float)
- **Nullable:** Sim
- **Propósito de Negócio:** Renda mensal do cliente.
- **Comportamento Esperado:** Deve ser um valor numérico, permit

---
> **[AI_METADATA_STATUS: DRAFT]**