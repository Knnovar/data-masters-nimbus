# 📊 Pipeline Data Masters — Relatório de Execução
**Data:** 2026-05-27 12:10:37  |  **Run ID:** `run_20260527_115447_357067`

---

## Resumo por Tabela

| Tabela | Cenário | Status | Linhas | Dups | Nulos (avg%) | Profiling (ms) | SLM (ms) | Score |
|--------|---------|--------|--------|------|--------------|----------------|----------|-------|
| `tb_clientes` | baseline | 🟢 PASS | 500 | 0 | 2.29% | 1277.6 | ✅ 328271.3 | **97.7** |
| `tb_transacoes` | baseline | 🟡 WARNING | 2,030 | 30 | 0.81% | 4127.6 | ✅ 290606.2 | **69.4** |
| `tb_contratos_credito` | baseline | 🟢 PASS | 300 | 0 | 0.0% | 878.5 | ✅ 317686.7 | **100.0** |

---

## Qualidade Geral da Execução

- **Score médio:** `89.0/100`
- **Tabelas processadas:** 3
- **Com DLQ:** 0
- **Com WARNING:** 1
- **Documentadas por SLM:** 3

---

## Detalhes por Tabela

### `tb_clientes`

### `tb_transacoes`
**Warnings:**
- ⚠️ 30 duplicatas detectadas (1.5%)

### `tb_contratos_credito`

---
> ⚠️ Toda documentação gerada pela SLM possui status **[AI_METADATA_STATUS: DRAFT]**.
> Requer validação humana pelo Data Steward antes de uso em produção.