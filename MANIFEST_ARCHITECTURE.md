# Arquitetura — Manifesto Estendido + Extrator SAS7BDAT

> Documento de arquitetura para revisão antes do desenvolvimento.
> Sprint 1 do plano de evolução do projeto Data Masters.

---

## 1. Motivação

O manifesto atual (`DataContract`) cobre apenas a estrutura técnica da tabela
— nomes de colunas, tipos e tolerâncias. Ele não carrega:

- De onde o dado vem e como foi gerado
- O que cada coluna **significa** no contexto do negócio bancário
- Quais regulações se aplicam ao dado
- Como o arquivo deve ser lido (encoding, formato, leiaute)

Essas lacunas fazem com que a SLM produza documentação genérica, e fazem com
que o Devin não consiga responder perguntas de negócio sobre as tabelas —
apenas perguntas estruturais.

O manifesto estendido resolve isso. O extrator SAS7BDAT resolve o problema
de geração manual: os arquivos `.sas7bdat` já carregam boa parte dessas
informações internamente, e podemos extraí-las automaticamente.

---

## 2. Manifesto Estendido — Schema Proposto

### 2.1 Estrutura completa

```yaml
# ── Identidade ────────────────────────────────────────────────────────────────
table      : tb_clientes
version    : 1.1.0
manifest_status: DRAFT           # DRAFT | VALIDATED — controle HITL
validated_by   : null            # preenchido pelo Data Steward ao validar
validated_at   : null

# ── Origem ────────────────────────────────────────────────────────────────────
source:
  system        : CORE_BANCARIO_TOTVS   # sistema de origem
  format        : sas7bdat              # csv | fixed_width | sas7bdat | json | xlsx | xml | parquet
  encoding      : latin-1              # utf-8 | latin-1 | ebcdic | cp1252
  os            : unix                 # windows | unix | mainframe
  delimiter     : null                 # apenas para csv (vírgula, ponto-vírgula, pipe…)
  update_frequency: daily              # daily | weekly | monthly | event_driven
  contact       : squad-dados@banco.com.br

# ── Contexto de negócio ───────────────────────────────────────────────────────
# Este é o campo mais importante para SLM e Devin.
# Texto livre, escrito pelo Data Steward ou gerado pela SLM e validado.
business_context: >
  Tabela mestre de clientes utilizada por todos os produtos de crédito e
  relacionamento. A segmentação (cd_segmento) determina o produto ofertado,
  os limites de crédito e o gestor de relacionamento responsável.
  Atualizada diariamente pelo batch noturno do CORE_BANCARIO_TOTVS.

# ── Regulatório ───────────────────────────────────────────────────────────────
regulatory:
  tags:
    - LGPD           # nr_cpf_cnpj e nm_cliente são dados pessoais sensíveis
    - SCR            # alimenta o Sistema de Informações de Crédito do BCB
    - BACEN_4658     # sujeita à política de segurança cibernética
  data_classification: confidential   # public | internal | confidential | restricted
  retention_years: 10

# ── Governança ────────────────────────────────────────────────────────────────
owner  : squad-dados-cadastrais
steward:
  name : João Silva
  email: joao.silva@banco.com.br
dependencies:
  - tb_agencias
  - tb_segmentos
  - tb_gestores_relacionamento

# ── Tolerâncias de qualidade ──────────────────────────────────────────────────
tolerance:
  max_null_pct    : 25
  allow_duplicates: false

# ── Schema de colunas ─────────────────────────────────────────────────────────
# Cada coluna agora tem description e sas_label opcionais
schema:
  - name       : cd_cliente
    type       : string
    nullable   : false
    primary_key: true
    description: Código único de identificação do cliente no sistema legado.
                 Gerado sequencialmente pelo CORE_BANCARIO_TOTVS.
    sas_label  : "CODIGO CLIENTE"       # extraído automaticamente do SAS7BDAT

  - name       : nr_cpf_cnpj
    type       : string
    nullable   : false
    description: CPF (11 dígitos) ou CNPJ (14 dígitos) sem máscara.
                 Campo sensível LGPD — não expor em logs ou relatórios.
    sas_label  : "CPF/CNPJ SEM MASCARA"
    regulatory_flags:
      - LGPD_SENSITIVE

  - name       : vl_renda_mensal
    type       : float
    nullable   : true
    description: Renda mensal declarada em BRL. Pode ser nula para clientes
                 PJ ou quando não informada no cadastro.
    sas_label  : "RENDA MENSAL DECLARADA"
    business_rules:
      - "Nulo para 100% dos clientes PJ (cd_segmento IN ['PJ_PEQUENO','PJ_MEDIO'])"
      - "Threshold de segmentação PRIME: vl_renda_mensal >= 10000"

# ── Layout posicional ─────────────────────────────────────────────────────────
# Preenchido apenas quando source.format = fixed_width
layout: null

# ── Sugestões de uso para o Devin ─────────────────────────────────────────────
sample_queries:
  - description: "Distribuição de clientes por segmento"
    sql: "SELECT cd_segmento, COUNT(*) as qtd FROM tb_clientes
          WHERE fl_ativo = true GROUP BY cd_segmento ORDER BY qtd DESC"

  - description: "Clientes PRIME com renda acima de 50k"
    sql: "SELECT cd_cliente, nm_cliente, vl_renda_mensal FROM tb_clientes
          WHERE cd_segmento = 'PRIME' AND vl_renda_mensal > 50000"
```

