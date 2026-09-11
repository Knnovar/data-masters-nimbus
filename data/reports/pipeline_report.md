# Pipeline Projeto Nimbus - Relatorio de Execucao
**Data:** 2026-09-11 17:57:41  |  **Run ID:** `run_20260911_174314_628a80`

---

## Resumo por Tabela

| Tabela | Cenário | Status | Linhas | Dups | Nulos (avg%) | Profiling (ms) | SLM (ms) | Score |
|--------|---------|--------|--------|------|--------------|----------------|----------|-------|
| `tb_clientes` | baseline | [PASS] PASS | 500 | 0 | 2.29% | 1235.0 | [OK] 72340.9 | **94.8** |
| `tb_transacoes` | baseline | [WARN] WARNING | 2,030 | 30 | 0.81% | 4081.8 | [OK] 52407.6 | **86.0** |
| `tb_contratos_credito` | baseline | [PASS] PASS | 300 | 0 | 0.0% | 948.1 | [OK] 73221.5 | **100.0** |
| `tb_clientes` | baseline | [PASS] PASS | 500 | 0 | 0.0% | 11.0 | [OK] 58075.0 | **100.0** |
| `tb_transacoes` | baseline | [WARN] WARNING | 2,030 | 30 | 0.0% | 24.6 | [OK] 53726.4 | **94.1** |
| `tb_contratos_credito` | baseline | [PASS] PASS | 300 | 0 | 0.0% | 10.5 | [OK] 61972.6 | **100.0** |
| `tb_clientes` | baseline | [PASS] PASS | 500 | 0 | 0.0% | 6.0 | [OK] 50915.7 | **100.0** |
| `tb_transacoes` | baseline | [WARN] WARNING | 2,030 | 30 | 1.6% | 10.5 | [OK] 54974.6 | **92.1** |
| `tb_contratos_credito` | baseline | [PASS] PASS | 300 | 0 | 0.0% | 7.4 | [OK] 64923.6 | **100.0** |

---

## Qualidade Geral da Execução

- **Score medio:** `96.3/100`
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
| `tb_clientes` | 100.0 | 100.0 | 100.0 |  100.0 | **100.0** |
| `tb_transacoes` | 100.0 | 100.0 | 70.4 |  100.0 | **94.1** |
| `tb_contratos_credito` | 100.0 | 100.0 | 100.0 |  100.0 | **100.0** |
| `tb_clientes` | 100.0 | 100.0 | 100.0 |  100.0 | **100.0** |
| `tb_transacoes` | 100.0 | 92.0 | 70.4 |  100.0 | **92.1** |
| `tb_contratos_credito` | 100.0 | 100.0 | 100.0 |  100.0 | **100.0** |

- ``tb_clientes` / **completeness** = 79.4: nulos em obrigatorias: 0.00% | anulaveis a 41% da tolerancia (25%)
- ``tb_transacoes` / **completeness** = 67.5: nulos em obrigatorias: 0.00% | anulaveis a 65% da tolerancia (10%)
- ``tb_transacoes` / **uniqueness** = 70.4: 30 duplicatas na PK ['id_transacao'] (1.48%)
- ``tb_transacoes` / **uniqueness** = 70.4: 30 duplicatas na PK ['id_transacao'] (1.48%)
- ``tb_transacoes` / **completeness** = 92.0: nulos em obrigatorias: 0.00% | anulaveis a 16% da tolerancia (10%)
- ``tb_transacoes` / **uniqueness** = 70.4: 30 duplicatas na PK ['id_transacao'] (1.48%)

---

## Gate de Tipagem (Manifest soberano)

| Tabela | Cenario | Publicacao | Linhas rejeitadas | % | Tolerancia | Colunas |
|--------|---------|------------|-------------------|---|------------|---------|
| `tb_transacoes` | baseline | PASS_WITH_REJECTS | 30 | 1.48% | 2.00% | - |
| `tb_transacoes` | baseline | PASS_WITH_REJECTS | 30 | 1.48% | 2.00% | - |
| `tb_transacoes` | baseline | PASS_WITH_REJECTS | 30 | 1.48% | 2.00% | - |

> Linha rejeitada = valor preenchido fora do tipo declarado no Manifest. A linha inteira vai para `quarantine/reject_<tabela>.csv` com `_reject_columns`, `_reject_values` e `_reject_reason`; acima da tolerancia do contrato (`tolerance.max_reject_pct`) a publicacao e bloqueada.

---

## Desempenho da SLM

| Tabela | Modelo | Wall (ms) | Carga (ms) | Prompt (Tok/ms) | Saida (tok/ms) | Tok/s | Cobertura | Truncado |
|--------|--------|-----------|------------|-----------------|----------------|-------|-----------|----------|
| `tb_clientes` | phi4 | 72,341 | 2 | 2475/2,077 | 1767/68,051 | **26.0** | 100.0% | nao |
| `tb_transacoes` | phi4 | 52,408 | 2 | 2152/3,443 | 1225/46,769 | **26.2** | 100.0% | nao |
| `tb_contratos_credito` | phi4 | 73,222 | 2 | 2686/1,925 | 1783/69,005 | **25.8** | 100.0% | nao |
| `tb_clientes` | phi4 | 58,075 | 2 | 2402/2,021 | 1389/53,840 | **25.8** | 100.0% | nao |
| `tb_transacoes` | phi4 | 53,726 | 2 | 2106/873 | 1310/50,434 | **26.0** | 100.0% | nao |
| `tb_contratos_credito` | phi4 | 61,973 | 2 | 2686/1,916 | 1485/57,806 | **25.7** | 100.0% | nao |
| `tb_clientes` | phi4 | 50,916 | 2 | 1949/624 | 1259/47,938 | **26.3** | 100.0% | nao |
| `tb_transacoes` | phi4 | 54,975 | 2 | 1801/621 | 1355/52,018 | **26.0** | 100.0% | nao |
| `tb_contratos_credito` | phi4 | 64,924 | 2 | 2494/1,763 | 1548/60,944 | **25.4** | 100.0% | nao |

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