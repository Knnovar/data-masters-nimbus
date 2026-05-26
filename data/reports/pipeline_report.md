# 📊 Pipeline Data Masters — Relatório de Execução
**Data:** 2026-05-26 19:52:10  |  **Run ID:** `run_20260526_195209_a34a55`

---

## Resumo por Tabela

| Tabela | Cenário | Status | Linhas | Dups | Nulos (avg%) | Profiling (ms) | SLM (ms) | Score |
|--------|---------|--------|--------|------|--------------|----------------|----------|-------|
| `tb_clientes` | baseline | 🟢 PASS | 500 | 0 | 2.29% | 14.2 | ⏭️ 0 | **97.7** |
| `tb_transacoes` | baseline | 🟡 WARNING | 2,030 | 30 | 0.81% | 19.9 | ⏭️ 0 | **69.4** |
| `tb_contratos_credito` | baseline | 🟢 PASS | 300 | 0 | 0.0% | 12.8 | ⏭️ 0 | **100.0** |

---

## Qualidade Geral da Execução

- **Score médio:** `89.0/100`
- **Tabelas processadas:** 3
- **Com DLQ:** 0
- **Com WARNING:** 1
- **Documentadas por SLM:** 0

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