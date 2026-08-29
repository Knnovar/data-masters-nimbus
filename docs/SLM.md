# A SLM no Projeto Nimbus

Este documento explica o papel da Small Language Model na arquitetura do Nimbus: o que ela recebe, o que produz, onde entra no fluxo e por que foi uma escolha deliberada usar um modelo local em vez de uma API de nuvem.

---

## Por que modelo local

A escolha pelo Ollama rodando localmente não foi por limitação técnica — foi por princípio. Dados bancários não devem trafegar para fora do perímetro da rede, mesmo em ambiente de PoC. Usando um modelo local, nenhuma linha de dado chega a um servidor externo.

Em ambiente Docker, o Ollama sobe como um serviço separado no mesmo `docker-compose.yml` do pipeline. O modelo configurado em `OLLAMA_MODEL` no `.env` é baixado automaticamente no primeiro boot via `ollama pull` — sem precisar embutir o modelo na imagem e sem aumentar o tamanho do build. Nas reinicializações seguintes, o modelo já está no volume `ollama_models` e não precisa ser baixado novamente.

O caminho de evolução para produção está documentado em [MIGRATION_PLAN.md](MIGRATION_PLAN.md): Azure OpenAI em Private Endpoint ou Databricks Model Serving substituem o Ollama com mudança de configuração, sem alterar a lógica do pipeline.

---

## Onde a SLM entra no pipeline

A SLM é chamada depois do profiling e depois da promoção para Silver, nunca antes. Ela não vê o dado bruto — recebe o Manifest e as estatísticas agregadas geradas pelo DuckDB sobre o Parquet do Silver. Isso é deliberado: a SLM documenta com base em metadados, não em dados sensíveis linha a linha.

```
Validator (PASS ou WARNING)
        |
  Profiler (DuckDB gera estatísticas sobre o Parquet Silver)
        |
  SLM recebe: Manifest + estatísticas por coluna
        |
  SLM produz: documentação Markdown por tabela
        |
  Arquivo salvo em data/reports/<tabela>_documentation.md
```

---

## O que a SLM recebe

Dois insumos chegam combinados no prompt. O primeiro é o Manifest completo da tabela — incluindo o `business_context` se já foi validado pelo Data Steward e as `regulatory_flags` identificadas para cada coluna. O segundo é um resumo das estatísticas do profiler, limitado ao essencial para não exceder o contexto do modelo: tipo de dado, percentual de nulos, min, max e os cinco valores mais frequentes por coluna.

Quando uma coluna tem percentual de nulos acima do limiar configurado em `NULL_TOLERANCE_PCT` (padrão 30%), a anomalia é destacada explicitamente no resumo enviado à SLM.

---

## O que a SLM produz

Para cada tabela, um arquivo Markdown é gravado em `data/reports/<tabela>_documentation.md`. O documento descreve o propósito de cada coluna cruzando o contrato declarado com o comportamento observado, aponta anomalias como nulos acima do esperado ou distribuições suspeitas, mapeia chaves de negócio e termina com uma seção de Pontos de Atenção.

Todo arquivo gerado carrega ao final a marcação:

```
> [AI_METADATA_STATUS: DRAFT] — Documentação gerada por SLM.
> Requer validação humana antes de uso em produção.
```

Essa tag nunca é removida automaticamente. Ela só deixa de aparecer como alerta no pipeline quando o Manifest correspondente é promovido para `VALIDATED` pelo Data Steward.

---

## A regra que define o comportamento da SLM

O system prompt instrui o modelo de forma explícita:

> "Se o Manifest contiver um campo `business_context`, use-o como verdade absoluta e expanda — nunca contradiga o que foi declarado pelo Data Steward. Não invente informações não presentes nos dados ou no Manifest."

Isso inverte a relação ingênua entre IA e documentação. A SLM não é a fonte da verdade, ela é uma assistente de redação que parte do que o Steward já validou. Quando o Manifest ainda está em `DRAFT`, ela tem mais liberdade para sugerir — mas a sugestão nunca vira fato sem revisão humana.

---

## O que acontece sem o Ollama disponível

O pipeline nunca falha por ausência da SLM. Antes de qualquer chamada, o módulo verifica se o serviço está acessível. Se não estiver, grava um stub explicando a ausência, registra o status como `SKIPPED` nas métricas e segue para o próximo passo.

Em ambiente Docker, o container `nimbus` só sobe depois que o `ollama` passa no healthcheck — o pipeline não começa enquanto o serviço não está pronto. Se quiser desativar o enriquecimento semântico completamente sem desligar o Ollama, basta setar `SKIP_SLM=true` no `.env`.

---

## Configuração

Tudo que pode ser ajustado fica em `.env` ou em variáveis de ambiente:

`OLLAMA_MODEL` define qual modelo é usado. O padrão é `phi3.5`, leve e adequado para CPU. Para máquinas com GPU, `qwen2.5-coder:7b` ou `phi4` oferecem melhor qualidade. O modelo é baixado automaticamente no primeiro boot — basta trocar o valor no `.env` e reiniciar o container.

`SKIP_SLM` desativa o enriquecimento completamente sem afetar o restante do pipeline — útil para execuções rápidas onde a documentação não é o objetivo.

`NULL_TOLERANCE_PCT` controla a partir de que percentual de nulos a SLM recebe um alerta explícito sobre a coluna. O padrão é 30%.

`OLLAMA_NUM_PARALLEL` e `OLLAMA_MAX_LOADED_MODELS` controlam o paralelismo do Ollama — mantidos em 1 por padrão para não estourar RAM em ambientes sem GPU. Aumente se tiver recursos disponíveis.
