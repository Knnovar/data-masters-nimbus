# HANDOFF.md — Contexto completo para retomada por LLM
# Data Masters — Sprint 2

> Este documento foi gerado para permitir que uma LLM retome o desenvolvimento
> exatamente de onde parou, sem perda de contexto.

---

## 1. ESTADO ATUAL DO PROJETO

### Localização
```
/home/claude/data-masters/          # container
/mnt/user-data/outputs/data-masters-v10-final.zip   # backup mais recente
```

### Status dos testes
```
104 testes no total
103 passando
1 falhando: test_deep_nesting_collapsed (TestJSONExtractor)
```

### Rodar testes
```bash
cd /home/claude/data-masters
python3 tests/run_tests.py -v
```

---

## 2. ESTRUTURA DE ARQUIVOS

### Arquivos da Sprint 1 (estáveis, não mexer)
```
src/validation/contracts.py         # DataContract estendido (SourceInfo, RegulatoryInfo, etc.)
src/validation/validator.py         # Validação + DLQ + schema evolution
src/storage/storage.py              # LocalStorage | MinIOStorage
src/generators/data_generator.py    # Dados fictícios bancários
src/profiler/duckdb_profiler.py     # Profiling DuckDB/Pandas
src/slm/ollama_enrichment.py        # Documentação via Ollama
src/metrics/metrics_collector.py    # Métricas + quality score
src/manifest/extractor_base.py      # ABC: _detect_regulatory_flags, _normalize_column_name
src/manifest/extractor_sas7bdat.py  # Extrator SAS (pyreadstat, metadataonly=True)
src/manifest/manifest_writer.py     # Serializa YAML, protege VALIDATED
src/manifest/manifest_validator.py  # DRAFT -> VALIDATED (HITL)
```

### Arquivos da Sprint 2 (criados nesta sessão)
```
src/ingestion/__init__.py           # vazio
src/ingestion/normalizer.py         # encoding + line endings + BOM
src/manifest/extractor_csv.py       # inferência de schema por amostragem
src/manifest/extractor_fixed.py     # fixed-width com leiaute TXT/CSV/XLSX
src/manifest/extractor_json.py      # JSON com json_normalize (CONTÉM BUG)
tests/test_sprint2.py               # 39 testes novos (1 falhando)
```

### Arquivos de orquestração (atualizados nesta sessão)
```
prefect_flow.py                     # task_extract_manifest adicionada (JOB-DM-000)
requirements.txt                    # chardet + openpyxl adicionados
```

---

## 3. BUG RESTANTE — ÚNICO A CORRIGIR

### Arquivo: `src/manifest/extractor_json.py`
### Teste: `test_deep_nesting_collapsed` (TestJSONExtractor)

**Causa raiz:**
Quando `max_level=1` e o JSON tem estrutura `{"l1": {"l2": {"l3": {"v": 42}}}}`,
o `pandas.json_normalize` colapsa os níveis profundos como DICTS dentro da Series.
Então quando `_infer_business_rules` chama `series.nunique()` em uma Series que
contém dicts, o pandas lança `TypeError: unhashable type: 'dict'`.

**Localização exata:**
```
src/manifest/extractor_json.py, linha 65:
    rules = csv_ext._infer_business_rules(col_name, series, inferred)

que chama:
src/manifest/extractor_csv.py, linha 156:
    nu = non_null.nunique()   # <- aqui falha se series tem dicts
```

**Fix a aplicar:**

Em `src/manifest/extractor_json.py`, dentro do loop de construção de colunas,
substituir a chamada a `_infer_business_rules` por uma versão segura que
converte dicts para string antes de operar:

```python
# ANTES (linha ~65):
rules = csv_ext._infer_business_rules(col_name, series, inferred)

# DEPOIS:
try:
    safe_series = series.apply(
        lambda x: str(x) if isinstance(x, (dict, list)) else x
    )
    rules = csv_ext._infer_business_rules(col_name, safe_series, inferred)
except Exception:
    rules = []
```

Também adicionar o mesmo tratamento para `_infer_type` e `_is_pk_candidate`
para garantir que séries com dicts não quebrem esses métodos:

```python
# Antes de chamar qualquer método em series, adicionar:
# Converte objetos complexos (dict/list) para string
if series.apply(lambda x: isinstance(x, (dict, list))).any():
    series   = series.apply(lambda x: str(x) if isinstance(x, (dict, list)) else x)
    inferred = {"type": "string"}
    col["business_rules"].append(
        f"Campo colapsado de estrutura aninhada (nivel > {max_level}). "
        "Considere aumentar max_level ou normalizar a origem."
    )
    # pula inferência e vai direto para flags/pk
```

