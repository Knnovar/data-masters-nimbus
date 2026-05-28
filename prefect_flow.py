"""
prefect_flow.py — Orquestração da Pipeline Data Masters via Prefect

Filosofia de design para portabilidade com Control-M:
─────────────────────────────────────────────────────
Cada @task do Prefect corresponde a exatamente um "job" no Control-M.
O mapeamento é intencional e documentado abaixo:

  Prefect Task               → Control-M Job (futuro)
  ─────────────────────────────────────────────────────
  task_generate_data         → JOB-DM-001-GENERATE
  task_validate              → JOB-DM-002-VALIDATE
  task_profile               → JOB-DM-003-PROFILE
  task_enrich_slm            → JOB-DM-004-ENRICH
  task_collect_metrics       → JOB-DM-005-METRICS
  task_report                → JOB-DM-006-REPORT

Cada task:
  - Recebe e retorna dicts serializáveis (sem objetos complexos entre tasks)
  - Emite exit code padronizado via TaskResult.exit_code (0/1/2)
  - Loga para stdout em formato legível por parsers do Control-M
  - É invocável de forma independente via CLI (ver __main__)

Uso:
    # Prefect (com UI local em http://localhost:4200)
    prefect server start          # em outro terminal
    python prefect_flow.py        # registra e executa

    # Sem Prefect (execução direta, compatível com Control-M)
    python prefect_flow.py --no-prefect --scenario baseline
    python prefect_flow.py --no-prefect --scenario all
"""

import argparse
import json
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path

# Torna o projeto importável de qualquer working directory
sys.path.insert(0, str(Path(__file__).parent))

from config import METRICS_DIR, REPORTS_DIR
from src.storage.storage import get_storage
from src.generators.data_generator import generate_all
from src.validation.validator import validate
from src.profiler.duckdb_profiler import profile
from src.slm.ollama_enrichment import enrich
from src.metrics.metrics_collector import collect, generate_report

# Prefect é opcional — sem ele, o flow roda como funções Python normais
try:
    from prefect import flow, task, get_run_logger
    from prefect.context import get_run_context
    _HAS_PREFECT = True
except ImportError:
    _HAS_PREFECT = False
    # Stubs transparentes que tornam os decoradores no-ops
    def flow(*args, **kwargs):
        def decorator(fn): return fn
        return decorator if args and callable(args[0]) else decorator
    def task(*args, **kwargs):
        def decorator(fn): return fn
        return decorator if args and callable(args[0]) else decorator
    def get_run_logger():
        import logging
        return logging.getLogger("data-masters")


# ─────────────────────────────────────────────────────────────────────────────
# Helpers de logging padronizado
# Formato compatível com parsers do Control-M (JOBNAME|STEP|STATUS|MSG)
# ─────────────────────────────────────────────────────────────────────────────
def _log(job_id: str, step: str, status: str, msg: str) -> None:
    ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    print(f"[{ts}] {job_id}|{step}|{status}|{msg}", flush=True)


def _exit_code(status: str) -> int:
    """
    Converte status semântico em exit code numérico.

    Control-M interpreta exit codes assim:
      0 → OK (job bem-sucedido)
      1 → WARNING (job OK, mas com alertas — não bloqueia dependentes)
      2 → ERROR (job falhou — bloqueia dependentes por padrão)
    """
    return {"PASS": 0, "WARNING": 1, "DLQ": 2, "ERROR": 2, "SKIPPED": 0}.get(status, 1)


# ─────────────────────────────────────────────────────────────────────────────
# Tasks — cada uma mapeada 1:1 a um futuro job Control-M
# ─────────────────────────────────────────────────────────────────────────────

