# Changelog — Projeto Nimbus

Histórico de evolução do projeto, da concepção inicial até o estado atual.
Documento de maturidade — mostra como o projeto cresceu em robustez ao
longo do tempo.

---

## Sprint 1 — Fundação: Pipeline + Manifest Estendido

**Objetivo:** estabelecer a arquitetura medallion local e o manifest como
contrato de dados extensível.

**Entregue:**
- Arquitetura medallion completa (Bronze/Silver/Gold/Quarantine) com
  abstração de Storage (`LocalStorage`)
- Modelo de contrato (`DataContract`) com schema base + campos estendidos
  (`source`, `regulatory`, `steward`, `business_context`, `sample_queries`)
- Extrator automático de manifest para SAS7BDAT via `pyreadstat`
  (metadados sem carregar dados em memória)
- Fluxo HITL: `manifest_status` DRAFT → VALIDATED, com `ManifestValidator`
  bloqueando promoção até todos os `# TODO` serem resolvidos
- Integração SLM (Ollama local) para documentação semântica baseada no
  manifest + estatísticas do profiler
- Orquestração dupla: `run_pipeline.py` (direto) e `prefect_flow.py`
  (Prefect 2.x com mapeamento 1:1 para jobs Control-M)
- 65 testes unitários

**Decisões de arquitetura registradas:**
- Control-M substituído localmente por Prefect; mapeamento de exit codes
  0/1/2 preservado para compatibilidade
- ChromaDB apenas para PoC; produção usa Databricks Vector Search
- MinIO como espelho local do ADLS Gen2, troca de backend em uma linha

---

## Sprint 2 — Multi-formato, Encoding e Geração Realista

**Objetivo:** expandir a cobertura de formatos de origem (refletindo a
heterogeneidade real de um banco) e resolver problemas de encoding que
travavam o pipeline em arquivos legados.

**Entregue:**
- `normalizer.py` — pré-processador de encoding (UTF-8, CRLF→LF, BOM,
  detecção de EBCDIC com aviso)
- Extratores de manifest para CSV (inferência por amostragem), Fixed-Width
  (leiaute TXT/CSV/XLSX + modo de inferência experimental) e JSON
  (normalização de estruturas aninhadas)
- Refatoração do gerador de dados fictícios para o padrão **Strategy**:
  `BaseWriter` (ABC) com `CSVWriter`, `JSONWriter`, `FixedWidthWriter` —
  domínio de negócio desacoplado do formato de saída
- `Storage.read()` tornado format-aware: detecta extensão e usa o parser
  correto (CSV, JSON via `json_normalize`, Fixed-Width via `read_fwf` +
  sidecar de colspecs)
- Task opcional no Prefect (`JOB-DM-000-EXTRACT`) para geração automática
  de manifest quando ainda não existe
- 83 testes unitários adicionais (total: 148)

**Bugs corrigidos durante a sprint** (documentados para referência futura):
- Detecção de line endings retornava `mixed` incorretamente para CRLF puro
- Dupla normalização de nomes de coluna quebrava separador `__` em JSON
  aninhado
- `nunique()` falhava em colunas JSON colapsadas (contendo dicts)
- DuckDB falhava no sniff automático de CSV gerado no Windows (`\r\n` sem
  `lineterminator` explícito)
- Profiler e SLM não executavam para formatos JSON/Fixed-Width — causa raiz:
  `Storage.read()` sempre assumia CSV

---

## Reestruturação de Documentação (sessão atual)

**Objetivo:** eliminar fragmentação de instruções entre múltiplos arquivos
`.md`, resolver dependência do `make` (incompatível nativamente com Windows)
e organizar a documentação por audiência e propósito.

**Entregue:**
- `tasks.py` — runner cross-platform substituindo a dependência exclusiva
  do Makefile para usuários Windows
- Reestruturação de toda a documentação em `docs/`, separada por tema:
  arquitetura, manifest, SLM, testes, changelog, próximos passos
- README.md reescrito como porta de entrada: visão geral, estrutura,
  manual rápido — sem detalhe técnico profundo (delegado aos docs)
- Rebrand do projeto: **Data Masters → Projeto Nimbus**

---

## Convenção deste changelog

Cada entrada de sprint documenta: objetivo, o que foi entregue, decisões
de arquitetura relevantes e bugs corrigidos com causa raiz — não apenas
lista de arquivos. O objetivo é que alguém lendo de fora consiga entender
*por que* o projeto está estruturado como está, não só *o que* existe hoje.

Pendências e planejamento futuro não ficam aqui — consulte sempre
[NEXT_STEPS.md](NEXT_STEPS.md) para o estado mais atual.
