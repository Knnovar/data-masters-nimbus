# Pipeline Projeto Nimbus - Relatorio de Execucao
**Data:** 2026-08-31 17:01:20  |  **Run ID:** `run_20260831_165021_7cba0f`

---

## Resumo por Tabela

| Tabela | Cenário | Status | Linhas | Dups | Nulos (avg%) | Profiling (ms) | SLM (ms) | Score |
|--------|---------|--------|--------|------|--------------|----------------|----------|-------|
| `tb_clientes` | baseline | [PASS] PASS | 500 | 0 | 2.29% | 1271.5 | [OK] 33641.5 | **97.7** |
| `tb_transacoes` | baseline | [WARN] WARNING | 2,030 | 30 | 0.81% | 4055.6 | [OK] 33635.7 | **69.4** |
| `tb_contratos_credito` | baseline | [PASS] PASS | 300 | 0 | 0.0% | 870.0 | [OK] 34117.4 | **100.0** |
| `tb_clientes` | baseline | [PASS] PASS | 500 | 0 | 0.0% | 10.9 | [OK] 33695.9 | **100.0** |
| `tb_transacoes` | baseline | [WARN] WARNING | 2,030 | 30 | 0.0% | 25.1 | [OK] 33519.4 | **70.2** |
| `tb_contratos_credito` | baseline | [PASS] PASS | 300 | 0 | 0.0% | 9.9 | [OK] 34712.3 | **100.0** |
| `tb_clientes` | baseline | [PASS] PASS | 500 | 0 | 0.0% | 6.2 | [OK] 33963.5 | **100.0** |
| `tb_transacoes` | baseline | [WARN] WARNING | 2,030 | 30 | 1.6% | 10.4 | [OK] 33138.2 | **68.6** |
| `tb_contratos_credito` | baseline | [PASS] PASS | 300 | 0 | 0.0% | 7.7 | [OK] 36616.4 | **100.0** |

---

## Qualidade Geral da Execução

- **Score medio:** `89.5/100`
- **Tabelas processadas:** 9
- **Com DLQ:** 0
- **Com WARNING:** 3
- **Documentadas por SLM:** 9

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