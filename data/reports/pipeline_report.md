# Pipeline Data Masters - Relatorio de Execucao
**Data:** 2026-05-28 00:49:08  |  **Run ID:** `run_20260528_004826_81ffca`

---

## Resumo por Tabela

| Tabela | Cenário | Status | Linhas | Dups | Nulos (avg%) | Profiling (ms) | SLM (ms) | Score |
|--------|---------|--------|--------|------|--------------|----------------|----------|-------|
| `tb_clientes` | baseline | [PASS] PASS | 500 | 0 | 2.29% | 4914.6 | [SKIP] 0 | **97.7** |
| `tb_transacoes` | baseline | [WARN] WARNING | 2,030 | 30 | 0.81% | 16562.9 | [SKIP] 0 | **69.4** |
| `tb_contratos_credito` | baseline | [PASS] PASS | 300 | 0 | 0.0% | 3769.6 | [SKIP] 0 | **100.0** |

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