### 2.2 Campos que a SLM pode gerar automaticamente

| Campo | Gerado automaticamente? | Como |
|---|---|---|
| `business_context` | ✅ SLM + revisão | Profiler stats + nome das colunas |
| `regulatory.tags` | ✅ SLM + revisão | Detecção de padrões (CPF, CNPJ, valores monetários) |
| `schema[].description` | ✅ SLM + revisão | Prefixo da coluna + stats |
| `schema[].sas_label` | ✅ Extração direta | Metadado interno do SAS7BDAT |
| `schema[].business_rules` | ⚠️ SLM sugestão | Baseado em distribuição de valores |
| `source.*` | ❌ Manual | Depende do sistema de origem |
| `steward.*` | ❌ Manual | Depende da estrutura organizacional |
| `sample_queries` | ✅ SLM + revisão | Baseado no schema e business_context |

---

## 3. Extrator SAS7BDAT — Arquitetura

### 3.1 O que o SAS7BDAT carrega internamente

Um arquivo `.sas7bdat` típico contém:

```
Metadados disponíveis via pyreadstat:
  column_names      → nomes das variáveis (ex: "CD_CLIENTE")
  column_labels     → labels descritivos (ex: "Codigo do Cliente no Sistema")
  column_formats    → formatos SAS (ex: "$CHAR12.", "BEST12.", "DATE9.")
  column_types      → numeric ou character
  file_label        → label do dataset inteiro
  creation_time     → data de criação do arquivo
  row_count         → número de registros
  original_variable_types → tamanho dos campos
```

### 3.2 Mapeamento SAS → Manifesto

```
SAS7BDAT                    →   Manifesto
────────────────────────────────────────────────────────────────
file_label                  →   description (rascunho)
column_names[i]             →   schema[i].name   (normalizado: lower + snake_case)
column_labels[i]            →   schema[i].sas_label + base para description
column_formats[i]           →   schema[i].type   (via mapeamento de formato)
column_types[i] == 'numeric'→   schema[i].type = float ou integer (ver formato)
column_types[i] == 'character'→ schema[i].type = string
row_count                   →   usado no profiling, não no manifesto
creation_time               →   source.last_modified (informativo)
```

**Mapeamento de formatos SAS para tipos do manifesto:**

```
Formato SAS         →   type no manifesto
────────────────────────────────────────────
$CHARn. / $n.       →   string
BEST. / COMMAn.     →   float
Zn.                 →   integer
DATE. / DDMMYY.     →   date
DATETIME. / DT.     →   datetime
Yn. / N.            →   boolean  (heurística: só tem 0 e 1)
```

### 3.3 Módulos propostos

```
src/
├── manifest/
│   ├── __init__.py
│   ├── extractor_base.py        Interface base: ExtractorBase
│   ├── extractor_sas7bdat.py    Implementação SAS7BDAT
│   ├── extractor_csv.py         Inferência por amostragem (Sprint 2)
│   ├── extractor_fixed.py       Layout posicional (Sprint 2)
│   ├── manifest_writer.py       Serializa para YAML + valida schema
│   └── manifest_validator.py    Valida manifesto existente (DRAFT → VALIDATED)
```

**`ExtractorBase` — interface comum:**

```python
class ExtractorBase(ABC):
    @abstractmethod
    def extract(self, file_path: Path, table_name: str) -> dict:
        """
        Lê o arquivo e retorna um dict compatível com o schema
        do manifesto estendido, com manifest_status = 'DRAFT'.
        Campos que não podem ser inferidos ficam como None.
        """

    @abstractmethod
    def supported_formats(self) -> list[str]:
        """Retorna os formatos que este extrator suporta."""
```

**`extractor_sas7bdat.py` — fluxo interno:**

```
1. pyreadstat.read_sas7bdat(file_path, metadataonly=True)
   → evita carregar os dados, lê apenas os metadados (rápido)

2. Normaliza os nomes das colunas
   → "CD CLIENTE" → "cd_cliente"  (lower + replace espaço por _)

3. Mapeia column_formats para tipos do manifesto

4. Detecta possíveis flags regulatórias por heurística:
   → coluna com "CPF" ou "CNPJ" no nome/label → LGPD_SENSITIVE
   → coluna com "RENDA", "SALARIO", "LIMITE" → possível SCR
   → coluna com "SENHA", "TOKEN" → restricted

5. Chama a SLM com os metadados extraídos para gerar:
   → business_context rascunho
   → description de cada coluna
   → sample_queries sugeridas

6. Serializa para YAML com manifest_status: DRAFT
```

