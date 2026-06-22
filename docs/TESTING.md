# Testes — Projeto Nimbus

148 testes unitários usando `unittest` nativo do Python — sem dependências
externas como `pytest`. Cobertura de todos os módulos críticos do pipeline.

---

## 1. Como rodar

```bash
# Cross-platform (Windows/Mac/Linux)
python tasks.py test

# Equivalente direto
python tests/run_tests.py -v

# Módulo específico
python tests/run_tests.py test_storage
python tests/run_tests.py test_manifest
python tests/run_tests.py test_writers
```

---

## 2. Cobertura por módulo

| Arquivo de teste | Testes | Cobre |
|---|---|---|
| `test_contracts.py` | 17 | `DataContract`, `ColumnContract`, `SourceInfo`, `RegulatoryInfo`, validação de versão |
| `test_manifest.py` | 22 | `ExtractorBase` (heurística regulatória), `ManifestWriter`, `ManifestValidator` (HITL) |
| `test_storage.py` | 15 | `LocalStorage` (read/write/move por formato), integração com `validator` |
| `test_validator.py` | 11 | Cenários PASS, WARNING, DLQ, schema evolution |
| `test_sprint2.py` | 39 | `normalizer.py`, `extractor_csv.py`, `extractor_fixed.py`, `extractor_json.py` |
| `test_writers.py` | 44 | `CSVWriter`, `JSONWriter`, `FixedWidthWriter`, `WriterFactory`, `generate_all` multi-formato |
| **Total** | **148** | |

---

## 3. Critérios de aceite validados por teste

Estes são os comportamentos que o projeto garante via teste automatizado —
não apenas "código roda", mas "código se comporta como o negócio exige".

### Validação e Schema Evolution
- Dados conformes ao contrato retornam `PASS`
- Duplicatas acima da tolerância retornam `WARNING`, nunca bloqueiam
- Coluna obrigatória ausente retorna `DLQ` e isola o arquivo em quarentena
- Coluna nova (não esperada) retorna `WARNING` classificado como `NON_BREAKING`
- Manifest em `DRAFT` gera warning informativo sem bloquear o pipeline

### Manifest e Governança HITL
- Manifest sem campos `# TODO` é promovível para `VALIDATED`
- Manifest com qualquer `# TODO` pendente bloqueia a promoção
- `ManifestWriter` nunca sobrescreve um manifest `VALIDATED` — gera `_draft.yaml`
- Ausência de `sample_queries` é aviso, não bloqueio (não é obrigatório)
- Heurística regulatória detecta corretamente: CPF/CNPJ → `LGPD_SENSITIVE`,
  renda/salário → `SCR_CANDIDATE`, senha/token → `RESTRICTED`

### Multi-formato (Writers)
- Arquivo fixed-width respeita **exatamente** a contagem de bytes do leiaute
  declarado, incluindo padding e truncamento de valores longos
- JSON com aninhamento gera estrutura válida, sem dicts não-serializáveis
- Formato inválido (`xml`, etc.) levanta `ValueError` com mensagem listando
  as opções suportadas — nunca falha silenciosamente
- Todos os três formatos (csv/json/fixed) geram o mesmo contrato de dados

### Normalização de Encoding
- CRLF é convertido para LF de forma idempotente (já normalizado não muda)
- Latin-1/CP1252 são convertidos para UTF-8 corretamente
- BOM é removido sem corromper o conteúdo
- EBCDIC é detectado e sinalizado — nunca convertido silenciosamente
- Arquivo original é sempre preservado em backup antes de qualquer alteração

### Storage multi-camada
- `move()` entre camadas sobrescreve destino existente (compatibilidade Windows)
- `read()` detecta formato pela extensão e usa o parser correto
- Camada desconhecida levanta erro claro em vez de falha silenciosa

---

## 4. Política de teste do projeto

- **Sem mocks de rede para Ollama** — os testes de SLM verificam o
  comportamento de fallback (`SKIPPED`) quando o serviço não está disponível,
  não a qualidade da resposta gerada
- **Storage real, não mock** — `test_validator.py` e `test_storage.py` usam
  `LocalStorage` real apontando para diretórios temporários, validando o
  comportamento de ponta a ponta
- **Testes determinísticos** — geração de dados fictícios usa seed fixa
  onde aplicável, para resultados reproduzíveis

---

## 5. O que ainda não tem cobertura automatizada

Documentado para transparência — ver [NEXT_STEPS.md](NEXT_STEPS.md) para
o planejamento:

- Integração real com Ollama (testado manualmente, não em CI)
- Backend `MinIOStorage` (requer Docker, fora do escopo de testes unitários)
- `prefect_flow.py` com servidor Prefect real (testado via `--no-prefect`)
