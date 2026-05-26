# 📊 Pipeline Data Masters — Relatório de Execução
**Data:** 2026-05-26 20:17:22  |  **Run ID:** `run_20260526_200100_fcd316`

---

## Resumo por Tabela

| Tabela | Cenário | Status | Linhas | Dups | Nulos (avg%) | Profiling (ms) | SLM (ms) | Score |
|--------|---------|--------|--------|------|--------------|----------------|----------|-------|
| `tb_clientes` | baseline | 🟢 PASS | 500 | 0 | 2.29% | 1246.4 | ✅ 335118.8 | **97.7** |
| `tb_transacoes` | baseline | 🟡 WARNING | 2,030 | 30 | 0.81% | 4505.4 | ✅ 299094.5 | **69.4** |
| `tb_contratos_credito` | baseline | 🟢 PASS | 300 | 0 | 0.0% | 858.8 | ✅ 334474.1 | **100.0** |

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