# Pipeline Projeto Nimbus - Relatorio de Execucao
**Data:** 2026-09-08 00:08:31  |  **Run ID:** `run_20260907_235428_b62cd0`

---

## Resumo por Tabela

| Tabela | Cenário | Status | Linhas | Dups | Nulos (avg%) | Profiling (ms) | SLM (ms) | Score |
|--------|---------|--------|--------|------|--------------|----------------|----------|-------|
| `tb_clientes` | baseline | [PASS] PASS | 500 | 0 | 2.29% | 1248.0 | [OK] 74369.8 | **94.8** |
| `tb_transacoes` | baseline | [WARN] WARNING | 2,030 | 30 | 0.81% | 4077.5 | [OK] 51530.6 | **86.0** |
| `tb_contratos_credito` | baseline | [PASS] PASS | 300 | 0 | 0.0% | 876.5 | [OK] 73591.3 | **100.0** |
| `tb_clientes` | baseline | [PASS] PASS | 500 | 0 | 0.0% | 14.3 | [OK] 60444.2 | **60.0** |
| `tb_transacoes` | baseline | [WARN] WARNING | 2,030 | 30 | 0.0% | 36.1 | [OK] 47868.2 | **94.1** |
| `tb_contratos_credito` | baseline | [PASS] PASS | 300 | 0 | 0.0% | 9.7 | [OK] 74107.3 | **100.0** |
| `tb_clientes` | baseline | [PASS] PASS | 500 | 0 | 0.0% | 6.1 | [OK] 56482.8 | **100.0** |
| `tb_transacoes` | baseline | [WARN] WARNING | 2,030 | 30 | 1.6% | 10.4 | [OK] 46976.7 | **92.1** |
| `tb_contratos_credito` | baseline | [PASS] PASS | 300 | 0 | 0.0% | 8.0 | [OK] 73942.4 | **100.0** |

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
| `tb_clientes` | phi4 | 74,370 | 2 | 2463/1,746 | 1800/70,357 | **25.6** | 100.0% | sim |
| `tb_transacoes` | phi4 | 51,531 | 2 | 2147/882 | 1265/48,269 | **26.2** | 100.0% | nao |
| `tb_contratos_credito` | phi4 | 73,591 | 2 | 2680/1,104 | 1800/70,024 | **25.7** | 100.0% | sim |
| `tb_clientes` | phi4 | 60,444 | 2 | 2388/1,998 | 1464/56,238 | **26.0** | 100.0% | nao |
| `tb_transacoes` | phi4 | 47,868 | 2 | 2105/849 | 1173/44,662 | **26.3** | 100.0% | nao |
| `tb_contratos_credito` | phi4 | 74,107 | 2 | 2676/1,920 | 1796/69,954 | **25.7** | 100.0% | nao |
| `tb_clientes` | phi4 | 56,483 | 1 | 1937/643 | 1394/53,455 | **26.1** | 100.0% | nao |
| `tb_transacoes` | phi4 | 46,977 | 2 | 1795/629 | 1144/43,992 | **26.0** | 100.0% | nao |
| `tb_contratos_credito` | phi4 | 73,942 | 1 | 2486/1,759 | 1800/69,962 | **25.7** | 100.0% | sim |

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