---

## 4. COMO APLICAR O FIX (passo a passo)

```python
# Abrir o arquivo
with open('src/manifest/extractor_json.py', encoding='utf-8') as f:
    content = f.read()

# Localizar o bloco do loop de colunas (começa em "for col_name in df.columns:")
# e substituir o bloco interno por uma versão que trata dicts
```

O bloco a substituir está entre as linhas que contém:
```python
        for col_name in df.columns:
            series   = df[col_name]
```
e termina antes de `columns.append({...})`.

**Substituição completa do bloco:**

```python
        for col_name in df.columns:
            series = df[col_name]

            # Detecta se a coluna contém dicts/listas (campo colapsado)
            has_complex = series.apply(
                lambda x: isinstance(x, (dict, list)) and pd.notna(x)
                if not isinstance(x, float) else False
            ).any()

            if has_complex:
                # Converte para string e marca como colapsado
                series   = series.apply(
                    lambda x: str(x) if isinstance(x, (dict, list)) else x
                )
                inferred = {"type": "string"}
                rules    = [
                    f"Campo colapsado de estrutura aninhada (nivel > {max_level}). "
                    "Considere aumentar max_level ou normalizar a origem."
                ]
                nullable = True
                is_pk    = False
                flags    = self._detect_regulatory_flags(col_name, col_name)
            else:
                inferred = csv_ext._infer_type(series)
                nullable = bool(series.isna().any() or (series == "").any())
                is_pk    = csv_ext._is_pk_candidate(col_name, series)
                flags    = self._detect_regulatory_flags(col_name, col_name)
                rules    = csv_ext._infer_business_rules(col_name, series, inferred)
                if inferred.get("format"):
                    rules.append(f"Formato detectado: {inferred['format']}")
                if inferred.get("mixed"):
                    rules.append("# TODO: coluna com valores mistos")

            columns.append({
                "name": col_name, "type": inferred["type"],
                "nullable": nullable, "primary_key": is_pk,
                "description": f"# TODO: descrever {col_name}",
                "regulatory_flags": flags, "business_rules": rules,
            })
```

---

## 5. APÓS CORRIGIR O BUG — TAREFAS RESTANTES

### 5a. Atualizar requirements.txt
Verificar se já tem estas linhas (podem ter sido perdidas no reset do container):
```
chardet>=5.0.0
openpyxl>=3.1.0
```

### 5b. Adicionar SPRINT2_SPECS.md ao contexto
O arquivo `SPRINT2_SPECS.md` foi criado mas pode não estar no ZIP.
Recriar se necessário (está no contexto desta sessão).

### 5c. Atualizar context.md com seção Sprint 2
Adicionar seção documentando:
- Arquivos criados nesta sprint
- Decisões de negócio registradas (EBCDIC fora do escopo, layouts locais)
- Estado dos testes (104 → 104 passando após o fix)

### 5d. Empacotar ZIP final
```bash
cd /home/claude
zip -r data-masters-v11.zip data-masters/ \
  --exclude "data-masters/data/*" \
  --exclude "data-masters/src/*/__pycache__/*" \
  --exclude "data-masters/__pycache__/*" \
  --exclude "data-masters/tests/__pycache__/*"
cp data-masters-v11.zip /mnt/user-data/outputs/data-masters-v11.zip
```

### 5e. Smoke test final
```bash
cd /home/claude/data-masters
python3 prefect_flow.py --no-prefect --scenario all
python3 show_metrics.py
python3 tests/run_tests.py -v   # deve mostrar 104 OK, 0 FAIL
```

---

## 6. DECISÕES TOMADAS NESTA SPRINT

| Decisão | Resolução |
|---|---|
| Formato padrão de leiaute | Nenhum padrão institucional — suporta TXT, CSV, XLSX |
| Repositório de leiautes | Local em `data/layouts/` (PoC) |
| EBCDIC | Fora do escopo — detecta, avisa, não converte |

---

## 7. PROBLEMAS ENCONTRADOS E SOLUÇÕES

### P1: Container reset entre sessões
**Causa:** O ambiente de execução é efêmero entre sessões longas.
**Solução:** Sempre restaurar do ZIP antes de continuar:
```bash
cd /home/claude && rm -rf data-masters
unzip /mnt/user-data/outputs/data-masters-v10-final.zip
```

### P2: _normalize_column_name remove __ dos separadores JSON
**Causa:** A função usa `re.sub(r'_+', '_', n)` que colapsa `__` para `_`.
**Solução:** Em `extractor_json.py`, não usar `_normalize_column_name` direto
nas colunas do df. Usar `_norm_part` em cada parte separada por `__`:
```python
def _norm_json_col(col):
    import re
    def _norm_part(s):
        s = re.sub(r'[^\w]', '_', s.strip().lower())
        return re.sub(r'_+', '_', s).strip('_')
    return '__'.join(_norm_part(p) for p in col.split('__'))
```

