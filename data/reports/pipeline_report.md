# Pipeline Projeto Nimbus - Relatorio de Execucao
**Data:** 2026-09-08 23:25:26  |  **Run ID:** `run_20260908_231442_7de358`

---

## Resumo por Tabela

| Tabela | Cenário | Status | Linhas | Dups | Nulos (avg%) | Profiling (ms) | SLM (ms) | Score |
|--------|---------|--------|--------|------|--------------|----------------|----------|-------|
| `tb_clientes` | baseline | [PASS] PASS | 500 | 0 | 2.29% | 1283.5 | [OK] 69126.8 | **94.8** |
| `tb_transacoes` | baseline | [WARN] WARNING | 2,030 | 30 | 0.81% | 4293.4 | [OK] 51948.0 | **86.0** |
| `tb_contratos_credito` | baseline | [PASS] PASS | 300 | 0 | 0.0% | 903.4 | [OK] 65300.7 | **100.0** |
| `tb_clientes` | baseline | [PASS] PASS | 500 | 0 | 0.0% | 16.6 | [OK] 62114.5 | **100.0** |
| `tb_transacoes` | baseline | [WARN] WARNING | 2,030 | 30 | 0.0% | 25.7 | [OK] 54588.5 | **94.1** |
| `tb_contratos_credito` | baseline | [PASS] PASS | 300 | 0 | 0.0% | 10.7 | [OK] 58992.9 | **100.0** |
| `tb_clientes` | baseline | [PASS] PASS | 500 | 0 | 0.0% | 6.2 | [OK] 65774.4 | **100.0** |
| `tb_transacoes` | baseline | [WARN] WARNING | 2,030 | 30 | 1.6% | 20.1 | [OK] 52612.6 | **92.1** |
| `tb_contratos_credito` | baseline | [PASS] PASS | 300 | 0 | 0.0% | 7.4 | [OK] 63884.6 | **100.0** |

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

> Linha rejeitada = valor preenchido fora do tipo declarado no Manifest. A linha inteira vai para `quarantine/reject_<tabela>.csv` com `_reject_columns`, `_reject_values` e `_reject_reason`; acima da tolerancia do contrato (`tolerancia.max_reject_pct`) a publicacao e bloqueada .

---

## Desempenho da SLM

| Tabela | Modelo | Wall (ms) | Carga (ms) | Prompt (Tok/ms) | Saida (tok/ms) | Tok/s | Cobertura | Truncado |
|--------|--------|-----------|------------|-----------------|----------------|-------|-----------|----------|
| `tb_clientes` | phi4 | 69,127 | 3 | 2487/1,061 | 1667/65,664 | **25.4** | 100.0% | nao |
| `tb_transacoes` | phi4 | 51,948 | 2 | 2175/910 | 1249/48,710 | **25.6** | 100.0% | nao |
| `tb_contratos_credito` | phi4 | 65,301 | 2 | 2718/6,420 | 1431/56,646 | **25.3** | 100.0% | nao |
| `tb_clientes` | phi4 | 62,114 | 2 | 2401/2,073 | 1475/57,880 | **25.5** | 100.0% | nao |
| `tb_transacoes` | phi4 | 54,588 | 2 | 2106/1,910 | 1288/50,261 | **25.6** | 100.0% | nao |
| `tb_contratos_credito` | phi4 | 58,993 | 2 | 2687/4,347 | 1330/52,433 | **25.4** | 100.0% | nao |
| `tb_clientes` | phi4 | 65,774 | 2 | 1941/640 | 1607/62,727 | **25.6** | 100.0% | nao |
| `tb_transacoes` | phi4 | 52,613 | 2 | 1795/653 | 1281/49,608 | **25.8** | 100.0% | nao |
| `tb_contratos_credito` | phi4 | 63,885 | 2 | 2494/1,025 | 1538/60,507 | **25.4** | 100.0% | nao |

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