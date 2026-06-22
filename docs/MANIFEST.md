# O Manifest — Projeto Nimbus

O Manifest é o componente central do Projeto Nimbus. É o contrato formal
entre quem produz o dado e quem consome — e a ponte entre o time de negócio
e o time técnico, que é a dor que este projeto resolve.

---

## 1. Por que o Manifest existe

Hoje, o conhecimento sobre o que uma tabela significa, de onde ela vem e
quais regras de negócio ela carrega vive disperso: em e-mails, na cabeça
de quem implementou, em conversas perdidas. Quando essa pessoa sai do time,
o conhecimento vai junto.

O Manifest formaliza esse conhecimento em um arquivo versionado, lido tanto
por humanos quanto por máquinas — incluindo a SLM (ver [SLM.md](SLM.md)) e
agentes de codificação como o Devin.

---

## 2. Estrutura do Manifest

```yaml
table          : tb_clientes
version        : 1.0.0
manifest_status: DRAFT           # DRAFT | VALIDATED

source:
  system          : CORE_BANCARIO_TOTVS
  format          : sas7bdat      # csv | fixed_width | sas7bdat | json | xlsx
  encoding        : latin-1
  os              : unix
  update_frequency: daily

regulatory:
  tags              : [LGPD, SCR, BACEN_4658]
  data_classification: confidential

steward:
  name : Joao Silva
  email: joao.silva@banco.com.br

business_context: >
  Tabela mestre de clientes. Segmentação determina o produto ofertado
  e o gestor responsável pelo relacionamento.

dependencies:
  - tb_agencias
  - tb_segmentos

sample_queries:
  - description: "Distribuição por segmento"
    sql: "SELECT cd_segmento, COUNT(*) FROM tb_clientes GROUP BY cd_segmento"

schema:
  - name             : nr_cpf_cnpj
    type              : string
    nullable          : false
    description       : CPF ou CNPJ sem máscara.
    sas_label          : "CPF SEM MASCARA"     # apenas se extraído de SAS7BDAT
    regulatory_flags   : [LGPD_SENSITIVE]
    business_rules     : []
```

### Campos e quem os preenche

| Campo | Preenchido por | Obrigatório p/ VALIDATED |
|---|---|---|
| `table`, `version`, `schema[].name/type` | Extrator automático | Sim |
| `schema[].sas_label` | Extrator (apenas SAS7BDAT) | Não |
| `schema[].regulatory_flags` | Extrator (heurística) + revisão do Steward | Sim |
| `business_context` | SLM (rascunho) + Data Steward (validação) | Sim |
| `source.*` | Extrator (parcial) + Data Steward | Sim |
| `steward.name/email` | Data Steward (manual) | Sim |
| `sample_queries` | SLM (sugestão) | Não (recomendado) |

---

## 3. O papel do Data Steward

O Data Steward é o elo humano do processo — a pessoa do time de negócio
ou de dados que valida o que a IA gerou antes que ele vire fonte de verdade
para o resto da organização.

**O que o Steward faz:**

1. Recebe um manifest em `DRAFT`, gerado automaticamente por um extrator
2. Revisa os campos marcados com `# TODO`
3. Confirma ou corrige o `business_context` sugerido pela SLM
4. Valida as `regulatory_flags` (LGPD, SCR, etc.) detectadas por heurística
5. Promove o manifest para `VALIDATED`

**O que muda quando o manifest é `VALIDATED`:**

- O pipeline para de emitir warning sobre documentação não confiável
- A SLM passa a tratar `business_context` como verdade absoluta — não
  reescreve, apenas expande
- Agentes como o Devin podem consumir o manifest via RAG com segurança

---

## 4. Fluxo HITL (Human-in-the-Loop)

```
Arquivo chega na Landing
          │
          ▼
  Extrator gera Manifest DRAFT
  (metadados automáticos + campos com # TODO)
          │
          ▼
  Data Steward revisa e preenche
          │
          ▼
  python tasks.py validate-manifest --file <path> --steward "Nome"
          │
          ▼
  Manifest VALIDATED
          │
          ▼
  Pipeline consome sem warnings
  SLM usa como verdade semântica
  Devin consome via RAG
```

---

## 5. Extratores Disponíveis

Cada formato de origem tem um extrator dedicado que gera o rascunho do
manifest automaticamente — sem digitação manual do schema.

### SAS7BDAT — `extractor_sas7bdat.py`

Lê metadados internos do arquivo (nome de variável, label, formato) sem
carregar os dados em memória (`pyreadstat`, `metadataonly=True`).

```bash
python tasks.py extract-sas --file dados/tb_clientes.sas7bdat --table tb_clientes
```

### CSV — `extractor_csv.py`

Infere schema lendo uma amostra (padrão 500 linhas). Detecta delimitador
e encoding automaticamente. Hierarquia de tipo: `date → integer → float →
boolean → string`.

```bash
python tasks.py extract-csv --file dados/tb_cobranca.csv --table tb_cobranca
```

### Fixed-Width (posicional) — `extractor_fixed.py`

Requer leiaute externo (TXT, CSV ou XLSX) com colunas `campo`, `inicio`,
`fim`, `tipo`. Sem leiaute, oferece modo `--infer` experimental, que marca
o manifest como `DRAFT_EXPERIMENTAL` — revisão obrigatória.

```bash
python -m src.manifest.extractor_fixed \
    --file data/landing/tb_posicional.txt \
    --layout data/layouts/tb_posicional_layout.txt \
    --table tb_posicional --output data/contracts/tb_posicional.yaml
```

### JSON — `extractor_json.py`

Normaliza estruturas aninhadas via `json_normalize`. Campos além do
`max_level` configurado são colapsados em string, com aviso no manifest.

```bash
python -m src.manifest.extractor_json \
    --file data/landing/tb_clientes.json \
    --table tb_clientes --output data/contracts/tb_clientes.yaml --enrich
```

---

## 6. Comandos Rápidos (via tasks.py)

```bash
# Verifica pendências sem alterar o arquivo
python tasks.py check-manifest --file data/contracts/tb_clientes.yaml

# Promove DRAFT -> VALIDATED
python tasks.py validate-manifest --file data/contracts/tb_clientes.yaml --steward "Nome"
```

---

## 7. Proteção de Dados

O `ManifestWriter` nunca sobrescreve um manifest `VALIDATED`. Se uma nova
extração for executada sobre uma tabela já validada, o resultado é gravado
em um arquivo `_draft.yaml` paralelo — preservando a versão validada e
permitindo comparação manual antes de qualquer substituição.
