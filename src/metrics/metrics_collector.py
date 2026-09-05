"""
Coleta e consolida métricas de cada execução da pipeline.

Produz:
  - metrics/run_<timestamp>.json  → histórico por run
  - metrics/summary.json          → acumulado de todas as runs
  - reports/pipeline_report.md    → relatório legível
"""

import json
from datetime import datetime
from pathlib import Path
from src.metrics import quality_score
from src.validation.validator import ValidationResult

def _slm_metrics(slm_result: dict) -> dict:
    """Achata perf/output do enriquecimento para comparar modelos entre runs.
    
    Campos planos (nao aninhados) porque o show_metrics.py e o export CSV
    consomem o registro como uma linha"""
    perf = slm_result.get("perf") or {}
    out = slm_result.get("output") or {}
    return {
        "slm_model"             : slm_result.get("model"),
        "slm_num_predict"       : slm_result.get("num_predict"),
        "slm_total_ms"          : perf.get("total_ms"),
        "slm_load_ms"           : perf.get("load_ms"),
        "slm_prompt_tokens"        : perf.get("prompt_tokens"),
        "slm_prompt_eval_ms"     : perf.get("prompt_eval_ms"),
        "slm_output_tokens"        : perf.get("output_tokens"),
        "slm_eval_ms"           : perf.get("eval_ms"),
        "slm_tokens_per_s"          : perf.get("tokens_per_s"),
        "slm_truncated"         : perf.get("truncated"),
        "slm_output_chars"        : out.get("chars"),
        "slm_output_words"        : out.get("words"),
        "slm_column_coverage_pct" : out.get("column_coverage_pct"),
        "slm_columns_missing"       : out.get("columns_missing"),
        "slm_has_pontos_atencao"      : out.get("has_pontos_atencao"),
        "slm_has_draft_tag"         : out.get("has_draft_tag"),
    }
    
def collect(
    run_id          : str,
    val_result      : ValidationResult,
    profiler_payload: dict,
    slm_result      : dict,
    metrics_dir     : Path,
    contract        = None,
    cast_report     : dict | None = None,
) -> dict:
    """Salva métricas individuais de uma tabela e retorna o dict."""

    score = quality_score.compute(val_result, profiler_payload, contract, cast_report)

    # Nulos por coluna
    cols          = profiler_payload.get("columns", {})
    null_summary  = {c: v.get("null_pct", 0) for c, v in cols.items()}
    avg_null      = round(sum(null_summary.values()) / len(null_summary), 2) if null_summary else 0

    record = {
        "run_id"             : run_id,
        "timestamp"          : datetime.now().isoformat(),
        "table"              : val_result.table,
        "scenario"           : val_result.scenario,
        "validation_status"  : val_result.status,
        "evolution_type"     : val_result.evolution_type,
        "rows_total"         : val_result.rows_total,
        "rows_valid"         : val_result.rows_valid,
        "duplicate_count"    : val_result.duplicate_count,
        "null_violations"    : val_result.null_violations,
        "avg_null_pct"       : avg_null,
        "profiling_ms"       : profiler_payload.get("profiling_ms", 0),
        "quality_score"      : quality_score,
        "issues"             : val_result.issues,
        "warnings"           : val_result.warnings,
        "slm_status"         : slm_result.get("status"),
        "slm_inference_ms"   : slm_result.get("inference_ms", 0),
        **_slm_metrics(slm_result),
        "quality_score"      : score["score"],
        "quality_dimensions" : score["dimensions"],
        **{f"score_{n}": d["value"] for n, d in score["dimensions"].items()},
    }

    # Persiste JSON por run
    path = metrics_dir / f"{run_id}_{val_result.table}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)

    return record


