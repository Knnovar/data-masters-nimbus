# Pipeline Projeto Nimbus - Relatorio de Execucao
**Data:** 2026-09-12 13:09:23  |  **Run ID:** `run_20260912_130401_70171d`

---

## Resumo por Tabela

| Tabela | Cenário | Status | Linhas | Dups | Nulos (avg%) | Profiling (ms) | SLM (ms) | Score |
|--------|---------|--------|--------|------|--------------|----------------|----------|-------|
| `tb_clientes` | baseline | [PASS] PASS | 500 | 0 | 2.29% | 1250.4 | [OK] 80887.7 | **94.8** |
| `tb_transacoes` | baseline | [WARN] WARNING | 2,030 | 30 | 0.81% | 4114.0 | [OK] 56248.5 | **86.0** |
| `tb_contratos_credito` | baseline | [PASS] PASS | 300 | 0 | 0.0% | 899.2 | [OK] 65914.3 | **100.0** |

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

## Gate de Tipagem (Manifest soberano)

| Tabela | Cenario | Publicacao | Linhas rejeitadas | % | Tolerancia | Colunas |
|--------|---------|------------|-------------------|---|------------|---------|
| `tb_transacoes` | baseline | PASS_WITH_REJECTS | 30 | 1.48% | 2.00% | - |
| `tb_contratos_credito` | baseline | BLOCKED | 0 | 0.00% | 1.00% | - |

> Linha rejeitada = valor preenchido fora do tipo declarado no Manifest. A linha inteira vai para `quarantine/reject_<tabela>.csv` com `_reject_columns`, `_reject_values` e `_reject_reason`; acima da tolerancia do contrato (`tolerance.max_reject_pct`) a publicacao e bloqueada.

---

## Desempenho da SLM

| Tabela | Modelo | Wall (ms) | Carga (ms) | Prompt (Tok/ms) | Saida (tok/ms) | Tok/s | Cobertura | Truncado |
|--------|--------|-----------|------------|-----------------|----------------|-------|-----------|----------|
| `tb_clientes` | phi4 | 80,888 | 14,332 | 2498/2,128 | 1600/62,361 | **25.7** | 100.0% | nao |
| `tb_transacoes` | phi4 | 56,248 | 2 | 2173/1,814 | 1370/52,278 | **26.2** | 100.0% | nao |
| `tb_contratos_credito` | phi4 | 65,914 | 2 | 2688/1,930 | 1589/61,752 | **25.7** | 100.0% | nao |

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