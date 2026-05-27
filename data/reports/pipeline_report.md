# 📊 Pipeline Data Masters — Relatório de Execução
**Data:** 2026-05-26 20:57:11  |  **Run ID:** `run_20260526_204608_27d455`

---

## Resumo por Tabela

| Tabela | Cenário | Status | Linhas | Dups | Nulos (avg%) | Profiling (ms) | SLM (ms) | Score |
|--------|---------|--------|--------|------|--------------|----------------|----------|-------|
| `tb_clientes` | breaking | 🔴 DLQ | 500 | 0 | 0% | 0 | ⏭️ 0 | **20.0** |
| `tb_transacoes` | breaking | 🟡 WARNING | 2,030 | 30 | 0.81% | 4167.7 | ✅ 328812.9 | **69.4** |
| `tb_contratos_credito` | breaking | 🟢 PASS | 300 | 0 | 0.0% | 924.5 | ✅ 324681.5 | **100.0** |

---

## Qualidade Geral da Execução

- **Score médio:** `63.1/100`
- **Tabelas processadas:** 3
- **Com DLQ:** 1
- **Com WARNING:** 1
- **Documentadas por SLM:** 2

---

## Detalhes por Tabela

### `tb_clientes`
**Issues críticos:**
- ❌ Colunas obrigatórias ausentes: ['cd_agencia']

### `tb_transacoes`
**Warnings:**
- ⚠️ 30 duplicatas detectadas (1.5%)

### `tb_contratos_credito`

---
> ⚠️ Toda documentação gerada pela SLM possui status **[AI_METADATA_STATUS: DRAFT]**.
> Requer validação humana pelo Data Steward antes de uso em produção.