### P3: _build_columns renormaliza colunas já normalizadas
**Causa:** `_build_columns` do CSVExtractor chama `_normalize_column_name`
internamente, desfazendo a normalização com `__` do JSON.
**Solução:** Em `extractor_json.py`, construir as colunas no loop diretamente
em vez de delegar para `csv_ext._build_columns(df, n_sample)`.

### P4: ExtractorBase é ABC, não pode ser instanciada com __new__
**Causa:** `_make_column` em `extractor_fixed.py` tentava usar
`ExtractorBase.__new__(ExtractorBase)` para acessar `_normalize_column_name`.
**Solução:** Implementar a função `_norm` localmente dentro de `_make_column`
sem depender da classe:
```python
import re as _re
def _norm(raw):
    n = _re.sub(r'[^\w]', '_', raw.strip().lower())
    return _re.sub(r'_+', '_', n).strip('_')
```

### P5: _detect_line_endings retorna "mixed" para arquivos CRLF puros
**Causa:** `"\r\n"` contém `"\n"`, então a verificação `"\n" in content`
era verdadeira mesmo sem LF isolado.
**Solução:** Remover os `\r\n` antes de verificar `\n` isolado:
```python
without_crlf = content.replace('\r\n', '')
has_lone_lf  = '\n' in without_crlf
```

---

## 8. ARQUITETURA DO FLUXO DE EXTRAÇÃO (Sprint 2)

```
Arquivo bruto na landing zone
          |
   [normalizer.py]
   - detecta encoding (chardet)
   - converte para UTF-8
   - normaliza CRLF -> LF
   - remove BOM
   - EBCDIC: avisa e retorna sem converter
          |
   [extractor_*.py] (escolhido pelo formato)
   - extractor_csv.py    -> CSV, TSV, TXT
   - extractor_fixed.py  -> posicional (com leiaute ou inferência)
   - extractor_json.py   -> JSON, JSONL, NDJSON
   - extractor_sas7bdat.py -> SAS (Sprint 1)
          |
   [manifest_writer.py]
   - salva YAML em data/contracts/
   - nunca sobrescreve VALIDATED
   - cria _draft.yaml se destino for VALIDATED
          |
   [manifest_validator.py]
   - verifica campos TODO
   - promove DRAFT -> VALIDATED
          |
   Pipeline normal (validator, profiler, SLM, etc.)
```

### Integração com Prefect
O `prefect_flow.py` ganhou a task `JOB-DM-000-EXTRACT` (opcional):
- Skipa se manifesto já existe
- Normaliza encoding antes de extrair
- Seleciona extrator pelo formato
- Grava manifesto em `contracts/` via storage

---

## 9. DEPENDÊNCIAS NOVAS (Sprint 2)

```
chardet>=5.0.0    # detecção de encoding
openpyxl>=3.1.0   # leitura de layouts XLSX
```

Instalar:
```bash
pip install chardet openpyxl --break-system-packages
```

---

## 10. CHECKLIST DE ENTREGA DA SPRINT 2

- [x] `src/ingestion/normalizer.py` — criado e testado
- [x] `src/manifest/extractor_csv.py` — criado e testado
- [x] `src/manifest/extractor_fixed.py` — criado e testado
- [x] `src/manifest/extractor_json.py` — criado, 1 bug restante
- [x] `tests/test_sprint2.py` — 39 testes, 38 passando
- [x] `prefect_flow.py` — task_extract adicionada
- [ ] Bug `test_deep_nesting_collapsed` — fix descrito na seção 3
- [ ] `requirements.txt` atualizado com chardet + openpyxl
- [ ] `context.md` atualizado com seção Sprint 2
- [ ] ZIP v11 gerado e entregue

---

## 11. COMANDO PARA RETOMAR EM NOVA SESSÃO

```
Olá! Preciso que continue o desenvolvimento do projeto Data Masters.
Leia o arquivo HANDOFF.md em /home/claude/data-masters/ (ou no ZIP entregue).
O projeto está na Sprint 2. Há 1 bug restante descrito na seção 3 do HANDOFF.md.
Após corrigir o bug, execute as tarefas da seção 5 na ordem indicada.
Restaure o projeto com:
  cd /home/claude && rm -rf data-masters
  unzip /mnt/user-data/outputs/data-masters-v10-final.zip
  pip install chardet openpyxl --break-system-packages
```
