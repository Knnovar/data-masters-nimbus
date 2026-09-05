# Pipeline Projeto Nimbus - Relatorio de Execucao
**Data:** 2026-09-05 00:29:53  |  **Run ID:** `run_20260905_002029_36eb51`

---

## Resumo por Tabela

| Tabela | Cenário | Status | Linhas | Dups | Nulos (avg%) | Profiling (ms) | SLM (ms) | Score |
|--------|---------|--------|--------|------|--------------|----------------|----------|-------|
| `tb_clientes` | baseline | [PASS] PASS | 500 | 0 | 2.29% | 1273.5 | [OK] 60541.6 | **94.8** |
| `tb_transacoes` | baseline | [WARN] WARNING | 2,030 | 30 | 0.81% | 4196.0 | [OK] 71187.9 | **86.0** |
| `tb_contratos_credito` | baseline | [PASS] PASS | 300 | 0 | 0.0% | 1073.9 | [OK] 61874.7 | **100.0** |
| `tb_clientes` | baseline | [PASS] PASS | 500 | 0 | 0.0% | 10.8 | [OK] 60627.8 | **60.0** |
| `tb_transacoes` | baseline | [WARN] WARNING | 2,030 | 30 | 0.0% | 24.8 | [OK] 55832.2 | **94.1** |
| `tb_contratos_credito` | baseline | [PASS] PASS | 300 | 0 | 0.0% | 9.9 | [OK] 61877.8 | **100.0** |
| `tb_clientes` | baseline | [PASS] PASS | 500 | 0 | 0.0% | 6.1 | [OK] 60032.6 | **100.0** |
| `tb_transacoes` | baseline | [WARN] WARNING | 2,030 | 30 | 1.6% | 10.5 | [OK] 49010.7 | **92.1** |
| `tb_contratos_credito` | baseline | [PASS] PASS | 300 | 0 | 0.0% | 7.3 | [OK] 55749.7 | **100.0** |

---

## Qualidade Geral da Execução

- **Score medio:** `91.9/100`
- **Tabelas processadas:** 9
- **Com DLQ:** 0
- **Com WARNING:** 3
- **Documentadas por SLM:** 9

---

## Score por Dimensao

| Tabela | Conformidade (40%) | Completude (25%) | Unicidade (20%) | Estabilidade (15%) | Score |
|--------|--------------------|------------------|-----------------|--------------------|-------|
| `tb_clientes` | 100.0 | 79.4 | 100.0 |  100.0 | **94.8** |
| `tb_transacoes` | 100.0 | 67.5 | 70.4 |  100.0 | **86.0** |
| `tb_contratos_credito` | 100.0 | 100.0 | 100.0 |  100.0 | **100.0** |
| `tb_clientes` | 0.0 | 100.0 | 100.0 |  100.0 | **60.0** |
| `tb_transacoes` | 100.0 | 100.0 | 70.4 |  100.0 | **94.1** |
| `tb_contratos_credito` | 100.0 | 100.0 | 100.0 |  100.0 | **100.0** |
| `tb_clientes` | 100.0 | 100.0 | 100.0 |  100.0 | **100.0** |
| `tb_transacoes` | 100.0 | 92.0 | 70.4 |  100.0 | **92.1** |
| `tb_contratos_credito` | 100.0 | 100.0 | 100.0 |  100.0 | **100.0** |

- ``tb_clientes` / **completeness** = 79.4: nulos em obrigatorias: 0.00% | anulaveis a 41% da tolerancia (25%)
- ``tb_transacoes` / **completeness** = 67.5: nulos em obrigatorias: 0.00% | anulaveis a 65% da tolerancia (10%)
- ``tb_transacoes` / **uniqueness** = 70.4: 30 duplicatas na PK ['id_transacao'] (1.48%)
- ``tb_clientes` / **conformity** = 0.0: tipo divergente do Manifest em vl_renda_mensal (17.8% de falha)
- ``tb_transacoes` / **uniqueness** = 70.4: 30 duplicatas na PK ['id_transacao'] (1.48%)
- ``tb_transacoes` / **completeness** = 92.0: nulos em obrigatorias: 0.00% | anulaveis a 16% da tolerancia (10%)
- ``tb_transacoes` / **uniqueness** = 70.4: 30 duplicatas na PK ['id_transacao'] (1.48%)

---

## Desempenho da SLM

| Tabela | Modelo | Wall (ms) | Carga (ms) | Prompt (Tok/ms) | Saida (tok/ms) | Tok/s | Cobertura | Truncado |
|--------|--------|-----------|------------|-----------------|----------------|-------|-----------|----------|
| `tb_clientes` | phi4 | 60,542 | 2 | 2320/958 | 1500/57,356 | **26.2** | 100.0% | sim |
| `tb_transacoes` | phi4 | 71,188 | 2 | 2093/12,321 | 1475/56,651 | **26.0** | 100.0% | nao |
| `tb_contratos_credito` | phi4 | 61,875 | 2 | 2629/1,917 | 1500/57,709 | **26.0** | 100.0% | sim |
| `tb_clientes` | phi4 | 60,628 | 2 | 2255/881 | 1500/57,375 | **26.1** | 100.0% | sim |
| `tb_transacoes` | phi4 | 55,832 | 2 | 2043/837 | 1381/52,576 | **26.3** | 100.0% | nao |
| `tb_contratos_credito` | phi4 | 61,878 | 2 | 2626/1,917 | 1500/57,735 | **26.0** | 100.0% | sim |
| `tb_clientes` | phi4 | 60,033 | 2 | 1891/620 | 1500/57,053 | **26.3** | 100.0% | sim |
| `tb_transacoes` | phi4 | 49,011 | 2 | 1745/621 | 1217/46,051 | **26.4** | 100.0% | nao |
| `tb_contratos_credito` | phi4 | 55,750 | 2 | 2439/1,757 | 1340/51,789 | **25.9** | 100.0% | nao |

> Compare modelos com `python show_metrics.py --models` (agrega todas as runs por `slm_model`).

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