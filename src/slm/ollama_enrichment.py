"""
Enriquecimento semântico via SLM local (Ollama).

Combina o manifesto YAML (intenção) com o payload do Profiler
(realidade estatística) e gera documentação técnica em Markdown,
anotando anomalias detectadas.

A documentação gerada recebe obrigatoriamente a tag:
    [AI_METADATA_STATUS: DRAFT]
"""

import json
import time
from pathlib import Path
from typing import Optional

import requests
import yaml

from config import OLLAMA_HOST, OLLAMA_MODEL, NULL_TOLERANCE_PCT

_SYSTEM_PROMPT = """Você é um Data Steward sênior de um banco brasileiro.
Seu trabalho é analisar o contrato de dados YAML (intenção declarada) junto
com as estatísticas reais do Data Profiler (realidade observada) e produzir
um dicionário técnico estruturado em Markdown.

Regras obrigatórias:
1. Descreva cada coluna: propósito de negócio, tipo, comportamento esperado.
2. Sinalize anomalias claras (ex: alto % de nulos, valores fora de faixa, chaves duplicadas).
3. Mapeie o comportamento das chaves de negócio e suas implicações.
4. Seja objetivo e técnico. Evite jargões desnecessários.
5. Escreva em português brasileiro.
6. NÃO invente informações não presentes nos dados fornecidos.
7. Conclua com uma seção "⚠️ Pontos de Atenção" listando os principais riscos."""

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


def enrich(
    contract_path : Path,
    profiler_payload: dict,
    reports_dir   : Path,
) -> dict:
    """
    Chama o Ollama para gerar documentação semântica da tabela.

    Retorna:
        {
            "table": ...,
            "status": "SUCCESS" | "SKIPPED" | "ERROR",
            "inference_ms": ...,
            "documentation": "... markdown ...",
            "ai_metadata_status": "DRAFT"
        }
    """
    table = profiler_payload["table"]

    if not _is_ollama_available():
        print(f"   ⏭️   [{table}] Ollama indisponível — enriquecimento ignorado")
        _write_stub(table, reports_dir)
        return {
            "table"             : table,
            "status"            : "SKIPPED",
            "inference_ms"      : 0,
            "documentation"     : _stub_doc(table),
            "ai_metadata_status": "DRAFT",
        }

    # Carrega o contrato YAML original
    with open(contract_path, encoding="utf-8") as f:
        yaml_content = f.read()

    # Serializa payload do profiler (limitado para não estourar contexto da SLM)
    profiler_summary = _summarize_profiler(profiler_payload)

    user_prompt = _USER_TEMPLATE.format(
        yaml_content   = yaml_content,
        profiler_json  = json.dumps(profiler_summary, ensure_ascii=False, indent=2),
        table_name     = table,
    )

    t0 = time.perf_counter()
    try:
        response = requests.post(
            f"{OLLAMA_HOST}/api/chat",
            json={
                "model"   : OLLAMA_MODEL,
                "stream"  : False,
                "options" : {"temperature": 0.2, "num_predict": 1500},
                "messages": [
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user",   "content": user_prompt},
                ],
            },
            timeout=120,
        )
        response.raise_for_status()
        doc = response.json()["message"]["content"]
        status = "SUCCESS"
    except Exception as e:
        doc    = f"⚠️ Erro na inferência SLM: {e}\n\n> **[AI_METADATA_STATUS: DRAFT]**"
        status = "ERROR"
        print(f"   ❌  [{table}] Erro Ollama: {e}")

    elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)

    # Garante que a tag DRAFT está presente
    if "[AI_METADATA_STATUS: DRAFT]" not in doc:
        doc += "\n\n---\n> **[AI_METADATA_STATUS: DRAFT]**"

    # Persiste o relatório
    report_path = reports_dir / f"{table}_documentation.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(doc)

    if status == "SUCCESS":
        print(f"   🤖  [{table}] Documentação SLM gerada em {elapsed_ms} ms → {report_path.name}")

    return {
        "table"             : table,
        "status"            : status,
        "inference_ms"      : elapsed_ms,
        "documentation"     : doc,
        "ai_metadata_status": "DRAFT",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def _summarize_profiler(payload: dict) -> dict:
    """Reduz o payload para o essencial, evitando exceder o contexto da SLM."""
    summary = {
        "table"       : payload["table"],
        "rows"        : payload["rows"],
        "columns"     : {},
    }
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
        # Marca anomalia de nulos alta
        if (stats.get("null_pct") or 0) > NULL_TOLERANCE_PCT:
            col_summary["ANOMALIA"] = f"null_pct {stats['null_pct']}% acima do limiar {NULL_TOLERANCE_PCT}%"
        summary["columns"][col] = col_summary
    return summary


def _stub_doc(table: str) -> str:
    return (
        f"# Documentação: {table}\n\n"
        "⚠️ **Ollama não estava disponível durante a execução.**\n"
        "Execute `ollama serve` e rode o pipeline novamente para gerar a documentação semântica.\n\n"
        "---\n> **[AI_METADATA_STATUS: DRAFT]**"
    )


def _write_stub(table: str, reports_dir: Path) -> None:
    path = reports_dir / f"{table}_documentation.md"
    with open(path, "w", encoding="utf-8") as f:
        f.write(_stub_doc(table))
