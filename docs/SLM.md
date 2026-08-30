# A SLM no Projeto Nimbus

Este documento explica o papel da Small Language Model na arquitetura do Nimbus: o que ela recebe, o que produz e por que foi uma escolha deliberada usar um modelo local em vez de uma API de nuvem.

---

## Por que modelo local e não uma API externa

A escolha pelo Ollama rodando localmente não foi por limitação técnica — foi por princípio. Dados bancários não devem trafegar para fora do perímetro da rede, mesmo em ambiente de PoC. Usando um modelo local, nenhuma linha de dado chega a um servidor externo. O processamento acontece inteiramente na máquina.

Há também a questão de custo previsível: sem cobrança por token, o enriquecimento pode rodar a cada execução sem gerar uma conta variável ao fim do mês.

E há um caminho claro de evolução: quando o projeto migrar para Azure Databricks, a SLM local é substituída por Azure OpenAI em Private Endpoint ou Databricks Model Serving — sem sair do perímetro e sem mudar a lógica do pipeline. A configuração é de uma linha. O detalhamento desse caminho está em [MIGRATION_PLAN.md](MIGRATION_PLAN.md).

---

## Onde a SLM entra no pipeline

A SLM é chamada depois do profiling, nunca antes. Ela não vê o dado bruto — recebe o Manifest (contrato declarado) e as estatísticas agregadas geradas pelo DuckDB. Isso é deliberado: a SLM documenta com base em metadados, não em dados sensíveis linha a linha.

```
Validator (PASS ou WARNING)
        |
  Profiler (DuckDB gera estatísticas por coluna)
        |
  SLM recebe: Manifest + estatísticas
        |
  SLM produz: documentação Markdown por tabela
        |
  Arquivo salvo em data/reports/
```

---

## O que a SLM recebe

Dois insumos chegam combinados no prompt. O primeiro é o Manifest completo da tabela — ou pelo menos a parte preenchida até o momento, incluindo o `business_context` se já foi validado pelo Data Steward e as `regulatory_flags` identificadas para cada coluna. O segundo é um resumo das estatísticas do profiler, limitado ao essencial para não exceder o contexto do modelo: tipo de dado, percentual de nulos, min, max e os cinco valores mais frequentes por coluna.

Quando a coluna tem um percentual de nulos acima do limiar configurado em `NULL_TOLERANCE_PCT` (padrão 30%), essa anomalia é destacada explicitamente no resumo enviado à SLM.

---

## O que a SLM produz

Para cada tabela, um arquivo Markdown é gravado em `data/reports/<tabela>_documentation.md`. O documento descreve o propósito de cada coluna cruzando o contrato declarado com o comportamento observado, aponta anomalias como nulos acima do esperado ou distribuições suspeitas, mapeia as chaves de negócio e termina com uma seção de Pontos de Atenção.

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

## O que acontece sem o Ollama rodando

O pipeline nunca falha por ausência da SLM. Antes de qualquer chamada, o módulo verifica se o serviço está disponível. Se não estiver, grava um arquivo de stub explicando a ausência, registra o status como `SKIPPED` nos métricas e segue para o próximo passo. Isso permite rodar a PoC inteiramente em qualquer máquina, com ou sem GPU, com ou sem o modelo baixado.

Para ativar o enriquecimento semântico, basta ter o Ollama em execução:

```bash
ollama serve
ollama pull phi3.5
```

---

## Configuração

Tudo o que pode ser ajustado fica em `config.py`:

`OLLAMA_MODEL` define qual modelo é usado. O padrão é `qwen2.5-coder:7b`, mas `phi3.5` oferece melhor custo-benefício em máquinas sem GPU. `SKIP_SLM` desativa o enriquecimento completamente sem tocar no restante do pipeline — útil para testes rápidos onde a documentação não é relevante. `NULL_TOLERANCE_PCT` controla a partir de que percentual de nulos a SLM recebe um alerta explícito na coluna.