def generate_report(all_metrics: list[dict], reports_dir: Path) -> Path:
    """Gera relatório Markdown consolidado da execução."""

    now   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        f"# Pipeline Projeto Nimbus - Relatorio de Execucao",
        f"**Data:** {now}  |  **Run ID:** `{all_metrics[0]['run_id'] if all_metrics else 'N/A'}`\n",
        "---\n",
        "## Resumo por Tabela\n",
        "| Tabela | Cenário | Status | Linhas | Dups | Nulos (avg%) | Profiling (ms) | SLM (ms) | Score |",
        "|--------|---------|--------|--------|------|--------------|----------------|----------|-------|",
    ]

    for m in all_metrics:
        status_icon = {"PASS": "[PASS]", "WARNING": "[WARN]", "DLQ": "[DLQ]"}.get(m["validation_status"], "[?]")
        slm_icon    = {"SUCCESS": "[OK]", "SKIPPED": "[SKIP]", "ERROR": "[ERR]"}.get(m["slm_status"], "[-]")
        lines.append(
            f"| `{m['table']}` | {m['scenario']} | {status_icon} {m['validation_status']} "
            f"| {m['rows_total']:,} | {m['duplicate_count']} | {m['avg_null_pct']}% "
            f"| {m['profiling_ms']} | {slm_icon} {m['slm_inference_ms']} | **{m['quality_score']}** |"
        )

    # Médias
    scores = [m["quality_score"] for m in all_metrics]
    avg_score = round(sum(scores) / len(scores), 1) if scores else 0

    lines += [
        "\n---\n",
        f"## Qualidade Geral da Execução\n",
        f"- **Score medio:** `{avg_score}/100`",
        f"- **Tabelas processadas:** {len(all_metrics)}",
        f"- **Com DLQ:** {sum(1 for m in all_metrics if m['validation_status'] == 'DLQ')}",
        f"- **Com WARNING:** {sum(1 for m in all_metrics if m['validation_status'] == 'WARNING')}",
        f"- **Documentadas por SLM:** {sum(1 for m in all_metrics if m['slm_status'] == 'SUCCESS')}",
        "\n---\n",
        "## Score por Dimensao\n",
        "| Tabela | Conformidade (40%) | Completude (25%) | Unicidade (20%) | Estabilidade (15%) | Score |",
        "|--------|--------------------|------------------|-----------------|--------------------|-------|",
    ]
    for m in all_metrics:
        dims = m.get("quality_dimensions") or {}
        def _v(name):
            v = (dims.get(name) or {}).get("value")
            return "n/d" if v is None else f"{v:.1f}"
        lines.append(
            f"| `{m['table']}` | {_v('conformity')} | {_v('completeness')} "
            f"| {_v('uniqueness')} |  {_v('schema_stability')} | **{m['quality_score']}** |"
        )
    lines.append("")
    for m in all_metrics:
        dims=m.get("quality_dimensions") or {}
        low = [(n, d) for n, d in dims.items() if d.get("value") is not None and d["value"] < 100]
        for name, d in low:
            lines.append(f"- ``{m['table']}` / **{name}** = {d['value']}: {d.get('detail', '')}")
    lines += [
        "\n---\n",
        "## Desempenho da SLM\n",
        ]
    slm_rows = [m for m in all_metrics if m.get("slm_status") == "SUCCESS" and m.get("slm_model")]
    if slm_rows:
        lines += [
            "| Tabela | Modelo | Wall (ms) | Carga (ms) | Prompt (Tok/ms) | Saida (tok/ms) | Tok/s | Cobertura | Truncado |",
            "|--------|--------|-----------|------------|-----------------|----------------|-------|-----------|----------|",
        ]
        for m in slm_rows:
            lines.append(
                f"| `{m['table']}` | {m['slm_model']} | {m['slm_inference_ms']:,.0f} "
                f"| {m.get('slm_load_ms') or 0:,.0f} "
                f"| {m.get('slm_prompt_tokens') or 0}/{m.get('slm_prompt_eval_ms') or 0:,.0f} "
                f"| {m.get('slm_output_tokens') or 0}/{m.get('slm_eval_ms') or 0:,.0f} "
                f"| **{m.get('slm_tokens_per_s') or 0:,.1f}** "
                f"| {m.get('slm_column_coverage_pct') or 0}% "
                f"| {'sim' if m.get('slm_truncated') else 'nao'} |"
            )
        lines.append(
            "\n> Compare modelos com `python show_metrics.py --models` "
            "(agrega todas as runs por `slm_model`)."
        )
    else:
        lines.append("Nenhuma inferencia bem-sucedida nesta execucao. \n")
    lines += [
        "\n---\n",
        "## Detalhes por Tabela\n",
    ]

    for m in all_metrics:
        lines.append(f"### `{m['table']}`")
        if m["issues"]:
            lines.append("**Issues criticos:**")
            for i in m["issues"]:
                lines.append(f"- [ERR] {i}")
        if m["warnings"]:
            lines.append("**Warnings:**")
            for w in m["warnings"]:
                lines.append(f"- [WARN] {w}")
        if m["null_violations"]:
            lines.append(f"**Nulos em colunas obrigatorias:** {m['null_violations']}")
        lines.append("")

    lines += [
        "---",
        "> AVISO: Toda documentacao gerada pela SLM possui status **[AI_METADATA_STATUS: DRAFT]**.",
        "> Requer validação humana pelo Data Steward antes de uso em produção.",
    ]

    report_path = reports_dir / "pipeline_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\n   [REPORT] Relatorio salvo em: {report_path}")
    return report_path
