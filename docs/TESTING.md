# Testes — Projeto Nimbus

148 testes unitários usando `unittest` nativo do Python, sem dependências externas. A escolha pelo `unittest` em vez do `pytest` foi deliberada — qualquer pessoa que tenha Python instalado consegue rodar os testes sem instalar mais nada.

---

## Como rodar

```bash
python tasks.py test
```

Ou diretamente:

```bash
python tests/run_tests.py -v
python tests/run_tests.py test_storage    # módulo específico
python tests/run_tests.py test_manifest
python tests/run_tests.py test_writers
```

---

## O que está coberto

Os testes estão distribuídos em seis arquivos, cada um cobrindo uma área do projeto:

`test_contracts.py` (17 testes) cobre o modelo de dados — `DataContract`, `ColumnContract`, `SourceInfo`, `RegulatoryInfo` e a validação de versão do Manifest. `test_manifest.py` (22 testes) cobre os módulos de extração e governança: a heurística regulatória do `ExtractorBase`, o `ManifestWriter` e o fluxo HITL do `ManifestValidator`. `test_storage.py` (15 testes) cobre o `LocalStorage` com leitura e escrita nos três formatos suportados, além de um conjunto de testes de integração com o `validator`. `test_validator.py` (11 testes) cobre os três cenários de validação: PASS, WARNING e DLQ, incluindo schema evolution. `test_sprint2.py` (39 testes) cobre os módulos da Sprint 2 — `normalizer.py`, `extractor_csv.py`, `extractor_fixed.py` e `extractor_json.py`. `test_writers.py` (44 testes) cobre os três writers de formato, a `WriterFactory` e o `generate_all` multi-formato.

---

## O que os testes garantem

Mais do que confirmar que o código roda, os testes garantem comportamentos de negócio específicos. Alguns exemplos:

**Validação.** Um arquivo com coluna obrigatória ausente sempre vai para DLQ, nunca passa silenciosamente. Uma coluna nova adicionada pela origem é classificada como NON_BREAKING, não como erro. Um Manifest em DRAFT gera aviso informativo sem bloquear a execução.

**Manifest e governança.** Um Manifest com campos `# TODO` pendentes não pode ser promovido para VALIDATED — o comando bloqueia e lista o que falta. Um Manifest já VALIDATED nunca é sobrescrito por uma nova extração — o writer cria um arquivo `_draft.yaml` paralelo. A ausência de `sample_queries` gera aviso, mas não impede a promoção.

**Encoding e normalização.** CRLF é convertido para LF sem corromper o conteúdo. BOM é removido antes do processamento. EBCDIC é detectado e sinalizado explicitamente — nunca convertido silenciosamente. O arquivo original é sempre preservado em backup antes de qualquer alteração.

**Writers multi-formato.** O arquivo Fixed-Width respeita exatamente a contagem de bytes declarada no leiaute, incluindo padding e truncamento de valores que excedem a largura do campo. JSON com aninhamento produz estrutura válida sem dicts não-serializáveis. Um formato inválido passado para a `WriterFactory` levanta `ValueError` com mensagem clara — nunca falha silenciosamente.

**Storage.** O `move()` entre camadas sobrescreve o destino quando ele já existe, garantindo compatibilidade com Windows onde `rename` falha se o arquivo de destino existe. O `read()` detecta o formato pela extensão e usa o parser correto para cada um.

---

## O que não tem cobertura automatizada

Documentado para transparência: a integração real com o Ollama é testada manualmente, não em CI, porque depende de um serviço externo rodando. O backend `MinIOStorage` requer Docker e está fora do escopo de testes unitários. O `prefect_flow.py` com servidor Prefect real é validado via `--no-prefect` nos testes.

Esses três pontos estão no radar de evolução — ver [NEXT_STEPS.md](NEXT_STEPS.md).

---

## Política de teste do projeto

Os testes de Storage e Validator usam `LocalStorage` real apontando para diretórios temporários (`tempfile.mkdtemp()`), não mocks. Isso garante que o comportamento de ponta a ponta é validado, não apenas a lógica interna de cada função. A geração de dados fictícios usa os mesmos geradores do pipeline para que os testes multi-formato reflitam exatamente o que o usuário vai encontrar em produção.
