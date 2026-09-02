## Dicionário Técnico Estruturado em Markdown

### Tabela: `tb_transacoes`

#### Propósito de Negócio
- **Registro de todas as movimentações financeiras por canal**, com foco especial em transações suspeitas para análise pelo motor antifraude.

#### Owner
- `squad-transacoes`

#### Versão do Manifesto
- **Versão:** 2.3.1

#### Desenvolvedor
- **Nome do Steward:** Data Steward Transacional
- **Email:** steward-transacoes@banco.com.br

#### Informações Regulatórias
- **Tags Regulatórios:** BACEN_4658, PCI_DSS
- **Classificação de Dados:** Confidencial
- **Retenção de Dados:** 7 anos

#### Descrição das Colunas

1. `cd_transacao` (cd_estabelecimento):
   - **Tipo:** VARCHAR
   - **Nullabilidade:** Não permitido
   - **Propósito:** UUID gerado pelo sistema transacional no momento da operação.
   - **Observação:** Nulo para aproximadamente 6% das transações, indicando compras online não identificadas.

2. `cd_cliente` (cd_estabelecimento):
   - **Tipo:** VARCHAR
  0. **Nullabilidade:** Não permitido
   - **Propósito:** Referência ao cliente em `tb_clientes`.

3. `dt_transacao` (dt_transacao):
   - **Tipo:** DATE
   - **Nullabilidade:** Não permitido
   - **Propósito:** Data da transação no fuso horário America/Sao_Paulo.

4. `vl_transacao` (vl_transacao):
   - **Tipo:** FLOAT
   - **Nullabilidade:** Não permitido
   - **Propósito:** Valor em BRL. Positivo para débitos, negativo para estornos.

5. `tp_transacao` (tp_transacao):
   - **Tipo:** VARCHAR
   - **Nullabilidade:** Não permitido
   - **Propósito:** Tipo da operação, dominio: COMPRA, SAQUE, TED, PIX, PAGAMENTO_BOLETO.

6. `fl_suspeita` (fl_suspeita):
   - **Tipo:** BOOLEAN
   - **Nullabilidade:** Não permitido
   - **Propósito:** Flag do motor antifraude. True indica transação em análise (aproximadamente 4% do volume).

7. `cd_canal` (cd_canal):
   - **Tipo:** VARCHAR
   - **Nullabilidade:** Não permitido
   - **Propósito:** Canal de origem: APP, INTERNET, AGENCIA, ATM, POS.

#### Estatísticas do Data Profiler

| Coluna           | dtype | Null Pct | Unique Count | Top Values (Top 3)                                                                                                                

---
> **[AI_METADATA_STATUS: DRAFT]**