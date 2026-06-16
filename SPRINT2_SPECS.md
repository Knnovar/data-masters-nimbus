# Sprint 2 — Especificacoes Tecnicas
## Multi-formato, Encoding e Integracao Prefect

> Continuacao direta da Sprint 1 (manifesto estendido + extrator SAS7BDAT).

---

## Contexto e Motivacao

A Sprint 1 entregou a infraestrutura do manifesto e o extrator para SAS7BDAT.
A Sprint 2 expande a cobertura para os demais formatos prevalentes no banco
e resolve o problema de encoding que impede a leitura correta de arquivos
legados em ambientes Windows/mainframe.

---

## Escopo da Sprint

| Item | Arquivo | Status |
|---|---|---|
| Extrator CSV com inferencia de schema | `src/manifest/extractor_csv.py` | Entregue |
| Extrator Fixed-Width posicional | `src/manifest/extractor_fixed.py` | Entregue |
| Extrator JSON com normalizacao aninhada | `src/manifest/extractor_json.py` | Entregue |
| Normalizacao de encoding na landing | `src/ingestion/normalizer.py` | Entregue |
| Integracao Prefect (task opcional) | `prefect_flow.py` | Entregue |
| Testes unitarios | `tests/test_sprint2.py` | 39 testes, 100% passando |

---

## 1. extractor_csv.py

Infere schema lendo `N_SAMPLE` linhas (padrao 500). Hierarquia de tipo:
`date` -> `integer` -> `float` -> `boolean` -> `string`. Detecta delimitador
via `csv.Sniffer` e encoding via `chardet` (threshold 0.80, fallback latin-1).

PK heuristica: prefixo `id_/cd_/nr_/cod_/key_/pk_` + 100% unico na amostra.
Sem header (linha 1 100% numerica): gera `col_001`, `col_002`...

```bash
python -m src.manifest.extractor_csv \
    --file data/landing/tb_cobranca.csv --table tb_cobranca \
    --output data/contracts/tb_cobranca.yaml --sample 500 --enrich
```

---

## 2. extractor_fixed.py

Dois modos:
- **Modo A** (leiaute fornecido): TXT tabular, CSV ou XLSX com colunas
  `campo/field`, `inicio/start`, `fim/end`, `tipo/type`, `descricao` (opcional)
- **Modo B** (`--infer`): inferencia experimental por frequencia de espacos,
  marca `manifest_status: DRAFT_EXPERIMENTAL`

Convencao de busca automatica: `data/layouts/<table>_layout.{txt,csv,xlsx}`

Validacao de leiaute: sobreposicao de campos (warning), lacunas (warning com
sugestao de padding), `end < start` (warning).

```bash
# Modo A
python -m src.manifest.extractor_fixed \
    --file data/landing/tb_pos.txt --layout data/layouts/tb_pos_layout.txt \
    --table tb_pos --output data/contracts/tb_pos.yaml

# Modo B
python -m src.manifest.extractor_fixed \
    --file data/landing/tb_pos.txt --table tb_pos \
    --output data/contracts/tb_pos.yaml --infer
```

---

## 3. extractor_json.py

Usa `pandas.json_normalize(max_level=N, sep="__")`. Campos alem de max_level
sao colapsados em string com business_rule explicando o colapso.

Suporta `.json` (objeto ou lista), `.jsonl`/`.ndjson`. Root key auto-detectada
(primeira chave do dict que contem uma lista) se `--root-key` nao informado.

```bash
python -m src.manifest.extractor_json \
    --file data/landing/tb_clientes.json --table tb_clientes \
    --output data/contracts/tb_clientes.yaml --root-key data --max-level 2 --enrich
```

---

## 4. normalizer.py

Pre-processador antes do validator. Garante UTF-8 + LF:
1. Detecta encoding (chardet)
2. Converte para UTF-8
3. CRLF/CR -> LF
4. Remove BOM (UTF-8 e UTF-16 LE)
5. Backup do original em `_originals/`
6. EBCDIC: detecta, avisa, NAO converte

```python
from src.ingestion.normalizer import normalize
result = normalize(Path("data/landing/tb.csv"), backup=True)
```

---

## 5. Integracao Prefect — JOB-DM-000-EXTRACT (opcional)

Task `task_extract_manifest(filename, table_name, fmt)` adicionada antes de
JOB-DM-001-GENERATE. Skipa silenciosamente se `contracts/<table>.yaml` ja
existe. Normaliza encoding antes de extrair. Roteia por `fmt`:
`csv` -> CSVExtractor, `json` -> JSONExtractor, `fixed` -> FixedWidthExtractor
(modo infer). Falha nao bloqueia o pipeline (retorna status ERROR, segue sem
manifesto).

---

## 6. Decisoes de negocio — RESOLVIDAS

**Decisao 1 — Formato padrao de leiaute:** Nao existe formato institucional.
Extrator suporta TXT, CSV e XLSX genericamente.

**Decisao 2 — Repositorio de leiautes:** Local em `data/layouts/` para a PoC.
Migracao para repositorio compartilhado fica pos-PoC.

**Decisao 3 — Politica EBCDIC:** Fora do escopo. Middleware ja converte na
maioria dos casos. Normalizer detecta, avisa e orienta reconversao manual.
Zero implementacao de codec EBCDIC.

---

## 7. Dependencias novas

```
chardet>=5.0.0    # deteccao de encoding
openpyxl>=3.1.0   # leitura de layouts XLSX
```

---

## 8. Estado final

```
104 testes totais (65 Sprint 1 + 39 Sprint 2) — 100% passando
python3 tests/run_tests.py -v
```

## 9. Sprint 3 — candidatos

- Tabela Gold consolidada de metricas
- CLI unificada com auto-deteccao de formato: `python -m src.manifest.extract --file X --format auto`
- Prefect: parametro `auto_extract: true` no prefect.yaml