### 3.4 CLI de uso

```bash
# Extrai manifesto de um SAS7BDAT e salva como YAML em contracts/
python -m src.manifest.extractor_sas7bdat \
    --file data/landing/tb_clientes.sas7bdat \
    --table tb_clientes \
    --output data/contracts/tb_clientes.yaml

# Com enriquecimento SLM (Ollama deve estar no ar)
python -m src.manifest.extractor_sas7bdat \
    --file data/landing/tb_clientes.sas7bdat \
    --table tb_clientes \
    --output data/contracts/tb_clientes.yaml \
    --enrich
```

---

## 4. Fluxo HITL do Manifesto

```
[Arquivo SAS7BDAT chega na Landing]
              │
              ▼
   extractor_sas7bdat.py
   (lê metadados + SLM enriquece)
              │
              ▼
   contracts/tb_clientes.yaml
   manifest_status: DRAFT
              │
              ▼
   Data Steward revisa:
   - business_context correto?
   - regulatory_tags completas?
   - descriptions fazem sentido?
   - sample_queries úteis?
              │
        ┌─────┴─────┐
        ▼           ▼
   Aprova      Rejeita / edita
        │           │
        ▼           ▼
   manifest_status: VALIDATED    volta para DRAFT com comentário
        │
        ▼
   Pipeline usa o manifesto
   SLM gera documentação enriquecida
   Devin consome via RAG
```

---

## 5. Impacto nos módulos existentes

### 5.1 `src/validation/contracts.py`

O `DataContract` atual precisará de novos dataclasses para os campos estendidos.
A estratégia é **adição backward-compatible** — todos os novos campos são
opcionais com `default=None`. Manifestos antigos continuam válidos.

```
DataContract (atual)          DataContract (estendido)
──────────────────────────────────────────────────────
table                         table
description                   description
owner                         owner
version                       version
tolerance                     tolerance
schema: [ColumnContract]      schema: [ColumnContract estendido]
                              manifest_status  ← novo
                              source: SourceInfo ← novo dataclass
                              regulatory: RegulatoryInfo ← novo dataclass
                              steward: StewardInfo ← novo dataclass
                              business_context ← novo
                              dependencies ← novo
                              sample_queries ← novo
```

### 5.2 `src/slm/ollama_enrichment.py`

O prompt atual envia o YAML inteiro para a SLM. Com o manifesto estendido,
o prompt passa a ter:

- `business_context` já disponível → SLM usa como âncora semântica
- `regulatory_tags` → SLM menciona no contexto de governança
- `schema[].description` já parcialmente preenchida → SLM complementa
- `sample_queries` → SLM pode validar ou sugerir variações

O `_SYSTEM_PROMPT` ganha uma instrução:
> "Se o manifesto já contiver `business_context`, use-o como verdade e
> expanda. Não contradiga o que está declarado pelo Data Steward."

### 5.3 `src/validators/validator.py`

Adiciona verificação de `manifest_status`:

```python
if contract.manifest_status == "DRAFT":
    result.warnings.append(
        "Manifesto em status DRAFT — documentação gerada sem validação humana."
    )
```

---

## 6. Dependências novas

```
pyreadstat>=1.2.0    # leitura de SAS7BDAT (também suporta SPSS, Stata)
```

`pyreadstat` é a única dependência nova para a Sprint 1. Não requer instalação
do SAS — lê o formato binário diretamente em Python.

---

## 7. O que NÃO muda nesta sprint

- `src/storage/storage.py` — nenhuma alteração
- `prefect_flow.py` — nenhuma alteração
- `run_pipeline.py` — nenhuma alteração
- Fluxo de validação, profiling e promoção Bronze → Silver — inalterado
- O manifesto gerado pelo extrator segue o mesmo caminho de qualquer manifesto:
  gravado em `contracts/` via storage e consumido pelo validator

---

## 8. Pontos de decisão antes de implementar

Três decisões que precisam ser tomadas antes de começar o código:

**Decisão 1 — Enriquecimento SLM é obrigatório ou opcional na extração?**
Se obrigatório, a extração sem Ollama no ar falha parcialmente.
Se opcional (`--enrich` flag), o rascunho sai sem `business_context` e
`sample_queries` — o Data Steward preenche manualmente.
*Recomendação: opcional, com fallback de campos vazios marcados com `# TODO`.*

**Decisão 2 — O extrator sobrescreve um manifesto existente?**
Se a tabela já tem um manifesto `VALIDATED` e um novo SAS7BDAT chega,
o extrator deve criar um diff ou sobrescrever?
*Recomendação: nunca sobrescrever VALIDATED. Criar `tb_clientes_draft.yaml`
para comparação manual.*

**Decisão 3 — Quem aciona o extrator?**
Manual via CLI, automático quando um `.sas7bdat` chega na landing, ou
integrado como um job antes do `task_validate` no Prefect?
*Recomendação para Sprint 1: CLI manual. Integração no Prefect fica para Sprint 2
quando os outros formatos também estiverem prontos.*
