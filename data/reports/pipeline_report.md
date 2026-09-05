# Pipeline Projeto Nimbus - Relatorio de Execucao
**Data:** 2026-09-05 19:57:18  |  **Run ID:** `run_20260905_195154_fc0f38`

---

## Resumo por Tabela

| Tabela | Cenário | Status | Linhas | Dups | Nulos (avg%) | Profiling (ms) | SLM (ms) | Score |
|--------|---------|--------|--------|------|--------------|----------------|----------|-------|
| `tb_clientes` | baseline | [PASS] PASS | 500 | 0 | 2.29% | 1278.2 | [OK] 70648.7 | **94.8** |
| `tb_transacoes` | baseline | [WARN] WARNING | 2,030 | 30 | 0.81% | 4277.9 | [OK] 60904.5 | **86.0** |
| `tb_contratos_credito` | baseline | [PASS] PASS | 300 | 0 | 0.0% | 895.1 | [OK] 56657.4 | **100.0** |

---

## Qualidade Geral da Execução

- **Score medio:** `93.6/100`
- **Tabelas processadas:** 3
- **Com DLQ:** 0
- **Com WARNING:** 1
- **Documentadas por SLM:** 3

---

## Score por Dimensao

| Tabela | Conformidade (40%) | Completude (25%) | Unicidade (20%) | Estabilidade (15%) | Score |
|--------|--------------------|------------------|-----------------|--------------------|-------|
| `tb_clientes` | 100.0 | 79.4 | 100.0 |  100.0 | **94.8** |
| `tb_transacoes` | 100.0 | 67.5 | 70.4 |  100.0 | **86.0** |
| `tb_contratos_credito` | 100.0 | 100.0 | 100.0 |  100.0 | **100.0** |

- ``tb_clientes` / **completeness** = 79.4: nulos em obrigatorias: 0.00% | anulaveis a 41% da tolerancia (25%)
- ``tb_transacoes` / **completeness** = 67.5: nulos em obrigatorias: 0.00% | anulaveis a 65% da tolerancia (10%)
- ``tb_transacoes` / **uniqueness** = 70.4: 30 duplicatas na PK ['id_transacao'] (1.48%)

---

## Desempenho da SLM

| Tabela | Modelo | Wall (ms) | Carga (ms) | Prompt (Tok/ms) | Saida (tok/ms) | Tok/s | Cobertura | Truncado |
|--------|--------|-----------|------------|-----------------|----------------|-------|-----------|----------|
| `tb_clientes` | phi4 | 70,649 | 2 | 2321/1,972 | 1724/66,494 | **25.9** | 100.0% | nao |
| `tb_transacoes` | phi4 | 60,904 | 2 | 2099/3,260 | 1444/55,230 | **26.1** | 100.0% | nao |
| `tb_contratos_credito` | phi4 | 56,657 | 2 | 2633/1,939 | 1361/52,507 | **25.9** | 100.0% | nao |

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

---
> AVISO: Toda documentacao gerada pela SLM possui status **[AI_METADATA_STATUS: DRAFT]**.
> Requer validação humana pelo Data Steward antes de uso em produção.