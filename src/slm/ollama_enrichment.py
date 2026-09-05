"""
Enriquecimento semântico via SLM local (Ollama).

Recebe o storage diretamente — lê o contrato via storage.read_path()
e grava a documentação via storage.write_text(), sem depender de Path
local. Funciona com LocalStorage e MinIOStorage sem alteração.

A documentação gerada recebe obrigatoriamente a tag:
    [AI_METADATA_STATUS: DRAFT]
"""

import json
import time

import requests
import yaml

from config import OLLAMA_HOST, OLLAMA_MODEL, NULL_TOLERANCE_PCT, SKIP_SLM, SLM_NUM_PREDICT as NUM_PREDICT

_SYSTEM_PROMPT = """Você é um Data Steward sênior de um banco brasileiro regulado pelo Banco Central.
Você conhece os padrões de nomenclatura de dados financeiros brasileiros:
- Prefixos: cd_ (código), nm_ (nome), vl_ (valor monetário), dt_ (data),
  fl_ (flag booleano), nr_ (número), tx_ (taxa), tp_ (tipo), id_ (identificador)

Seu trabalho é analisar o contrato de dados YAML (intenção declarada) junto
com as estatísticas reais do Data Profiler (realidade observada) e produzir
um dicionário técnico estruturado em Markdown.

Regras obrigatórias:
1. Se o manifesto contiver um campo business_context, use-o como verdade absoluta
   e expanda — nunca contradiga o que foi declarado pelo Data Steward.
2. Se o manifesto contiver description nas colunas, use como base e complemente
   com as estatísticas — não substitua.
3. Descreva cada coluna: propósito de negócio, tipo, comportamento esperado.
4. Sinalize anomalias claras (ex: alto % de nulos, valores fora de faixa, duplicatas).
5. Se houver regulatory_tags no manifesto, mencione as implicações de compliance.
6. Seja objetivo e técnico. Escreva em português brasileiro.
7. NAO invente informações não presentes nos dados ou no manifesto.
8. Conclua com uma seção Pontos de Atencao listando os principais riscos."""

_USER_TEMPLATE = """## Contrato YAML:
```yaml
{yaml_content}
```

## Estatísticas do Data Profiler:
```json
{profiler_json}
```

Gere o dicionário técnico completo da tabela `{table_name}`.
Ao final, adicione obrigatoriamente:

---
> **[AI_METADATA_STATUS: DRAFT]** — Documentação gerada por SLM. Requer validação humana pelo Data Steward responsável antes de uso em produção."""


def _is_ollama_available() -> bool:
    try:
        r = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