@task(name="JOB-DM-001-GENERATE", retries=1, retry_delay_seconds=10)
def task_generate_data(scenario: str, run_id: str) -> list:
    """
    Control-M equivalent: JOB-DM-001-GENERATE
    Trigger: schedule (horário de abertura do batch) ou evento de arquivo na landing zone.
    Depende de: nenhum (início do DAG)
    Bloqueia: JOB-DM-002-VALIDATE
    """
    _log("JOB-DM-001", "GENERATE", "STARTED", f"scenario={scenario}")
    try:
        storage  = get_storage()
        produced = generate_all(storage, scenario=scenario)
        _log("JOB-DM-001", "GENERATE", "ENDED_OK", f"tables={len(produced)} backend={type(storage).__name__}")
        # Serializa apenas metadados — Storage é recriado em cada task
        return [
            {
                "table"            : p["table"],
                "filename"         : p["filename"],
                "contract_filename": p["contract_filename"],
                "scenario"         : scenario,
            }
            for p in produced
        ]
    except Exception as e:
        _log("JOB-DM-001", "GENERATE", "ENDED_NOTOK", str(e))
        raise


@task(name="JOB-DM-002-VALIDATE", retries=0)
def task_validate(item: dict, run_id: str) -> dict:
    """
    Control-M equivalent: JOB-DM-002-VALIDATE
    Trigger: conclusão de JOB-DM-001-GENERATE
    Bloqueia: JOB-DM-003-PROFILE (apenas se status != DLQ)

    Exit code 2 (DLQ) interrompe a cadeia para a tabela afetada,
    mas não bloqueia o processamento das demais.
    """
    table = item["table"]
    _log("JOB-DM-002", f"VALIDATE/{table}", "STARTED", f"file=bronze/{item['filename']}")
    try:
        storage = get_storage()
        result  = validate(
            storage,
            item["filename"],
            item["contract_filename"],
            scenario=item["scenario"],
        )
        ec = _exit_code(result.status)
        _log(
            "JOB-DM-002", f"VALIDATE/{table}",
            "ENDED_OK" if ec < 2 else "ENDED_NOTOK",
            f"status={result.status} exit_code={ec} layer={'quarantine' if result.status=='DLQ' else 'bronze'} evolution={result.evolution_type}",
        )
        return {
            **item,
            "validation_status" : result.status,
            "evolution_type"    : result.evolution_type,
            "rows_total"        : result.rows_total,
            "rows_valid"        : result.rows_valid,
            "duplicate_count"   : result.duplicate_count,
            "null_violations"   : result.null_violations,
            "issues"            : result.issues,
            "warnings"          : result.warnings,
            "exit_code"         : ec,
        }
    except Exception as e:
        _log("JOB-DM-002", f"VALIDATE/{table}", "ENDED_NOTOK", str(e))
        raise


@task(name="JOB-DM-003-PROFILE", retries=1, retry_delay_seconds=5)
def task_profile(validated: dict) -> dict:
    """
    Control-M equivalent: JOB-DM-003-PROFILE
    Trigger: JOB-DM-002-VALIDATE com exit_code 0 ou 1
    Pré-condição: validation_status != DLQ
    Bloqueia: JOB-DM-004-ENRICH
    """
    table = validated["table"]
    if validated["validation_status"] == "DLQ":
        _log("JOB-DM-003", f"PROFILE/{table}", "SKIPPED", "upstream DLQ")
        return {**validated, "profiler_payload": {"table": table, "rows": 0, "profiling_ms": 0, "columns": {}}}

    _log("JOB-DM-003", f"PROFILE/{table}", "STARTED", f"reading bronze/{validated['filename']}")
    try:
        storage  = get_storage()
        csv_path = storage.read_path("bronze", validated["filename"])
        payload  = profile(csv_path)
        # Promoção Bronze → Silver após profiling bem-sucedido
        storage.move(validated["filename"], "bronze", "silver")
        _log("JOB-DM-003", f"PROFILE/{table}", "ENDED_OK",
             f"rows={payload['rows']} ms={payload['profiling_ms']} promoted=bronze->silver")
        return {**validated, "profiler_payload": payload}
    except Exception as e:
        _log("JOB-DM-003", f"PROFILE/{table}", "ENDED_NOTOK", str(e))
        raise


