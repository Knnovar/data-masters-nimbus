# Pipeline Projeto Nimbus - Relatorio de Execucao
**Data:** 2026-09-04 23:36:28  |  **Run ID:** `run_20260904_233053_725544`

---

## Resumo por Tabela

| Tabela | Cenário | Status | Linhas | Dups | Nulos (avg%) | Profiling (ms) | SLM (ms) | Score |
|--------|---------|--------|--------|------|--------------|----------------|----------|-------|
| `tb_clientes` | baseline | [PASS] PASS | 500 | 0 | 2.29% | 1274.0 | [OK] 34058.0 | **91.4** |
| `tb_transacoes` | baseline | [WARN] WARNING | 2,030 | 30 | 0.81% | 4172.2 | [OK] 34916.3 | **76.6** |
| `tb_contratos_credito` | baseline | [PASS] PASS | 300 | 0 | 0.0% | 877.2 | [OK] 35377.7 | **100.0** |
| `tb_clientes` | baseline | [PASS] PASS | 500 | 0 | 0.0% | 16.9 | [OK] 33744.2 | **100.0** |
| `tb_transacoes` | baseline | [WARN] WARNING | 2,030 | 30 | 0.0% | 25.9 | [OK] 33568.7 | **90.1** |
| `tb_contratos_credito` | baseline | [PASS] PASS | 300 | 0 | 0.0% | 10.2 | [OK] 34210.7 | **100.0** |
| `tb_clientes` | baseline | [PASS] PASS | 500 | 0 | 0.0% | 6.3 | [OK] 33246.7 | **100.0** |
| `tb_transacoes` | baseline | [WARN] WARNING | 2,030 | 30 | 1.6% | 11.5 | [OK] 33229.9 | **86.8** |
| `tb_contratos_credito` | baseline | [PASS] PASS | 300 | 0 | 0.0% | 7.5 | [OK] 34736.1 | **100.0** |

---

## Qualidade Geral da Execução

- **Score medio:** `93.9/100`
- **Tabelas processadas:** 9
- **Com DLQ:** 0
- **Com WARNING:** 3
- **Documentadas por SLM:** 9

---

## Score por Dimensao

| Tabela | Conformidade (40%) | Completude (25%) | Unicidade (20%) | Estabilidade (15%) | Score |
|--------|--------------------|------------------|-----------------|--------------------|-------|
| `tb_clientes` | n/d | 79.4 | 100.0 |  100.0 | **91.4** |
| `tb_transacoes` | n/d | 67.5 | 70.4 |  100.0 | **76.6** |
| `tb_contratos_credito` | n/d | 100.0 | 100.0 |  100.0 | **100.0** |
| `tb_clientes` | n/d | 100.0 | 100.0 |  100.0 | **100.0** |
| `tb_transacoes` | n/d | 100.0 | 70.4 |  100.0 | **90.1** |
| `tb_contratos_credito` | n/d | 100.0 | 100.0 |  100.0 | **100.0** |
| `tb_clientes` | n/d | 100.0 | 100.0 |  100.0 | **100.0** |
| `tb_transacoes` | n/d | 92.0 | 70.4 |  100.0 | **86.8** |
| `tb_contratos_credito` | n/d | 100.0 | 100.0 |  100.0 | **100.0** |

- ``tb_clientes` / **completeness** = 79.4: nulos em obrigatorias: 0.00% | anulaveis a 41% da tolerancia (25%)
- ``tb_transacoes` / **completeness** = 67.5: nulos em obrigatorias: 0.00% | anulaveis a 65% da tolerancia (10%)
- ``tb_transacoes` / **uniqueness** = 70.4: 30 duplicatas na PK ['id_transacao'] (1.48%)
- ``tb_transacoes` / **uniqueness** = 70.4: 30 duplicatas na PK ['id_transacao'] (1.48%)
- ``tb_transacoes` / **completeness** = 92.0: nulos em obrigatorias: 0.00% | anulaveis a 16% da tolerancia (10%)
- ``tb_transacoes` / **uniqueness** = 70.4: 30 duplicatas na PK ['id_transacao'] (1.48%)

---

## Desempenho da SLM

| Tabela | Modelo | Wall (ms) | Carga (ms) | Prompt (Tok/ms) | Saida (tok/ms) | Tok/s | Cobertura | Truncado |
|--------|--------|-----------|------------|-----------------|----------------|-------|-----------|----------|
| `tb_clientes` | phi4 | 34,058 | 2 | 2320/990 | 800/30,824 | **26.0** | 55.6% | sim |
| `tb_transacoes` | phi4 | 34,916 | 2 | 2085/1,473 | 800/31,182 | **25.7** | 87.5% | sim |
| `tb_contratos_credito` | phi4 | 35,378 | 2 | 2629/1,996 | 800/31,154 | **25.7** | 60.0% | sim |
| `tb_clientes` | phi4 | 33,744 | 2 | 2256/888 | 800/30,486 | **26.2** | 55.6% | sim |
| `tb_transacoes` | phi4 | 33,569 | 2 | 2055/862 | 800/30,396 | **26.3** | 87.5% | sim |
| `tb_contratos_credito` | phi4 | 34,211 | 2 | 2635/1,125 | 800/30,741 | **26.0** | 70.0% | sim |
| `tb_clientes` | phi4 | 33,247 | 2 | 1886/635 | 800/30,257 | **26.4** | 66.7% | sim |
| `tb_transacoes` | phi4 | 33,230 | 2 | 1751/625 | 800/30,273 | **26.4** | 87.5% | sim |
| `tb_contratos_credito` | phi4 | 34,736 | 2 | 2436/1,001 | 800/31,418 | **25.5** | 60.0% | sim |

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