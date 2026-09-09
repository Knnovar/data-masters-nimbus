# Pipeline Projeto Nimbus - Relatorio de Execucao
**Data:** 2026-09-08 21:45:46  |  **Run ID:** `run_20260908_214224_70c51e`

---

## Resumo por Tabela

| Tabela | Cenário | Status | Linhas | Dups | Nulos (avg%) | Profiling (ms) | SLM (ms) | Score |
|--------|---------|--------|--------|------|--------------|----------------|----------|-------|
| `tb_clientes` | type_drift | [PASS] PASS | 500 | 0 | 2.13% | 716.8 | [OK] 67126.0 | **55.2** |
| `tb_transacoes` | type_drift | [WARN] WARNING | 2,030 | 30 | 0.84% | 4081.9 | [OK] 49831.5 | **85.7** |
| `tb_contratos_credito` | type_drift | [PASS] PASS | 300 | 0 | 0.0% | 894.4 | [OK] 54580.9 | **100.0** |

---

## Qualidade Geral da Execução

- **Score medio:** `80.3/100`
- **Tabelas processadas:** 3
- **Com DLQ:** 0
- **Com WARNING:** 1
- **Documentadas por SLM:** 3

---

## Score por Dimensao

| Tabela | Conformidade (40%) | Completude (25%) | Unicidade (20%) | Estabilidade (15%) | Score |
|--------|--------------------|------------------|-----------------|--------------------|-------|
| `tb_clientes` | 0.0 | 80.8 | 100.0 |  100.0 | **55.2** |
| `tb_transacoes` | 100.0 | 66.5 | 70.4 |  100.0 | **85.7** |
| `tb_contratos_credito` | 100.0 | 100.0 | 100.0 |  100.0 | **100.0** |

- ``tb_clientes` / **conformity** = 0.0: tipo divergente do Manifest em vl_renda_mensal (8.0% de falha)
- ``tb_clientes` / **completeness** = 80.8: nulos em obrigatorias: 0.00% | anulaveis a 38% da tolerancia (25%)
- ``tb_transacoes` / **completeness** = 66.5: nulos em obrigatorias: 0.00% | anulaveis a 67% da tolerancia (10%)
- ``tb_transacoes` / **uniqueness** = 70.4: 30 duplicatas na PK ['id_transacao'] (1.48%)

---

## Gate de Tipagem (Manifest soberano)

| Tabela | Cenario | Publicacao | Linhas rejeitadas | % | Tolerancia | Colunas |
|--------|---------|------------|-------------------|---|------------|---------|
| `tb_clientes` | type_drift | BLOCKED | 40 | 8.00% | 1.00% | `vl_renda_mensal`: 40 |

> Linha rejeitada = valor preenchido fora do tipo declarado no Manifest. A linha inteira vai para `quarantine/reject_<tabela>.csv` com `_reject_columns`, `_reject_values` e `_reject_reason`; acima da tolerancia do contrato (`tolerancia.max_reject_pct`) a publicacao e bloqueada .

---

## Desempenho da SLM

| Tabela | Modelo | Wall (ms) | Carga (ms) | Prompt (Tok/ms) | Saida (tok/ms) | Tok/s | Cobertura | Truncado |
|--------|--------|-----------|------------|-----------------|----------------|-------|-----------|----------|
| `tb_clientes` | phi4 | 67,126 | 1 | 2496/2,086 | 1634/62,873 | **26.0** | 100.0% | nao |
| `tb_transacoes` | phi4 | 49,832 | 2 | 2175/883 | 1223/46,630 | **26.2** | 100.0% | nao |
| `tb_contratos_credito` | phi4 | 54,581 | 2 | 2722/1,937 | 1310/50,432 | **26.0** | 100.0% | nao |

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