@task(name="JOB-DM-004-ENRICH", retries=1, retry_delay_seconds=30)
def task_enrich_slm(profiled: dict) -> dict:
    """
    Control-M equivalent: JOB-DM-004-ENRICH
    Trigger: JOB-DM-003-PROFILE
    Timeout recomendado (Control-M): 300s por tabela
    Bloqueia: JOB-DM-005-METRICS

    Nota: exit_code 1 (WARNING/SKIPPED) é aceitável e não bloqueia dependentes.
    O SLM pode estar indisponível sem impactar o pipeline de dados.
    """
    table = profiled["table"]
    if profiled["validation_status"] == "DLQ":
        _log("JOB-DM-004", f"ENRICH/{table}", "SKIPPED", "upstream DLQ")
        return {**profiled, "slm_result": {"table": table, "status": "SKIPPED", "inference_ms": 0}}

    _log("JOB-DM-004", f"ENRICH/{table}", "STARTED", "calling Ollama")
    try:
        storage = get_storage()
        slm     = enrich(storage, profiled["contract_filename"], profiled["profiler_payload"])
        # Documentação gravada no layer reports via SLM — anota no log
        _log("JOB-DM-004", f"ENRICH/{table}", "ENDED_OK",
             f"slm_status={slm['status']} ms={slm['inference_ms']} ai_status=DRAFT")
        return {**profiled, "slm_result": slm}
    except Exception as e:
        _log("JOB-DM-004", f"ENRICH/{table}", "ENDED_NOTOK", str(e))
        return {**profiled, "slm_result": {"table": table, "status": "ERROR", "inference_ms": 0}}


@task(name="JOB-DM-005-METRICS")
def task_collect_metrics(enriched: dict, run_id: str) -> dict:
    """
    Control-M equivalent: JOB-DM-005-METRICS
    Trigger: JOB-DM-004-ENRICH
    Bloqueia: JOB-DM-006-REPORT
    """
    table = enriched["table"]
    _log("JOB-DM-005", f"METRICS/{table}", "STARTED", "")

    # Reconstrói ValidationResult a partir do dict serializado
    from src.validation.validator import ValidationResult
    val_result = ValidationResult(
        table           = table,
        status          = enriched["validation_status"],
        scenario        = enriched["scenario"],
        evolution_type  = enriched.get("evolution_type"),
        issues          = enriched.get("issues", []),
        warnings        = enriched.get("warnings", []),
        rows_total      = enriched.get("rows_total", 0),
        rows_valid      = enriched.get("rows_valid", 0),
        null_violations = enriched.get("null_violations", {}),
        duplicate_count = enriched.get("duplicate_count", 0),
    )

    metrics = collect(
        run_id,
        val_result,
        enriched.get("profiler_payload", {}),
        enriched.get("slm_result", {}),
        METRICS_DIR,
    )
    _log("JOB-DM-005", f"METRICS/{table}", "ENDED_OK", f"score={metrics['quality_score']}")
    return metrics


@task(name="JOB-DM-006-REPORT")
def task_report(all_metrics: list, run_id: str) -> str:
    """
    Control-M equivalent: JOB-DM-006-REPORT
    Trigger: conclusão de TODOS os JOB-DM-005-METRICS (fan-in)
    Depende de: todos os jobs da cadeia
    Condição: executa mesmo se alguns jobs anteriores retornaram WARNING
    """
    _log("JOB-DM-006", "REPORT", "STARTED", f"tables={len(all_metrics)}")
    report_path = generate_report(all_metrics, REPORTS_DIR)

    summary_path = METRICS_DIR / f"{run_id}_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(all_metrics, f, ensure_ascii=False, indent=2)

    _log("JOB-DM-006", "REPORT", "ENDED_OK", f"report={report_path.name}")
    return str(report_path)


# ─────────────────────────────────────────────────────────────────────────────
# Flow principal
# ─────────────────────────────────────────────────────────────────────────────

