# Changelog — Projeto Nimbus

Histórico de evolução do projeto, da concepção até o estado atual. O objetivo deste documento é que alguém de fora consiga entender por que o projeto está estruturado como está — não apenas o que existe hoje, mas as decisões que moldaram cada escolha.

---

## Sprint 1 — Fundação

O objetivo da primeira sprint era estabelecer a arquitetura medallion local e provar que o Manifest poderia funcionar como um contrato de dados extensível, capaz de carregar tanto a estrutura técnica quanto o contexto de negócio.

O entregável principal foi a arquitetura completa de Bronze, Silver, Gold e Quarantine com a abstração de Storage — uma interface única que o restante do pipeline usa sem saber se está escrevendo em disco local ou em um bucket S3. Essa decisão foi tomada cedo e com intenção clara: a migração para ADLS Gen2 em produção precisaria ser uma troca de implementação, não uma reescrita de lógica.

O modelo de contrato (`DataContract`) ganhou os campos estendidos nesta sprint: `source`, `regulatory`, `steward`, `business_context` e `sample_queries`. Todos opcionais e backward-compatible — Manifests antigos continuam carregando sem erro.

O extrator para SAS7BDAT foi o primeiro a ser implementado, e por um motivo estratégico: é o formato mais rico em metadados internos. O arquivo SAS já carrega nome de variável, label descritivo e formato — o extrator apenas organiza isso em YAML sem precisar carregar os dados em memória.

O fluxo HITL foi estabelecido nesta sprint: todo Manifest nasce como `DRAFT`, e só avança para `VALIDATED` depois de revisão humana via `manifest_validator.py`. O pipeline emite aviso quando consome um contrato não validado, mas não trava.

A orquestração foi implementada em paralelo com duas camadas: `run_pipeline.py` para execução direta e `prefect_flow.py` para integração com Prefect e mapeamento explícito para jobs Control-M com exit codes padronizados (0=OK, 1=WARNING, 2=ERROR/DLQ).

A sprint encerrou com 65 testes unitários passando.

---

## Sprint 2 — Multi-formato e encoding

A segunda sprint partiu de uma constatação prática: um banco real não trabalha só com CSV. Arquivos chegam de sistemas distintos em formatos distintos, frequentemente com encoding incorreto para o ambiente de processamento.

O primeiro entregável foi o `normalizer.py` — um pré-processador que garante UTF-8 e LF antes de qualquer coisa tocar o arquivo. Ele trata Latin-1, CP1252, BOM e CRLF automaticamente. Para EBCDIC, a decisão foi consciente: detectar e sinalizar, mas não converter. O middleware de transferência normalmente já faz essa conversão, e implementar um codec EBCDIC completo para casos esporádicos não justificaria o custo de manutenção.

Os extratores de Manifest para CSV, Fixed-Width e JSON foram implementados seguindo a mesma interface do extrator SAS7BDAT da Sprint 1. O de Fixed-Width tem um detalhe importante: sem um arquivo de leiaute externo, um arquivo posicional é completamente ilegível. Por isso o extrator exige o leiaute (TXT, CSV ou XLSX) e oferece um modo de inferência experimental apenas como último recurso, marcando o resultado como `DRAFT_EXPERIMENTAL` para forçar revisão.

O gerador de dados fictícios foi refatorado nesta sprint. A lógica que inventa os dados e a lógica que decide o formato de saída estavam misturadas — um problema que ficaria pior à medida que novos formatos fossem adicionados. A refatoração introduziu o padrão Strategy: `BaseWriter` como interface, `CSVWriter`, `JSONWriter` e `FixedWidthWriter` como implementações. O gerador de domínio entrega um DataFrame, o writer decide como serializar.

O `FixedWidthWriter` introduziu um mecanismo de sidecar: ao gravar um `.txt`, ele grava também um `.layout` com os colspecs exatos de cada campo. O `LocalStorage.read()` usa esse sidecar para garantir que a leitura posterior use as posições corretas. Sem isso, `read_fwf` tentaria inferir as colunas por heurística e chegaria a resultados errados.

Seis bugs foram corrigidos durante a sprint e documentados com causa raiz: a detecção de line endings que retornava `mixed` incorretamente para CRLF puro, a dupla normalização de nomes de coluna que quebrava o separador `__` em campos JSON aninhados, o `nunique()` que falhava em colunas com dicts colapsados, o DuckDB que falhava no sniff de CSV gerado no Windows sem `lineterminator` explícito, e o Storage que sempre assumia CSV ao ler — o que fazia JSON e Fixed-Width irem para DLQ antes mesmo de chegar ao validator.

A sprint encerrou com 148 testes unitários passando.

---

## Reestruturação de documentação e rebrand

Com o projeto funcional e estável, a necessidade passou a ser outra: tornar o código acessível para quem não participou do desenvolvimento. Havia instruções espalhadas em seis arquivos `.md` sem hierarquia clara, e o `Makefile` como único ponto de entrada de comandos — inutilizável no Windows sem instalação adicional.

O `tasks.py` foi criado como runner cross-platform: `python tasks.py <comando>` funciona nativamente em Windows, Mac e Linux sem dependência de `make`. Todos os fluxos do Makefile foram replicados e o comportamento padrão dos comandos de pipeline foi atualizado para rodar os três formatos por padrão — CSV, JSON e Fixed-Width — em vez de apenas CSV.

A documentação foi reorganizada em uma pasta `docs/` com arquivos temáticos: arquitetura, manifest, SLM, testes, changelog, próximos passos e plano de migração. O README foi reescrito como porta de entrada — apresentação, estrutura e manual rápido, sem detalhe técnico que pertence aos documentos específicos.

O projeto foi renomeado de Data Masters para **Projeto Nimbus**.
