# O Manifest — Projeto Nimbus

O Manifest é o componente central do projeto. É o contrato formal entre quem produz o dado e quem consome — e a ponte real entre o time de negócio e o time técnico, que é a dor que o Nimbus resolve.

---

## Por que o Manifest existe

O conhecimento sobre o que uma tabela significa, de onde ela vem e quais regras de negócio ela carrega vive hoje disperso: em e-mails, na cabeça de quem implementou, em conversas que ninguém registrou. Quando essa pessoa sai do time, o conhecimento vai junto.

O Manifest formaliza esse conhecimento em um arquivo versionado, legível tanto por humanos quanto por máquinas — incluindo a SLM e agentes de codificação como o Devin. A ideia não é criar mais burocracia, mas criar um único lugar confiável onde negócio e técnico concordam sobre o que um dado representa.

---

## Estrutura do Manifest

```yaml
table          : tb_clientes
version        : 1.0.0
manifest_status: DRAFT           # DRAFT | VALIDATED

source:
  system          : CORE_BANCARIO_TOTVS
  format          : sas7bdat
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
  Tabela mestre de clientes. A segmentação determina o produto ofertado
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
    sas_label          : "CPF SEM MASCARA"
    regulatory_flags   : [LGPD_SENSITIVE]
    business_rules     : []
```

Nem todos os campos precisam ser preenchidos manualmente. Os extratores automáticos cuidam do schema técnico, da detecção de flags regulatórias por heurística e, quando o Ollama está disponível, do `business_context` inicial. O que sobra para o Data Steward revisar é bem menor do que parece à primeira vista.

| Campo | Quem preenche | Obrigatório para VALIDATED |
|---|---|---|
| `schema[].name`, `schema[].type` | Extrator automático | Sim |
| `schema[].sas_label` | Extrator (SAS7BDAT) | Não |
| `schema[].regulatory_flags` | Extrator (heurística) + revisão do Steward | Sim |
| `business_context` | SLM (rascunho) + Data Steward (validação) | Sim |
| `source.*` | Extrator (parcial) + Data Steward | Sim |
| `steward.name`, `steward.email` | Data Steward | Sim |
| `sample_queries` | SLM (sugestão) | Recomendado, não obrigatório |

---

## O papel do Data Steward

O Data Steward é o elo humano do processo — a pessoa que sabe o que o dado representa no negócio e que valida o que a IA gerou antes que ele vire fonte de verdade para o resto da organização.

Na prática, o trabalho do Steward é revisar um arquivo YAML com os campos marcados como `# TODO`, confirmar ou corrigir o `business_context` sugerido pela SLM e validar as flags regulatórias que foram detectadas por heurística. Depois disso, um comando promove o manifest de `DRAFT` para `VALIDATED`.

O que muda depois dessa promoção é significativo: o pipeline para de emitir alertas sobre documentação não confiável, a SLM passa a tratar o `business_context` como verdade e só expande — nunca reescreve — e agentes como o Devin podem consumir o manifest via RAG com segurança.

---

## O fluxo HITL na prática

```
Arquivo chega na Landing Zone
          |
  Extrator gera Manifest DRAFT
  (schema automático, regulatory_flags por heurística, campos TODO marcados)
          |
  Data Steward abre o YAML e preenche o que falta
          |
  python tasks.py validate-manifest --file <path> --steward "Nome"
          |
  Manifest VALIDATED
          |
  Pipeline consome sem alertas
  SLM usa como base para a documentação
  Devin consulta via RAG
```

---

## Extratores disponíveis

Cada formato de origem tem um extrator que gera o rascunho do Manifest automaticamente, sem precisar digitar o schema manualmente.

O extrator para **SAS7BDAT** lê os metadados internos do arquivo — nome de variável, label, formato — sem carregar os dados em memória. É o mais rico em informação automática porque o próprio formato SAS carrega boa parte do que o Manifest precisa.

```bash
python tasks.py extract-sas --file dados/tb_clientes.sas7bdat --table tb_clientes
```

O extrator para **CSV** infere o schema lendo as primeiras 500 linhas do arquivo e detecta delimitador e encoding automaticamente. A hierarquia de inferência de tipo segue a ordem `date → integer → float → boolean → string`, e colunas com prefixo `id_`, `cd_` ou `nr_` e 100% de valores únicos na amostra são marcadas como chave primária candidata.

```bash
python tasks.py extract-csv --file dados/tb_cobranca.csv --table tb_cobranca
```

Para **arquivos posicionais** (fixed-width), o extrator espera um arquivo de leiaute definindo nome, posição inicial, posição final e tipo de cada campo. Sem o leiaute, um modo de inferência experimental tenta deduzir as colunas por análise de frequência de espaços em branco — mas o resultado é marcado como `DRAFT_EXPERIMENTAL` e exige revisão obrigatória.

```bash
python -m src.manifest.extractor_fixed \
    --file data/landing/tb_posicional.txt \
    --layout data/layouts/tb_posicional_layout.txt \
    --table tb_posicional --output data/contracts/tb_posicional.yaml
```

O extrator para **JSON** normaliza estruturas aninhadas via `json_normalize`. Campos além do nível configurável são colapsados em string e marcados no manifest para revisão.

```bash
python -m src.manifest.extractor_json \
    --file data/landing/tb_clientes.json \
    --table tb_clientes --output data/contracts/tb_clientes.yaml --enrich
```

---

## Verificando e validando um manifest

Para checar o que ainda está pendente antes de promover:

```bash
python tasks.py check-manifest --file data/contracts/tb_clientes.yaml
```

Para promover de DRAFT para VALIDATED depois que tudo estiver preenchido:

```bash
python tasks.py validate-manifest --file data/contracts/tb_clientes.yaml --steward "Nome do Steward"
```

Um detalhe importante: o `ManifestWriter` nunca sobrescreve um manifest `VALIDATED`. Se uma nova extração for executada sobre uma tabela já validada, o resultado é gravado em um arquivo `_draft.yaml` separado, permitindo comparação manual antes de qualquer substituição.
