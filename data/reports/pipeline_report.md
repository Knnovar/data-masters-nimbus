# Pipeline Data Masters - Relatorio de Execucao
**Data:** 2026-05-28 21:49:39  |  **Run ID:** `run_20260528_214115_1b55e9`

---

## Resumo por Tabela

| Tabela | Cenário | Status | Linhas | Dups | Nulos (avg%) | Profiling (ms) | SLM (ms) | Score |
|--------|---------|--------|--------|------|--------------|----------------|----------|-------|
| `tb_clientes` | baseline | [PASS] PASS | 500 | 0 | 2.29% | 1305.7 | [OK] 66866.3 | **97.7** |
| `tb_transacoes` | baseline | [WARN] WARNING | 2,030 | 30 | 0.81% | 4144.8 | [OK] 53086.6 | **69.4** |
| `tb_contratos_credito` | baseline | [PASS] PASS | 300 | 0 | 0.0% | 942.8 | [OK] 60975.1 | **100.0** |
| `tb_clientes` | non_breaking | [WARN] WARNING | 500 | 0 | 7.32% | 1388.4 | [OK] 59267.2 | **67.7** |
| `tb_transacoes` | non_breaking | [WARN] WARNING | 2,030 | 30 | 0.73% | 4115.6 | [OK] 53117.3 | **69.5** |
| `tb_contratos_credito` | non_breaking | [PASS] PASS | 300 | 0 | 0.0% | 880.7 | [OK] 61303.3 | **100.0** |
| `tb_clientes` | breaking | [DLQ] DLQ | 500 | 0 | 0% | 0 | [SKIP] 0 | **20.0** |
| `tb_transacoes` | breaking | [WARN] WARNING | 2,030 | 30 | 0.8% | 4113.3 | [OK] 52935.1 | **69.4** |
| `tb_contratos_credito` | breaking | [PASS] PASS | 300 | 0 | 0.0% | 900.1 | [OK] 61037.3 | **100.0** |

---

## Qualidade Geral da Execução

- **Score médio:** `77.1/100`
- **Tabelas processadas:** 9
- **Com DLQ:** 1
- **Com WARNING:** 4
- **Documentadas por SLM:** 8

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
- [WARN] Novas colunas detectadas (non-breaking): ['cd_gestor_relacionamento']

### `tb_transacoes`
**Warnings:**
- [WARN] Manifesto em status DRAFT — documentacao gerada sem validacao humana. Execute: python -m src.manifest.manifest_validator --file <contrato.yaml> --steward 'Nome'
- [WARN] 30 duplicatas detectadas (1.5%)

### `tb_contratos_credito`
**Warnings:**
- [WARN] Manifesto em status DRAFT — documentacao gerada sem validacao humana. Execute: python -m src.manifest.manifest_validator --file <contrato.yaml> --steward 'Nome'

### `tb_clientes`
**Issues críticos:**
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