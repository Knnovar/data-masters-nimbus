## Dicionário Técnico: Tb_contratos_credito

**Business Context:**
Contratos de produtos de crédito ativos e encerrados, que integram todos os produtos ofertados pelo banco. Esses contratos são essenciais para a preparação mensal do Sistema de Crédito (SCR).

**Dados de Contrato:**

1. `cd_cliente`: Código do cliente, referência ao cliente no sistema `tb_clientes`. Propósito: Identificar o cliente associado a cada contrato.
2. `dt_contrato`: Data de abertura do contrato. Propósito: Registrar quando o contrato foi estabelecido.
3. `vl_limite`: Limite de crédito aprovado, em BRL. Propósito: Determinar o valor máximo disponível para o produto de crédito.
4. `vl_utilizado`: Saldo utilizado atual, em BRL. Propósito: Monitorar o valor atualmente emprestado pelo cliente.
5. `tp_produto`: Tipo do produto de crédito (Carta, Cheque Especial, Crédito Pessoal, Financiamento Veículo, Consignado). Propósito: Classificar o tipo de produto de crédito.
6. `cd_status`: Status do contrato (Ativo, Encerrado, Em Atras, Renegociado). Propósito: Acompanhar o estado atual do contrato.
7. `dt_vencimento`: Data de vencimento da última parcela ou do contrato. Propósito: Estabelecer o prazo para o pagamento ou renegociação.
8. `nr_parcelas`: Número total de parcelas do contrato (1 para crédito rotativo). Propósito: Determinar o número de pagamentos a serem feitos.
9. `tx_juros_am`: Taxa de juros ao mês, em percentual. Propósito: Calcular os juros mensais a serem pagos pelo cliente.

**Regulatory Tags:**
- SCR
- BACEN 4658
- LGPD

**Data Classifications:**
- Restrito: Os dados são considerados sensíveis e devem ser tratados de acordo com as regulamentações de privacidade e seguroptionais.

**Retention Years:**
- 10 anos: Os dados devem ser mantidos por um período de dez anos, conforme regulamentação.

**Business Rules:**
- Para produtos com Cheque Especial, o valor utilizado pode exceder até 15% do limite aprovado.
- Quando o status do contrato é EM_ATRASO, uma cobrança automática é disparada após o primeiro dia de atraso.

**Statistics from Data Profiler:**

1. `cd_cliente`: Tipo VARCHAR, 0% de valores nulos, 299 identificadores únicos únicos.
2. `dt_contrato`: Tipo DATE, 0% de valores nulos, data única.
3. `vl_limite`: Tipo FLOAT, 0% de valores nulos, mínimo: 1065.12, má

---
> **[AI_METADATA_STATUS: DRAFT]**