def enrich(storage, contract_filename: str, profiler_payload: dict) -> dict:
    """
    Gera documentação semântica da tabela via SLM local.

    Recebe o storage diretamente — lê o contrato de 'contracts' e
    grava a documentação em 'reports', sem Path local explícito.

    Retorna:
        {
            "table": ...,
            "status": "SUCCESS" | "SKIPPED" | "ERROR",
            "inference_ms": ...,
            "documentation": "... markdown ...",
            "ai_metadata_status": "DRAFT"
        }
    """
    table           = profiler_payload["table"]
    report_filename = f"{table}_documentation.md"

    # SKIP_SLM desativa o enriquecimento sem alterar o resto do pipeline
    if SKIP_SLM:
        print(f"   [SKIP] [{table}] SLM desativado via SKIP_SLM=True")
        storage.write_text("reports", report_filename, _stub_doc(table))
        return _skipped(table)

    if not _is_ollama_available():
        print(f"   [SKIP] [{table}] Ollama indisponivel - enriquecimento ignorado")
        storage.write_text("reports", report_filename, _stub_doc(table))
        return _skipped(table)

    # Carrega contrato do layer contracts via storage
    contract_path = storage.read_path("contracts", contract_filename)
    with open(contract_path, encoding="utf-8") as f:
        yaml_content = f.read()

    profiler_summary = _summarize_profiler(profiler_payload)
    user_prompt = _USER_TEMPLATE.format(
        yaml_content  = yaml_content,
        profiler_json = json.dumps(profiler_summary, ensure_ascii=False, indent=2),
        table_name    = table,
    )

    t0 = time.perf_counter()
    payload={}
    try:
        response = requests.post(
            f"{OLLAMA_HOST}/api/chat",
            json={
                "model"  : OLLAMA_MODEL,
                "stream" : False,
                "options": {"temperature": 0.2, "num_predict": NUM_PREDICT},
                "messages": [
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user",   "content": user_prompt},
                ],
            },
            timeout=600,
        )
        response.raise_for_status()
        payload = response.json()
        doc    = payload["message"]["content"]
        status = "SUCCESS"
    except Exception as e:
        doc    = f"Erro na inferencia SLM: {e}\n\n> **[AI_METADATA_STATUS: DRAFT]**"
        status = "ERROR"
        print(f"   [ERROR] [{table}] Ollama: {e}")

    elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)

    if "[AI_METADATA_STATUS: DRAFT]" not in doc:
        doc += "\n\n---\n> **[AI_METADATA_STATUS: DRAFT]**"

    # Grava documentação no layer reports via storage
    storage.write_text("reports", report_filename, doc)
    perf = _perf_metrics(payload, elapsed_ms)
    out = _output_metrics(doc, yaml_content)

    if status == "SUCCESS":
        tokens = (f"{perf['output_tokens']} tok" if perf["output_tokens"] is not None 
                  else f"~{out['output_tokens_est']} tok (est)")
        speed = f"{perf['tokens_per_s']} tok/s" if perf["tokens_per_s"] else "tok/s n/d"
        trunc = "| TRUNCADO" if perf["truncated"] else ""
        print(f"   [SLM] [{table}] {OLLAMA_MODEL}: {elapsed_ms} ms | {tokens} | {speed} | "
              f"cobertura {out['column_coverage_pct']}%{trunc} -> reports/{report_filename}")

    return {
        "table"             : table,
        "status"            : status,
        "inference_ms"      : elapsed_ms,
        "documentation"     : doc,
        "ai_metadata_status": "DRAFT",
        "model"             : OLLAMA_MODEL,
        "num_predict"       : NUM_PREDICT,
        "perf"              : perf,
        "output"            : out,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Helpers internos
# ─────────────────────────────────────────────────────────────────────────────

def _skipped(table: str) -> dict:
    return {"table": table, "status": "SKIPPED", "inference_ms": 0,
            "documentation": _stub_doc(table), "ai_metadata_status": "DRAFT",
            "model": OLLAMA_MODEL, "num_predict": NUM_PREDICT, "perf": _perf_metrics({}, 0), "output": _output_metrics("", "")}

def _perf_metrics(payload: dict, wall_ms: float) -> dict:
    """Tempos reportados pelo Ollama (ns) normalizados em ms + throughput (tokens/s).
    
    Permite comparar modelos separando carga do modelo (load_ms), leitura do 
    prompt(prompt_eval_ms) e geração do output (eval_ms) - o wall_ms sozinho mistura os
    tres e penaliza o primeiro run de cada modelo."""
    def _ms(key):
        v=payload.get(key)
        return round(v / 1_000_000, 1) if isinstance(v, (int, float)) else None
    eval_ms = _ms("eval_duration")
    out_tokens = payload.get("eval_count")
    tokens_per_s = None
    if isinstance(out_tokens, int) and eval_ms:
        tokens_per_s = round(out_tokens / (eval_ms / 1000), 1)
    return {
        "wall_ms"      : wall_ms,
        "total_ms"     : _ms("total_duration"),
        "load_ms"      : _ms("load_duration"),
        "prompt_tokens"  : payload.get("prompt_eval_count"),
        "prompt_eval_ms" : _ms("prompt_eval_duration"),
        "output_tokens"  : out_tokens,
        "eval_ms"      : eval_ms,
        "tokens_per_s"  : tokens_per_s,
        "done_reason"    : payload.get("done_reason"),
        "truncated"      : payload.get("done_reason") == "length",
    }
def _output_metrics(doc: str, yaml_content: str) -> dict:
    """Caracteristicas da resposta - o que compara qualidade entre modelos.
    
    column_coverage_pct e o percentual de colunas do contrato citadas na
    documentacao; truncated indica resposta cortada pelo num_predict"""

    columns = []
    if yaml_content:
        try:
            parsed = yaml.safe_load(yaml_content) or {}
            columns = [c.get("name") for c in (parsed.get("schema") or [])
                       if isinstance(c, dict) and c.get("name")]
        except Exception:
            columns = []
    cited = [c for c in columns if c in doc]
    words = doc.split()

    return {
        "chars"              : len(doc),
        "words"              : len(words),
        "lines"              : doc.count("\n") + 1 if doc else 0,
        "headings"           : sum(1 for ln in doc.splitlines() if ln.startswith("#")),
        "output_tokens_est"  : round(len(words) * 1.3) if words else 0,
        "columns_total"          : len(columns),
        "columns_cited"          : len(cited),
        "column_coverage_pct"    : round(len(cited) / len(columns) * 100, 1) if columns else 0.0,
        "columns_missing"          : [c for c in columns if c not in doc],
        "has_pontos_atencao"          : "pontos de aten" in doc.lower(),
        "has_draft_tag"          : "[AI_METADATA_STATUS: DRAFT]" in doc,
    }

def _stub_doc(table: str) -> str:
    return (
        f"# Documentacao: {table}\n\n"
        "Ollama nao estava disponivel durante a execucao.\n"
        "Execute `ollama serve` e rode o pipeline novamente.\n\n"
        "---\n> **[AI_METADATA_STATUS: DRAFT]**"
    )


def _summarize_profiler(payload: dict) -> dict:
    """Reduz o payload para o essencial, evitando exceder o contexto da SLM."""
    summary = {"table": payload["table"], "rows": payload["rows"], "columns": {}}
    for col, stats in payload["columns"].items():
        col_summary = {
            "dtype"       : stats.get("dtype"),
            "null_pct"    : stats.get("null_pct"),
            "unique_count": stats.get("unique_count"),
        }
        if "min" in stats:
            col_summary.update({"min": stats["min"], "max": stats["max"], "mean": stats["mean"]})
        if "top_values" in stats:
            col_summary["top_values"] = stats["top_values"][:3]
        if (stats.get("null_pct") or 0) > NULL_TOLERANCE_PCT:
            col_summary["ANOMALIA"] = f"null_pct {stats['null_pct']}% acima do limiar {NULL_TOLERANCE_PCT}%"
        summary["columns"][col] = col_summary
    return summary
