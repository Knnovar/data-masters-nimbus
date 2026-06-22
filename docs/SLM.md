# A SLM no Projeto Nimbus

Este documento explica o papel da Small Language Model (SLM) na arquitetura,
o que ela recebe, o que produz, e onde encaixa no fluxo de dados.

---

## 1. Por que SLM e não LLM de nuvem

O projeto usa **Ollama local** rodando um modelo pequeno (`phi3.5` ou
`qwen2.5-coder:7b`), não uma API de LLM externa. Três razões:

1. **Zero egress de dados** — nenhuma informação bancária trafega para fora
   do perímetro da rede, mesmo em ambiente de PoC
2. **Custo previsível** — sem cobrança por token, viável para rodar a cada
   execução de pipeline
3. **Caminho de produção claro** — em Databricks, o mesmo papel é cumprido
   por Model Serving ou Azure OpenAI em Private Endpoint (ver
   [MIGRATION_PLAN.md](MIGRATION_PLAN.md))

---

## 2. Onde a SLM entra no pipeline

```
Validator (PASS/WARNING) → Profiler (DuckDB) → SLM → Reports
                                                  │
                              recebe: Manifest VALIDATED/DRAFT
                                    + estatísticas do Profiler
                                                  │
                                            gera: Markdown
                                          documentado por coluna
```

A SLM é chamada **depois** do profiling, nunca antes. Ela nunca vê o dado
bruto — apenas o manifest (contrato declarado) e as estatísticas agregadas
(min, max, % nulos, top valores). Isso é deliberado: a SLM documenta com
base em metadados, não em dados sensíveis linha a linha.

---

## 3. O que a SLM recebe

Dois insumos combinados em um único prompt:

**1. O Manifest** (contrato YAML completo ou parcial)
```yaml
business_context: "Tabela mestre de clientes..."
regulatory: { tags: [LGPD, SCR] }
schema:
  - name: vl_renda_mensal
    description: "Renda mensal declarada em BRL."
```

**2. As estatísticas do Profiler** (resumidas para caber no contexto)
```json
{
  "vl_renda_mensal": {
    "dtype": "float", "null_pct": 12.4,
    "min": 800.0, "max": 95000.0, "mean": 6200.5
  }
}
```

---

## 4. O que a SLM produz

Um documento Markdown por tabela, salvo em `data/reports/<tabela>_documentation.md`,
contendo:

- Descrição de cada coluna (propósito de negócio + comportamento observado)
- Anomalias detectadas (ex: % de nulos acima do esperado)
- Mapeamento de chaves de negócio e suas implicações
- Seção final de **Pontos de Atenção** com os principais riscos

Toda documentação gerada carrega a tag obrigatória:

```
> **[AI_METADATA_STATUS: DRAFT]** — Documentação gerada por SLM.
> Requer validação humana antes de uso em produção.
```

Essa tag nunca é removida automaticamente — só some quando o manifest
correspondente é promovido para `VALIDATED` pelo Data Steward.

---

## 5. Regra de ouro do prompt: a SLM não inventa

O system prompt instrui explicitamente o modelo:

> *"Se o manifesto contiver um campo `business_context`, use-o como verdade
> absoluta e expanda — nunca contradiga o que foi declarado pelo Data
> Steward. Não invente informações não presentes nos dados ou no manifesto."*

Isso inverte a relação ingênua entre IA e documentação: a SLM não é a fonte
da verdade, ela é uma **assistente de redação** que parte do que o Steward
já validou. Quando o manifest ainda está em `DRAFT`, a SLM tem mais liberdade
para sugerir — mas a sugestão nunca vira fato sem revisão humana.

---

## 6. Comportamento sem Ollama disponível

O projeto nunca quebra se o Ollama não estiver rodando. `enrich()` verifica
disponibilidade antes de qualquer chamada:

```python
if not _is_ollama_available():
    # grava um stub explicando a ausência, status = SKIPPED
    # o pipeline continua normalmente
```

Isso é o que permite rodar a PoC completa em qualquer máquina, com ou sem
GPU, com ou sem o modelo baixado — a documentação fica pendente, mas nada
trava.

---

## 7. Configuração

| Parâmetro (`config.py`) | Padrão | Efeito |
|---|---|---|
| `OLLAMA_MODEL` | `qwen2.5-coder:7b` | Troque por `phi3.5` para melhor custo/benefício em CPU |
| `SKIP_SLM` | `False` | `True` desativa completamente sem alterar o resto do pipeline |
| `OLLAMA_HOST` | `http://localhost:11434` | Endpoint do servidor Ollama |
| `NULL_TOLERANCE_PCT` | `30.0` | % de nulos acima do qual a SLM reporta como anomalia |

---

## 8. Caminho para produção

Três opções avaliadas para substituir o Ollama local em ambiente Databricks:

| Opção | Quando escolher |
|---|---|
| **Azure OpenAI (Private Endpoint)** | Preferida — já é o cloud provider do banco |
| **Databricks Model Serving** | Se o modelo precisar de fine-tuning no domínio bancário |
| **VM Azure NC-series com Ollama** | Transição mais direta, menor mudança de código |

Em todos os casos, `MLflow Tracing` é o mecanismo de auditoria para
compliance BACEN — cada chamada à SLM fica registrada e rastreável.
