# Dicionário Técnico da Tabela `tb_clientes`

## Descrição Geral

A tabela `tb_clientes` é um cadastro mestre que contém informações sobre clientes, tanto pessoas físicas quanto jurídicas. Esta tabela é gerida pela equipe de dados cadastrais do banco.

### Versão e Propriedade
- **Versão**: 1.0.0
- **Proprietário**: squad-dados-cadastrais

## Colunas da Tabela

### `cd_cliente`
- **Tipo**: String (VARCHAR)
- **Negócio**: Identificador único do cliente.
- **Comportamento Esperado**: Não deve conter valores nulos e deve ser exclusivo para cada registro. Serve como chave primária.
- **Estatísticas Observadas**:
  - Percentual de Nulos: 0%
  - Contagem Única: 500
- **Anomalias**: Nenhuma observada.

### `nr_cpf_cnpj`
- **Tipo**: String (VARCHAR)
- **Negócio**: CPF para pessoas físicas ou CNPJ para empresas.
- **Comportamento Esperado**: Não deve conter valores nulos e deve ser exclusivo para cada registro.
- **Estatísticas Observadas**:
  - Percentual de Nulos: 0%
  - Contagem Única: 500
  - Valores Mínimo, Máximo e Médio: Verificados como numéricos (1283495651.0 a 98425103606.0).
- **Anomalias**: Os valores estão sendo tratados como strings, mas representam números.

### `nm_cliente`
- **Tipo**: String (VARCHAR)
- **Negócio**: Nome do cliente.
- **Comportamento Esperado**: Não deve conter valores nulos.
- **Estatísticas Observadas**:
  - Percentual de Nulos: 0%
  - Contagem Única: 495
  - Valores duplicados observados (ex.: "Gabriel Vargas" aparece duas vezes).
- **Anomalias**: Existem nomes repetidos, o que pode indicar registros duplicados não identificados pela chave primária.

### `dt_nascimento`
- **Tipo**: String (VARCHAR)
- **Negócio**: Data de nascimento do cliente.
- **Comportamento Esperado**: Pode conter valores nulos para clientes jurídicos.
- **Estatísticas Observadas**:
  - Percentual de Nulos: 0%
  - Contagem Única: 495
  - Valores duplicados observados (ex.: "1988-01-01" aparece duas vezes).
- **Anomalias**: Tratada como string, mas deveria ser do tipo data.

### `cd_segmento`
- **Tipo**: String (VARCHAR)
- **Negócio**: Segmentação do cliente (ex.: PJ_PEQUENO, PRIVATE).
- **Comportamento Esperado**: Não deve conter valores nulos.
- **Estatísticas Observadas**:
  - Percentual de Nulos: 0%
  - Contagem Única: 5
- **Anomalias**: Nenhuma observada.

### `cd_agencia`
- **Tipo**: String (VARCHAR)
- **Negócio**: Código da agência associada ao cliente.
- **Comportamento Esperado**: Não deve conter valores nulos.
- **Estatísticas Observadas**:
  - Percentual de Nulos: 0%
  - Contagem Única: 473
  - Valores duplicados observados (ex.: "AGENC-???" aparece 15 vezes).
- **Anomalias**: Exist

---
> **[AI_METADATA_STATUS: DRAFT]**