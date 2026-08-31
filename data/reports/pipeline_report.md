# Pipeline Projeto Nimbus - Relatorio de Execucao
**Data:** 2026-08-31 00:13:37  |  **Run ID:** `run_20260831_000153_054995`

---

## Resumo por Tabela

| Tabela | Cenário | Status | Linhas | Dups | Nulos (avg%) | Profiling (ms) | SLM (ms) | Score |
|--------|---------|--------|--------|------|--------------|----------------|----------|-------|
| `tb_clientes` | baseline | [PASS] PASS | 500 | 0 | 2.29% | 1284.4 | [OK] 49252.1 | **97.7** |
| `tb_transacoes` | baseline | [WARN] WARNING | 2,030 | 30 | 0.81% | 4206.9 | [OK] 34430.0 | **69.4** |
| `tb_contratos_credito` | baseline | [PASS] PASS | 300 | 0 | 0.0% | 911.2 | [OK] 34914.1 | **100.0** |
| `tb_clientes` | baseline | [PASS] PASS | 500 | 0 | 0.0% | 11.3 | [OK] 33791.5 | **100.0** |
| `tb_transacoes` | baseline | [WARN] WARNING | 2,030 | 30 | 0.0% | 25.0 | [OK] 33762.4 | **70.2** |
| `tb_contratos_credito` | baseline | [PASS] PASS | 300 | 0 | 0.0% | 10.2 | [OK] 34266.0 | **100.0** |
| `tb_clientes` | baseline | [PASS] PASS | 500 | 0 | 0.0% | 7.9 | [OK] 33257.9 | **100.0** |
| `tb_transacoes` | baseline | [WARN] WARNING | 2,030 | 30 | 1.6% | 11.5 | [OK] 33229.9 | **68.6** |
| `tb_contratos_credito` | baseline | [PASS] PASS | 300 | 0 | 0.0% | 8.0 | [OK] 34018.4 | **100.0** |

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