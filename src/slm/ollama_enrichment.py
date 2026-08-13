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

from config import OLLAMA_HOST, OLLAMA_MODEL, NULL_TOLERANCE_PCT, SKIP_SLM

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
    try:
        response = requests.post(
            f"{OLLAMA_HOST}/api/chat",
            json={
                "model"  : OLLAMA_MODEL,
                "stream" : False,
                "options": {"temperature": 0.2, "num_predict": 800},
                "messages": [
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user",   "content": user_prompt},
                ],
            },
            timeout=600,
        )
        response.raise_for_status()
        doc    = response.json()["message"]["content"]
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

    if status == "SUCCESS":
        print(f"   [SLM] [{table}] Documentacao gerada em {elapsed_ms} ms -> reports/{report_filename}")

    return {
        "table"             : table,
        "status"            : status,
        "inference_ms"      : elapsed_ms,
        "documentation"     : doc,
        "ai_metadata_status": "DRAFT",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Helpers internos
# ─────────────────────────────────────────────────────────────────────────────

def _skipped(table: str) -> dict:
    return {"table": table, "status": "SKIPPED", "inference_ms": 0,
            "documentation": _stub_doc(table), "ai_metadata_status": "DRAFT"}


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
