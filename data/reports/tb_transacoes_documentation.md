# Dicionário Técnico da Tabela `tb_transacoes`

## Informações do Contrato YAML
- **Tabela:** `tb_transacoes`
- **Descrição:** Movimentações financeiras de todos os canais de atendimento.
- **Proprietário:** `squad-transacoes`
- **Versão:** `2.3.1`
- **Status:** `DRAFT`
- **Fonte:**
  - **Sistema:** `SWITCH_TRANSACIONAL`
  - **Formato:** `csv`
  - **Codificação:** `utf-8`
  - **Sistema Operacional:** `unix`
  - **Frequência de Atualização:** `event_driven`
  - **Contato:** `squad-transacoes@banco.com.br`
- **Regulamentação:**
  - Tags: `BACEN_4658`, `PCI_DSS`
  - Classificação de Dados: `confidencial`
  - Retenção: `7 anos`
- **Steward:** `Data Steward Transacional`
  - **Email:** `steward-transacoes@banco.com.br`
- **Contexto Empresarial:** Registro de todas as movimentações financeiras por canal, com foco especial nas transações suspeitas para análise pelo motor antifraude. Nota: `cd_estabelecimento` pode ser nulo para compras online não identificadas, representando aproximadamente 6% do total.

## Descrição das Colunas

1. **id_transacao (string, nullable: false, primary_key: true):** UUID gerado pelo sistema transacional no momento da operação.
2. **cd_cliente (string, nullable: false):** Referência ao cliente encontrada em `tb_clientes`.
3. **dt_transacao (date, nullable: false):** Data da transação no fuso horário America/Sao_Paulo.
4. **vl_transacao (float, nullable: false):** Valor em BRL, positivo para débitos e negativo para estornos.
5. **tp_transacao (string, nullable: false):** Tipo da operação, com domínio: COMPRA, SAQUE, TED, PIX, PAGAMENTO_BOLETO.
6. **cd_estabelecimento (string, nullable: true):** CNPJ do estabelecimento, nulo para compras online não identificadas (~6%).
7. **fl_suspeita (boolean, nullable: false):** Flag do motor antifraude, indicando transações sob análise (~4% do volume).
8. **cd_canal (string, nullable: false):** Canal de origem, com domínio: APP, INTERNET, AGENCIA, ATM, POS.

## Estatísticas do Data Profiler

- **Total de Linhas:** 2029
- **Análise Detalhada:**
  - `b094bfed-9c45-4071-997d-726acb77cad9D54BB

---
> **[AI_METADATA_STATUS: DRAFT]**