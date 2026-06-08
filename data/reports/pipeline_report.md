# Pipeline Data Masters - Relatorio de Execucao
**Data:** 2026-06-01 11:33:44  |  **Run ID:** `run_20260601_112422_fcb958_breaking`

---

## Resumo por Tabela

| Tabela | Cenário | Status | Linhas | Dups | Nulos (avg%) | Profiling (ms) | SLM (ms) | Score |
|--------|---------|--------|--------|------|--------------|----------------|----------|-------|
| `tb_clientes` | breaking | [DLQ] DLQ | 500 | 0 | 0% | 0 | [SKIP] 0 | **20.0** |
| `tb_transacoes` | breaking | [WARN] WARNING | 2,030 | 30 | 0.8% | 4166.4 | [OK] 58163.2 | **69.4** |
| `tb_contratos_credito` | breaking | [PASS] PASS | 300 | 0 | 0.0% | 898.7 | [OK] 67879.0 | **100.0** |

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
- [ERR] Colunas obrigatórias ausentes: ['cd_agencia']
**Warnings:**
- [WARN] Manifesto em status DRAFT — documentacao gerada sem validacao humana. Execute: python -m src.manifest.manifest_validator --file <contrato.yaml> --steward 'Nome'

### `tb_transacoes`
**Warnings:**
- [WARN] Manifesto em status DRAFT — documentacao gerada sem validacao humana. Execute: python -m src.manifest.manifest_validator --file <contrato.yaml> --steward 'Nome'
- [WARN] 30 duplicatas detectadas (1.5%)

### `tb_contratos_credito`
**Warnings:**
- [WARN] Manifesto em status DRAFT — documentacao gerada sem validacao humana. Execute: python -m src.manifest.manifest_validator --file <contrato.yaml> --steward 'Nome'

---
> AVISO: Toda documentacao gerada pela SLM possui status **[AI_METADATA_STATUS: DRAFT]**.
> Requer validação humana pelo Data Steward antes de uso em produção.