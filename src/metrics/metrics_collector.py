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

from src.validation.validator import ValidationResult


def _compute_quality_score(val_result: ValidationResult, profiler_payload: dict) -> float:
    """
    Score de qualidade 0–100 baseado em:
      - 40 pts: status de validação
      - 30 pts: taxa de nulos global
      - 20 pts: taxa de duplicatas
      - 10 pts: cobertura de schema (colunas esperadas presentes)
    """
    score = 0.0

    # Validação
    if val_result.status == "PASS"   : score += 40
    elif val_result.status == "WARNING": score += 25
    # DLQ → 0

    # Nulos globais
    cols = profiler_payload.get("columns", {})
    if cols:
        avg_null = sum(c.get("null_pct", 0) for c in cols.values()) / len(cols)
        score += max(0, 30 - avg_null)    # 30 pts se nulos = 0

    # Duplicatas
    total = val_result.rows_total or 1
    dup_pct = val_result.duplicate_count / total * 100
    score += max(0, 20 - dup_pct * 10)

    # Schema coverage (bonus estático)
    if val_result.evolution_type is None:
        score += 10

    return round(min(score, 100), 1)


def collect(
    run_id          : str,
    val_result      : ValidationResult,
    profiler_payload: dict,
    slm_result      : dict,
    metrics_dir     : Path,
) -> dict:
    """Salva métricas individuais de uma tabela e retorna o dict."""

    quality_score = _compute_quality_score(val_result, profiler_payload)

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
        "slm_status"         : slm_result.get("status"),
        "slm_inference_ms"   : slm_result.get("inference_ms", 0),
        "quality_score"      : quality_score,
        "issues"             : val_result.issues,
        "warnings"           : val_result.warnings,
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
        f"# Pipeline Data Masters - Relatorio de Execucao",
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
