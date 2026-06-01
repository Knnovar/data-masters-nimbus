# Dicionário Técnico da Tabela `tb_contratos_credito_non_breaking`

## Visão Geral

A tabela `tb_contratos_credito_non_breaking` contém dados sobre contratos de crédito ativos e encerrados, conforme descrito no manifesto. Ela alimenta o Sistema de Controle de Risco (SCR) mensalmente e é gerida pela equipe `squad-credito`. A tabela está em formato SAS7BDAT com codificação Latin-1 e atualizações diárias.

### Contexto de Negócio

Os contratos incluem todos os produtos oferecidos pelo banco, como cartão de crédito, cheque especial, crédito pessoal, financiamento de veículo e consignado. O valor utilizado (`vl_utilizado`) pode exceder o limite aprovado (`vl_limite`) em até 15% para produtos com tolerância, como o cheque especial. Um contrato com status `EM_ATRASO` desencadeia uma cobrança automática após D+1.

### Regulamentação

A tabela possui tags regulatórias importantes: SCR, BACEN_4658 e LGPD, indicando que os dados são classificados como restritos e devem ser retidos por 10 anos. As colunas `vl_limite` e `vl_utilizado` são candidatas ao SCR.

## Colunas

### id_contrato
- **Tipo**: VARCHAR
- **Descrição**: Identificador único do contrato gerado pelo sistema de crédito.
- **Negócio**: Serve como chave primária, garantindo unicidade em 300 registros.
- **Estatísticas**: Sem valores nulos; todos os identificadores são únicos.

### cd_cliente
- **Tipo**: VARCHAR
- **Descrição**: Referência ao cliente na tabela `tb_clientes`.
- **Negócio**: Liga o contrato a um cliente específico.
- **Estatísticas**: 219 clientes únicos em 300 registros; alguns clientes têm múltiplos contratos.

### dt_contrato
- **Tipo**: VARCHAR (Deveria ser DATE)
- **Descrição**: Data de abertura do contrato.
- **Negócio**: Indica quando o contrato foi estabelecido.
- **Estatísticas**: 283 datas únicas; formato deve ser verificado para consistência.

### vl_limite
- **Tipo**: VARCHAR (Deveria ser FLOAT)
- **Descrição**: Limite de crédito aprovado em BRL.
- **Negócio**: Define o máximo que pode ser utilizado pelo cliente.
- **Estatísticas**: Valores variam de 790.74 a 99981.73; todos os valores são únicos.

### vl_utilizado
- **Tipo**: VARCHAR (Deveria ser FLOAT)
- **Descrição**: Saldo atual utilizado em BRL.
- **Negócio**: Mostra o uso atual do limite, podendo exceder para certos produtos.
- **Estatísticas**: Valores variam de 40.59 a 112380.03; todos os valores são únicos.

### tp_produto
- **Tipo**: VARCHAR
- **Descrição**: Tipo do produto de crédito (ex: CARTAO_CREDITO, CHEQUE_ESPECIAL).
- **Negócio**: Identifica o tipo de produto associado ao contrato.
- **Estatísticas**: 5 tipos únicos; `CREDITO_PESSOAL` e `FINANCIAMENTO_VEICULO` são os mais comuns.

### cd_status
- **Tipo**: VARCHAR
- **Descrição**: Status do contrato (ex: ATIVO, ENCERRADO).
- **Negócio**: Indica a situação atual do contrato.


---
> **[AI_METADATA_STATUS: DRAFT]**