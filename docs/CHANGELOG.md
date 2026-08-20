# Changelog — Projeto Nimbus

Histórico de evolução do projeto, da concepção até o estado atual. O objetivo deste documento é que alguém de fora consiga entender por que o projeto está estruturado como está — não apenas o que existe hoje, mas as decisões que moldaram cada escolha.

---

## Sprint 1 — Fundação

O objetivo da primeira sprint era estabelecer a arquitetura medallion local e provar que o Manifest poderia funcionar como contrato de dados extensível, capaz de carregar tanto a estrutura técnica quanto o contexto de negócio.

O entregável principal foi a arquitetura completa de Bronze, Silver, Gold e Quarantine com a abstração de Storage — uma interface única que o restante do pipeline usa sem saber se está escrevendo em disco local ou em um bucket S3. Essa decisão foi tomada cedo e com intenção clara: a migração para ADLS Gen2 em produção precisaria ser uma troca de implementação, não uma reescrita de lógica.

O modelo de contrato ganhou os campos estendidos: `source`, `regulatory`, `steward`, `business_context` e `sample_queries`. O extrator para SAS7BDAT foi o primeiro a ser implementado por ser o formato mais rico em metadados internos. O fluxo HITL foi estabelecido: todo Manifest nasce como `DRAFT` e só avança para `VALIDATED` depois de revisão humana. A orquestração foi implementada em paralelo com `run_pipeline.py` e `prefect_flow.py` com mapeamento 1:1 para jobs Control-M.

A sprint encerrou com 65 testes unitários passando.

---

## Sprint 2 — Multi-formato e encoding

A segunda sprint partiu de uma constatação prática: um banco real não trabalha só com CSV. O primeiro entregável foi o `normalizer.py` — um pré-processador que garante UTF-8 e LF antes de qualquer coisa tocar o arquivo. Para EBCDIC, a decisão foi detectar e sinalizar, mas não converter — o middleware de transferência normalmente já faz essa conversão.

Os extratores de Manifest para CSV, Fixed-Width e JSON foram implementados seguindo a mesma interface do extrator SAS7BDAT. O gerador de dados fictícios foi refatorado com o padrão Strategy: `BaseWriter` como interface, `CSVWriter`, `JSONWriter` e `FixedWidthWriter` como implementações. O `FixedWidthWriter` introduziu um mecanismo de sidecar `.layout` para garantir a leitura posterior com os colspecs corretos.

Seis bugs foram corrigidos e documentados com causa raiz: detecção incorreta de line endings para CRLF puro, dupla normalização quebrando separadores `__` em JSON aninhado, `nunique()` falhando em colunas com dicts colapsados, DuckDB falhando no sniff de CSV gerado no Windows, e o Storage sempre assumindo CSV ao ler arquivos de outros formatos.

A sprint encerrou com 148 testes unitários passando.

---

## Reestruturação de documentação e rebrand

Com o projeto funcional e estável, a necessidade passou a ser outra: tornar o código acessível para quem não participou do desenvolvimento. O `tasks.py` foi criado como runner cross-platform que funciona nativamente em Windows, Mac e Linux sem dependência de `make`. A documentação foi reorganizada em `docs/` com arquivos temáticos. O README foi reescrito como porta de entrada. O projeto foi renomeado de Data Masters para Projeto Nimbus.

---

## Sprint A — Parquet no Silver

O Silver passou a armazenar dados em formato Parquet com compressão Snappy em vez de CSV. A mudança preserva o dado original em `bronze/_archive/` para rastreabilidade e garante que o Silver tem schema tipado — colunas numéricas chegam como float ou int, não como string, o que melhora a performance das consultas DuckDB.

O método `promote_to_parquet()` substituiu o `move()` na promoção Bronze → Silver. O `storage.read()` detecta o formato pela extensão e usa o parser correto para cada caso. O `pyarrow` foi adicionado como dependência.

A sprint encerrou com 158 testes passando.

---

## Sprint B — Databricks via REST API

`src/connectors/databricks_uploader.py` integra o pipeline com o Databricks sem necessidade de cluster Spark — compatível com Databricks for Students que disponibiliza apenas SQL Warehouse.

O upload usa a DBFS API em três etapas com blocos de 1MB em base64. Após o upload, a tabela é registrada no metastore via Statement Execution API. A integração é ativada via `DATABRICKS_AUTO_UPLOAD=true` em `config.py` e nunca bloqueia o pipeline — falhas são logadas e ignoradas. O `tasks.py` ganhou os comandos `upload-silver` e `test-databricks`.

A sprint encerrou com 175 testes passando.

---

## Deploy Docker — one-click

O projeto foi empacotado em um stack Docker com três serviços orquestrados pelo `docker-compose.yml`: o pipeline Nimbus, o Ollama e o MinIO. O `scripts/entrypoint.sh` coordena a sequência completa de inicialização — aguarda os serviços ficarem saudáveis, baixa o modelo via `ollama pull` se necessário, inicia o Prefect server, registra os deployments, sobe o worker e executa o pipeline automaticamente.

O `config.py` foi reescrito para ler todas as configurações via variáveis de ambiente, tornando o comportamento local e em Docker idênticos em termos de código. O único arquivo que o usuário precisa editar é o `.env`. GPU NVIDIA e AMD/ROCm são suportadas via configuração comentada no `docker-compose.yml`. O modelo Ollama é configurável via `OLLAMA_MODEL` no `.env` e baixado automaticamente — a imagem Docker não embute o modelo para manter o tamanho controlado e permitir customização.