@flow(
    name="data-masters-pipeline",
    description="Pipeline lakehouse bancária com contratos, profiler e SLM.",
    version="1.0.0",
)
def pipeline_flow(scenario: str = "baseline", run_id: str | None = None) -> dict:
    """
    DAG completo. Execução por tabela é paralela quando Prefect está disponível.

    Diagrama de dependências (espelha a estrutura de jobs Control-M):

        [001-GENERATE]
              │
        ┌─────┴──────┐──────────────────┐
        ▼            ▼                  ▼
    [002-VAL]   [002-VAL]          [002-VAL]
    tb_clientes  tb_transacoes  tb_contratos
        │            │                  │
    [003-PROF]  [003-PROF]         [003-PROF]
        │            │                  │
    [004-ENRICH][004-ENRICH]      [004-ENRICH]
        │            │                  │
    [005-MTR]   [005-MTR]          [005-MTR]
        └────────────┴──────────────────┘
                     │  fan-in
                [006-REPORT]
    """
    if run_id is None:
        import uuid as _uuid
        run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(_uuid.uuid4())[:6]}"

    _log("PIPELINE", "FLOW", "STARTED", f"run_id={run_id} scenario={scenario}")

    # JOB-001: Geração
    produced = task_generate_data(scenario, run_id)

    # JOB-002 a 005: por tabela (Prefect executa em paralelo automaticamente)
    all_metrics = []
    for item in produced:
        validated = task_validate(item, run_id)
        profiled  = task_profile(validated)
        enriched  = task_enrich_slm(profiled)
        metrics   = task_collect_metrics(enriched, run_id)
        all_metrics.append(metrics)

    # JOB-006: Relatório consolidado (fan-in)
    report_path = task_report(all_metrics, run_id)

    # Resumo no terminal
    _print_summary(all_metrics, run_id)

    worst_exit = max(_exit_code(m["validation_status"]) for m in all_metrics)
    _log("PIPELINE", "FLOW", "ENDED_OK" if worst_exit < 2 else "ENDED_NOTOK",
         f"exit_code={worst_exit} report={report_path}")

    return {
        "run_id"     : run_id,
        "scenario"   : scenario,
        "exit_code"  : worst_exit,
        "report_path": report_path,
        "metrics"    : all_metrics,
    }


def _print_summary(all_metrics: list, run_id: str) -> None:
    icons = {"PASS": "[PASS]", "WARNING": "[WARN]", "DLQ": "[DLQ]"}
    print(f"\n{'='*66}")
    print(f"  RUN: {run_id}")
    print(f"{'='*66}")
    print(f"  {'Tabela':<30} {'Cenário':<14} {'Status':<10} {'Score':>6}")
    print(f"  {'-'*62}")
    for m in all_metrics:
        icon = icons.get(m["validation_status"], "⚪")
        print(
            f"  {m['table']:<30} {m['scenario']:<14} "
            f"{icon} {m['validation_status']:<8} {m['quality_score']:>6.1f}/100"
        )
    avg = round(sum(m["quality_score"] for m in all_metrics) / len(all_metrics), 1) if all_metrics else 0
    print(f"  {'-'*62}")
    print(f"  {'Score médio':>55} {avg:>6.1f}/100\n")


# ─────────────────────────────────────────────────────────────────────────────
# Entry point CLI
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Data Masters Pipeline")
    parser.add_argument(
        "--scenario", choices=["baseline", "non_breaking", "breaking", "all"],
        default="all",
    )
    parser.add_argument(
        "--no-prefect", action="store_true",
        help="Executa sem registrar no servidor Prefect (compatível com Control-M)",
    )
    parser.add_argument("--run-id", default=None, help="Run ID externo (útil para rastreio Control-M)")
    args = parser.parse_args()

    scenarios = (
        ["baseline", "non_breaking", "breaking"]
        if args.scenario == "all"
        else [args.scenario]
    )

    # Run ID externo: permite que o Control-M injete seu próprio ID de job
    base_run_id = args.run_id or f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:6]}"

    worst_global = 0
    for sc in scenarios:
        run_id = f"{base_run_id}_{sc}" if len(scenarios) > 1 else base_run_id
        result = pipeline_flow(scenario=sc, run_id=run_id)
        worst_global = max(worst_global, result["exit_code"])

    # Exit code global — o Control-M lê este valor para decidir o status do job pai
    sys.exit(worst_global)
