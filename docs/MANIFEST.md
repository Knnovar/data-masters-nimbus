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

---

## Versionamento: o que existe e o que não existe

O ciclo `DRAFT → VALIDATED` é real, auditável e protegido: o promotor registra `validated_by` e
`validated_at`, recusa promover manifest com `# TODO` pendente e o `ManifestWriter` nunca sobrescreve
um `VALIDATED` (só sobrescreve DRAFT, e apenas com `--overwrite`).

Sobre a versão do contrato, o que existe hoje e o que ainda não existe:

- Os quatro extratores escrevem `version: "1.0.0"` no rascunho, mas a partir daí quem calcula o
  número é o `manifest-version`, comparando o contrato com o baseline. A seção
  [Versão do contrato](#versão-do-contrato-manifest-version) descreve a regra inteira.
- O histórico de versões fica no próprio Manifest, em `version_history`, e o lock em
  `data/contracts/.lock/` guarda o último estado publicado.
- Ainda não há registry central: nada de `tb_clientes_v2.yaml`, nada de seleção automática da
  versão vigente, nada de consulta de quem consome cada versão.
- O `_draft.yaml` gerado por uma nova extração sobre um contrato `VALIDATED` continua sendo
  comparado à mão. O `manifest-version` compara o contrato com o baseline, e não o rascunho com o
  contrato em vigor.

O que falta nessa frente está registrado em [NEXT_STEPS.md](NEXT_STEPS.md).

---

## O gate de governança

`REQUIRE_VALIDATED_MANIFEST` controla o rigor:

| Valor | Comportamento |
|---|---|
| `false` (padrão) | manifest em DRAFT gera aviso em toda execução, mas a publicação segue |
| `true` | manifest em DRAFT **bloqueia a publicação** e o pipeline termina com exit code 2 |

O status também viaja com o dado: o footer do Parquet no Silver carrega `manifest_validated` ou
`manifest_draft`, e o relatório consolidado leva a marca `[AI_METADATA_STATUS: DRAFT]` enquanto
houver texto gerado pela SLM sem revisão humana.

---

## Do contrato para a permissão: `emit-grants`

A classificação de sensibilidade não serve só para mascarar rejeito: ela é a mesma informação que
um administrador de Unity Catalog precisa para conceder acesso. `emit-grants` fecha esse caminho
derivando o DDL de acesso do próprio Manifest:

```bash
python tasks.py emit-grants --file data/contracts/tb_clientes.yaml
python tasks.py emit-grants --file data/contracts/tb_clientes.yaml \
  --catalog nimbus --schema silver \
  --reader-group nimbus_readers --pii-group nimbus_pii_readers \
  --output grants.sql
```

A saída tem três partes: `GRANT USE CATALOG`/`USE SCHEMA`/`SELECT` para o grupo leitor; uma
`CREATE OR REPLACE FUNCTION` de máscara **por tipo SQL** (o Unity Catalog exige que a função
devolva o tipo da coluna, então `mask_pii_string` devolve `'***'` e `mask_pii_date` devolve
`NULL`); e um `ALTER COLUMN ... SET MASK` para cada coluna marcada `LGPD_SENSITIVE`.

Duas decisões que valem explicitar:

- **O comando não executa nada.** Não abre conexão, não autentica e não usa o PAT — ele imprime
  texto. Quem aplica é quem tem alçada no workspace, e o artefato existe justamente para ser
  revisado antes disso. O pipeline deriva a permissão do contrato; não concede permissão.
- **Classificação restrita sai comentada.** Com `classification` em `restricted`, `secret` ou
  `confidential_restricted`, o `GRANT SELECT` é emitido como comentário: liberar leitura de tabela
  restrita para um grupo amplo é decisão de dono do dado, não default de ferramenta.

O `owner`, a `version` e o status do Manifest viajam no cabeçalho do SQL, então o DDL sempre diz de
qual contrato ele saiu — e um Manifest em DRAFT gera aviso no próprio arquivo.

---

## Versão do contrato: `manifest-version`

O campo `version` não é decorativo nem manual: ele é derivado do **diff entre o Manifest atual e o
baseline**, com a regra de compatibilidade escrita no código.

```bash
# analisa (nao altera o arquivo)
python tasks.py manifest-version --file data/contracts/tb_clientes.yaml

# aplica o bump e registra o historico
python tasks.py manifest-version --file data/contracts/tb_clientes.yaml \
  --apply --author "Joao Silva"

# compara contra um arquivo especifico em vez do baseline automatico
python tasks.py manifest-version --file data/contracts/tb_clientes.yaml \
  --baseline data/contracts/tb_clientes_v1.yaml
```

### A regra de bump

| Mudança | Nível | Por quê |
|---|---|---|
| coluna removida, tipo alterado, `nullable: true → false`, PK ou ordem de colunas alterada | **MAJOR** | quebra consumidor existente |
| formato/delimitador/encoding da origem alterado | **MAJOR** | quebra a leitura do arquivo |
| tolerância restringida (limite menor, ou limite acordado removido) | **MAJOR** | carga que passava passa a reprovar |
| coluna nova obrigatória (`nullable: false`) | **MAJOR** | carga existente não tem a coluna |
| coluna nova opcional, `nullable: false → true`, tolerância afrouxada, classificação regulatória | **MINOR** | retrocompatível |
| descrição, `business_rules`, `sas_label`, owner/steward, metadados | **PATCH** | não muda o dado |

Entre várias mudanças, vale a **de maior severidade**: `MAJOR > MINOR > PATCH > NONE`.

### Contra o que se compara

A resolução do baseline é, nesta ordem:

1. `--baseline <arquivo>`, quando você quer comparar contra uma versão específica;
2. **Git** (`git show HEAD:<caminho>`) — o baseline é o contrato commitado, sem estado extra;
3. **lock file** (`data/contracts/.lock/<tabela>.yaml`) — snapshot do último bump aplicado, usado
   quando não há `.git` (container, tarball, workspace sem histórico);
4. sem baseline: o Manifest é tratado como primeira versão e o lock inicial é gravado no `--apply`.

O lock é gravado a cada `--apply` e **é versionado junto com o contrato** — é ele que mantém a
auditoria funcionando dentro da imagem, onde não existe histórico Git.

### O histórico fica no próprio contrato

```yaml
version: 2.0.0
version_history:
  - version: 2.0.0
    previous_version: 1.0.0
    level: MAJOR
    date: "2026-09-14T02:02:44"
    author: "Joao Silva"
    baseline_source: "git:HEAD"
    revalidacao_requerida: true
    changes:
      - nivel: MAJOR
        campo: schema.vl_renda_mensal
        detalhe: coluna removida
```

Duas consequências deliberadas:

- **Promover com schema alterado e sem bump falha.** O `manifest_validator` chama a mesma avaliação
  antes de gravar `VALIDATED` e recusa a promoção, apontando o comando que corrige. A exceção
  existe (`--skip-version-check`) e é explícita, para não virar caminho normal.
- **Aplicar bump em Manifest `VALIDATED` devolve o status para `DRAFT`** e limpa `validated_by` /
  `validated_at`. Manter `VALIDATED` seria afirmar que o Steward aprovou uma versão que ele nunca
  viu; a revalidação continua sendo ato humano.

---

## Cuidado operacional com os arquivos

Os manifests vivem em `data/contracts/`, que **é versionado** (o `.gitignore` e o `.dockerignore`
têm a exceção escrita, com o motivo): contrato é artefato de governança, não dado gerado — e sem
ele o container não tem contra o que validar. O diretório `.lock/` acompanha, pelo mesmo motivo.

`python tasks.py clean-data` preserva `data/contracts/` por padrão; só apaga os contratos com
`--contracts` explícito. Ainda assim, antes de qualquer limpeza vale conferir o que está `VALIDATED`
— um contrato promovido é o registro de uma decisão humana, não um arquivo reproduzível.
