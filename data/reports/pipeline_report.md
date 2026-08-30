# Pipeline Projeto Nimbus - Relatorio de Execucao
**Data:** 2026-08-30 16:37:05  |  **Run ID:** `run_20260830_163438_bcdc6a`

---

## Resumo por Tabela

| Tabela | Cenário | Status | Linhas | Dups | Nulos (avg%) | Profiling (ms) | SLM (ms) | Score |
|--------|---------|--------|--------|------|--------------|----------------|----------|-------|
| `tb_clientes` | baseline | [PASS] PASS | 500 | 0 | 2.29% | 1264.7 | [OK] 14042.0 | **97.7** |
| `tb_transacoes` | baseline | [WARN] WARNING | 2,030 | 30 | 0.81% | 4211.4 | [OK] 13659.4 | **69.4** |
| `tb_contratos_credito` | baseline | [PASS] PASS | 300 | 0 | 0.0% | 875.5 | [OK] 14687.8 | **100.0** |
| `tb_clientes` | baseline | [PASS] PASS | 500 | 0 | 0.0% | 10.9 | [OK] 13882.8 | **100.0** |
| `tb_transacoes` | baseline | [WARN] WARNING | 2,030 | 30 | 0.0% | 28.2 | [OK] 13495.0 | **70.2** |
| `tb_contratos_credito` | baseline | [PASS] PASS | 300 | 0 | 0.0% | 9.8 | [OK] 14762.9 | **100.0** |
| `tb_clientes` | baseline | [PASS] PASS | 500 | 0 | 0.0% | 6.3 | [OK] 8480.1 | **100.0** |
| `tb_transacoes` | baseline | [WARN] WARNING | 2,030 | 30 | 1.6% | 10.6 | [OK] 12913.3 | **68.6** |
| `tb_contratos_credito` | baseline | [PASS] PASS | 300 | 0 | 0.0% | 7.4 | [OK] 14292.1 | **100.0** |

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