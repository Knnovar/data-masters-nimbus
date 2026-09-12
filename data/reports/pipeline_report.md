# Pipeline Projeto Nimbus - Relatorio de Execucao
**Data:** 2026-09-12 00:39:27  |  **Run ID:** `run_20260912_003926_2b9529`

---

## Resumo por Tabela

| Tabela | Cenário | Status | Linhas | Dups | Nulos (avg%) | Profiling (ms) | SLM (ms) | Score |
|--------|---------|--------|--------|------|--------------|----------------|----------|-------|
| `tb_clientes` | baseline | [DLQ] DLQ | 0 | 0 | 0% | 0 | [SKIP] 0 | **60.0** |
| `tb_transacoes` | baseline | [DLQ] DLQ | 0 | 0 | 0% | 0 | [SKIP] 0 | **60.0** |
| `tb_contratos_credito` | baseline | [DLQ] DLQ | 0 | 0 | 0% | 0 | [SKIP] 0 | **60.0** |

---

## Qualidade Geral da Execução

- **Score medio:** `60.0/100`
- **Tabelas processadas:** 3
- **Com DLQ:** 3
- **Com WARNING:** 0
- **Documentadas por SLM:** 0

---

## Score por Dimensao

| Tabela | Conformidade (40%) | Completude (25%) | Unicidade (20%) | Estabilidade (15%) | Score |
|--------|--------------------|------------------|-----------------|--------------------|-------|
| `tb_clientes` | 0.0 | 100.0 | 100.0 |  100.0 | **60.0** |
| `tb_transacoes` | 0.0 | 100.0 | 100.0 |  100.0 | **60.0** |
| `tb_contratos_credito` | 0.0 | 100.0 | 100.0 |  100.0 | **60.0** |

- ``tb_clientes` / **conformity** = 0.0: tabela em quarentena (breaking change)
- ``tb_transacoes` / **conformity** = 0.0: tabela em quarentena (breaking change)
- ``tb_contratos_credito` / **conformity** = 0.0: tabela em quarentena (breaking change)

---

## Gate de Tipagem (Manifest soberano)

| Tabela | Cenario | Publicacao | Linhas rejeitadas | % | Tolerancia | Colunas |
|--------|---------|------------|-------------------|---|------------|---------|
| `tb_clientes` | baseline | BLOCKED | 0 | n/d | n/d | - |
| `tb_transacoes` | baseline | BLOCKED | 0 | n/d | n/d | - |
| `tb_contratos_credito` | baseline | BLOCKED | 0 | n/d | n/d | - |

> Linha rejeitada = valor preenchido fora do tipo declarado no Manifest. A linha inteira vai para `quarantine/reject_<tabela>.csv` com `_reject_columns`, `_reject_values` e `_reject_reason`; acima da tolerancia do contrato (`tolerance.max_reject_pct`) a publicacao e bloqueada.

---

## Desempenho da SLM

Nenhuma inferencia bem-sucedida nesta execucao. 


---

## Detalhes por Tabela

### `tb_clientes`
**Issues criticos:**
- [ERR] Arquivo ilegivel: [Errno 2] No such file or directory: 'C:\\Programação\\data-masters-nimbus\\data-masters-nimbus\\data\\landing\\tb_clientes.csv'

### `tb_transacoes`
**Issues criticos:**
- [ERR] Arquivo ilegivel: [Errno 2] No such file or directory: 'C:\\Programação\\data-masters-nimbus\\data-masters-nimbus\\data\\landing\\tb_transacoes.csv'

### `tb_contratos_credito`
**Issues criticos:**
- [ERR] Arquivo ilegivel: [Errno 2] No such file or directory: 'C:\\Programação\\data-masters-nimbus\\data-masters-nimbus\\data\\landing\\tb_contratos_credito.csv'

---
> AVISO: Toda documentacao gerada pela SLM possui status **[AI_METADATA_STATUS: DRAFT]**.
> Requer validação humana pelo Data Steward antes de uso em produção.