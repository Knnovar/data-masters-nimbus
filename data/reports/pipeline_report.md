# Pipeline Projeto Nimbus - Relatorio de Execucao
**Data:** 2026-06-22 01:07:56  |  **Run ID:** `run_20260622_005302_e9f3d8`

---

## Resumo por Tabela

| Tabela | Cenário | Status | Linhas | Dups | Nulos (avg%) | Profiling (ms) | SLM (ms) | Score |
|--------|---------|--------|--------|------|--------------|----------------|----------|-------|
| `tb_clientes` | baseline | [PASS] PASS | 500 | 0 | 2.29% | 1280.1 | [OK] 47167.1 | **97.7** |
| `tb_transacoes` | baseline | [WARN] WARNING | 2,030 | 30 | 0.81% | 4028.5 | [OK] 34086.7 | **69.4** |
| `tb_contratos_credito` | baseline | [PASS] PASS | 300 | 0 | 0.0% | 909.6 | [OK] 34864.8 | **100.0** |
| `tb_clientes` | baseline | [PASS] PASS | 500 | 0 | 0.0% | 10.7 | [OK] 33759.6 | **100.0** |
| `tb_transacoes` | baseline | [WARN] WARNING | 2,030 | 30 | 0.0% | 24.6 | [OK] 33369.3 | **70.2** |
| `tb_contratos_credito` | baseline | [PASS] PASS | 300 | 0 | 0.0% | 10.2 | [OK] 33970.6 | **100.0** |
| `tb_clientes` | baseline | [PASS] PASS | 500 | 0 | 0.0% | 6.1 | [OK] 33068.0 | **100.0** |
| `tb_transacoes` | baseline | [WARN] WARNING | 2,030 | 30 | 1.6% | 10.3 | [OK] 32985.8 | **68.6** |
| `tb_contratos_credito` | baseline | [PASS] PASS | 300 | 0 | 0.0% | 7.4 | [OK] 33792.2 | **100.0** |
| `tb_clientes` | non_breaking | [WARN] WARNING | 500 | 0 | 8.3% | 1350.7 | [OK] 33956.6 | **66.7** |
| `tb_transacoes` | non_breaking | [WARN] WARNING | 2,030 | 30 | 0.68% | 4128.3 | [OK] 33649.4 | **69.5** |
| `tb_contratos_credito` | non_breaking | [PASS] PASS | 300 | 0 | 0.0% | 872.1 | [OK] 34065.1 | **100.0** |
| `tb_clientes` | non_breaking | [WARN] WARNING | 500 | 0 | 0.0% | 11.5 | [OK] 33810.7 | **75.0** |
| `tb_transacoes` | non_breaking | [WARN] WARNING | 2,030 | 30 | 0.0% | 24.5 | [OK] 33480.4 | **70.2** |
| `tb_contratos_credito` | non_breaking | [PASS] PASS | 300 | 0 | 0.0% | 9.6 | [OK] 34070.4 | **100.0** |
| `tb_clientes` | non_breaking | [PASS] PASS | 500 | 0 | 0.0% | 5.9 | [OK] 33105.8 | **100.0** |
| `tb_transacoes` | non_breaking | [WARN] WARNING | 2,030 | 30 | 1.52% | 10.4 | [OK] 33041.7 | **68.7** |
| `tb_contratos_credito` | non_breaking | [PASS] PASS | 300 | 0 | 0.0% | 7.3 | [OK] 33814.9 | **100.0** |
| `tb_clientes` | breaking | [DLQ] DLQ | 500 | 0 | 0% | 0 | [SKIP] 0 | **20.0** |
| `tb_transacoes` | breaking | [WARN] WARNING | 2,030 | 30 | 0.76% | 3959.8 | [OK] 33626.1 | **69.5** |
| `tb_contratos_credito` | breaking | [PASS] PASS | 300 | 0 | 0.0% | 864.5 | [OK] 34148.0 | **100.0** |
| `tb_clientes` | breaking | [DLQ] DLQ | 500 | 0 | 0% | 0 | [SKIP] 0 | **20.0** |
| `tb_transacoes` | breaking | [WARN] WARNING | 2,030 | 30 | 0.0% | 24.3 | [OK] 33453.3 | **70.2** |
| `tb_contratos_credito` | breaking | [PASS] PASS | 300 | 0 | 0.0% | 9.7 | [OK] 34014.7 | **100.0** |
| `tb_clientes` | breaking | [DLQ] DLQ | 500 | 0 | 0% | 0 | [SKIP] 0 | **20.0** |
| `tb_transacoes` | breaking | [WARN] WARNING | 2,030 | 30 | 1.54% | 10.3 | [OK] 33000.6 | **68.7** |
| `tb_contratos_credito` | breaking | [PASS] PASS | 300 | 0 | 0.0% | 7.4 | [OK] 33845.3 | **100.0** |

---

## Qualidade Geral da Execução

- **Score medio:** `78.7/100`
- **Tabelas processadas:** 27
- **Com DLQ:** 3
- **Com WARNING:** 11
- **Documentadas por SLM:** 24

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

### `tb_clientes`
**Warnings:**
- [WARN] Manifesto em status DRAFT — documentacao gerada sem validacao humana. Execute: python -m src.manifest.manifest_validator --file <contrato.yaml> --steward 'Nome'
- [WARN] Novas colunas detectadas (non-breaking): ['cd_gestor_relacionamento']

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
- [WARN] Novas colunas detectadas (non-breaking): ['cd_gestor_relacionamento']

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
**Issues criticos:**
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

### `tb_clientes`
**Issues criticos:**
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

### `tb_clientes`
**Issues criticos:**
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