# Pipeline Projeto Nimbus - Relatorio de Execucao
**Data:** 2026-09-12 02:18:11  |  **Run ID:** `run_20260912_021225_9307f9`

---

## Resumo por Tabela

| Tabela | Cenário | Status | Linhas | Dups | Nulos (avg%) | Profiling (ms) | SLM (ms) | Score |
|--------|---------|--------|--------|------|--------------|----------------|----------|-------|
| `tb_clientes` | type_drift | [PASS] PASS | 500 | 0 | 2.13% | 712.9 | [OK] 78514.6 | **55.2** |
| `tb_transacoes` | type_drift | [WARN] WARNING | 2,030 | 30 | 0.84% | 4034.0 | [OK] 52211.2 | **85.7** |
| `tb_contratos_credito` | type_drift | [PASS] PASS | 300 | 0 | 0.0% | 879.1 | [OK] 74348.0 | **100.0** |

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
| `tb_transacoes` | type_drift | PASS_WITH_REJECTS | 30 | 1.48% | 2.00% | - |
| `tb_contratos_credito` | type_drift | BLOCKED | 0 | 0.00% | 1.00% | - |

> Linha rejeitada = valor preenchido fora do tipo declarado no Manifest. A linha inteira vai para `quarantine/reject_<tabela>.csv` com `_reject_columns`, `_reject_values` e `_reject_reason`; acima da tolerancia do contrato (`tolerance.max_reject_pct`) a publicacao e bloqueada.

---

## Desempenho da SLM

| Tabela | Modelo | Wall (ms) | Carga (ms) | Prompt (Tok/ms) | Saida (tok/ms) | Tok/s | Cobertura | Truncado |
|--------|--------|-----------|------------|-----------------|----------------|-------|-----------|----------|
| `tb_clientes` | phi4 | 78,515 | 14,853 | 2496/2,151 | 1489/59,430 | **25.1** | 100.0% | nao |
| `tb_transacoes` | phi4 | 52,211 | 2 | 2179/1,518 | 1237/48,463 | **25.5** | 100.0% | nao |
| `tb_contratos_credito` | phi4 | 74,348 | 2 | 2687/1,968 | 1777/70,154 | **25.3** | 100.0% | nao |

> Compare modelos com `python show_metrics.py --models` (agrega todas as runs por `slm_model`).

---

## Detalhes por Tabela

### `tb_clientes`

### `tb_transacoes`
**Warnings:**
- [WARN] 30 duplicatas detectadas (1.5%)

### `tb_contratos_credito`
**Warnings:**
- [WARN] Manifesto em status DRAFT — documentacao gerada sem validacao humana. Execute: python -m src.manifest.manifest_validator --file <contrato.yaml> --steward 'Nome'

---
> AVISO: Toda documentacao gerada pela SLM possui status **[AI_METADATA_STATUS: DRAFT]**.
> Requer validação humana pelo Data Steward antes de uso em produção.