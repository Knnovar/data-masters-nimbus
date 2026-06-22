"""
prefect_flow.py - Orquestracao da Pipeline Projeto Nimbus via Prefect

Mapeamento Prefect Task -> Control-M Job:
  task_generate_data   -> JOB-DM-001-GENERATE
  task_validate        -> JOB-DM-002-VALIDATE
  task_profile         -> JOB-DM-003-PROFILE
  task_enrich_slm      -> JOB-DM-004-ENRICH
  task_collect_metrics -> JOB-DM-005-METRICS
  task_report          -> JOB-DM-006-REPORT

Cada task:
  - Recebe e retorna dicts serializaveis (sem objetos complexos entre tasks)
  - Emite exit code padronizado: 0=OK, 1=WARNING, 2=ERROR
  - Loga para stdout no formato JOBNAME|STEP|STATUS|MSG (parseavel pelo Control-M)
  - E invocavel de forma independente via CLI (ver __main__)

Uso:
    # Com servidor Prefect (UI em http://127.0.0.1:4200)
    prefect server start          # terminal 1
    python setup_prefect.py       # terminal 2 - registra deployments
    prefect worker start --pool data-masters-local  # terminal 3
    prefect deployment run 'data-masters-pipeline/baseline-manual'

    # Sem servidor Prefect (compativel com Control-M)
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
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent))

from config import METRICS_DIR, REPORTS_DIR
from src.storage.storage import get_storage
from src.generators.data_generator import generate_all
from src.validation.validator import validate
from src.profiler.duckdb_profiler import profile
from src.slm.ollama_enrichment import enrich
from src.metrics.metrics_collector import collect, generate_report
from src.ingestion.normalizer import normalize

# Prefect e opcional — sem ele os decoradores viram no-ops transparentes
try:
    from prefect import flow, task
    _HAS_PREFECT = True
except ImportError:
    _HAS_PREFECT = False
    def flow(*a, **kw):
        fn = a[0] if a and callable(a[0]) else None
        def decorator(f): return f
        return fn if fn else decorator
    def task(*a, **kw):
        fn = a[0] if a and callable(a[0]) else None
        def decorator(f): return f
        return fn if fn else decorator


# ─────────────────────────────────────────────────────────────────────────────
# Logging padronizado — formato parseavel pelo Control-M
# ─────────────────────────────────────────────────────────────────────────────

def _log(job_id, step, status, msg):
    ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    print("[{}] {}|{}|{}|{}".format(ts, job_id, step, status, msg), flush=True)


def _exit_code(status):
    """0=PASS/SKIPPED, 1=WARNING, 2=DLQ/ERROR"""
    return {"PASS": 0, "WARNING": 1, "DLQ": 2, "ERROR": 2, "SKIPPED": 0}.get(status, 1)


# ─────────────────────────────────────────────────────────────────────────────
# Tasks
# ─────────────────────────────────────────────────────────────────────────────

@task(name="JOB-DM-000-EXTRACT", retries=1, retry_delay_seconds=5)
def task_extract_manifest(filename: str, table_name: str, fmt: str = "csv") -> dict:
    """
    Control-M: JOB-DM-000-EXTRACT (opcional)
    Gera rascunho de manifesto se ainda nao existir para a tabela.
    Skipa silenciosamente se manifesto ja estiver presente (DRAFT ou VALIDATED).

    Parametros:
        filename   : nome do arquivo na landing zone
        table_name : nome da tabela
        fmt        : formato do arquivo (csv | fixed | json | sas7bdat)
    """
    _log("JOB-DM-000", "EXTRACT/{}".format(table_name), "STARTED",
         "file={} format={}".format(filename, fmt))
    try:
        storage       = get_storage()
        contract_file = "{}.yaml".format(table_name)

        # Skipa se manifesto ja existe
        if storage.exists("contracts", contract_file):
            _log("JOB-DM-000", "EXTRACT/{}".format(table_name), "SKIPPED",
                 "manifesto ja existe em contracts/{}".format(contract_file))
            return {"table": table_name, "status": "SKIPPED",
                    "contract_filename": contract_file}

        # Normaliza encoding antes de extrair
        csv_path = storage.read_path("bronze", filename)
        norm_result = normalize(csv_path, backup=True)
        if norm_result["status"] == "ebcdic":
            _log("JOB-DM-000", "EXTRACT/{}".format(table_name), "ENDED_NOTOK",
                 "EBCDIC detectado - requer conversao manual")
            return {"table": table_name, "status": "ERROR",
                    "warning": norm_result["warning"]}

        # Seleciona extrator pelo formato
        if fmt == "csv":
            from src.manifest.extractor_csv import CSVExtractor
            extractor = CSVExtractor()
            manifest  = extractor.extract(csv_path, table_name)
        elif fmt == "json":
            from src.manifest.extractor_json import JSONExtractor
            extractor = JSONExtractor()
            manifest  = extractor.extract(csv_path, table_name)
        elif fmt == "fixed":
            from src.manifest.extractor_fixed import FixedWidthExtractor
            extractor = FixedWidthExtractor()
            manifest  = extractor.extract(csv_path, table_name, infer=True)
        else:
            _log("JOB-DM-000", "EXTRACT/{}".format(table_name), "SKIPPED",
                 "formato {} nao suportado automaticamente".format(fmt))
            return {"table": table_name, "status": "SKIPPED",
                    "contract_filename": None}

        import yaml
        storage.write_text("contracts", contract_file,
                           yaml.dump(manifest, allow_unicode=True, sort_keys=False))

        _log("JOB-DM-000", "EXTRACT/{}".format(table_name), "ENDED_OK",
             "manifesto DRAFT gerado -> contracts/{}".format(contract_file))
        return {"table": table_name, "status": "OK",
                "contract_filename": contract_file}

    except Exception as e:
        _log("JOB-DM-000", "EXTRACT/{}".format(table_name), "ENDED_NOTOK", str(e))
        # Falha nao bloqueia o pipeline — retorna sem manifesto
        return {"table": table_name, "status": "ERROR", "warning": str(e)}


@task(name="JOB-DM-001-GENERATE", retries=1, retry_delay_seconds=10)
def task_generate_data(scenario, run_id, fmt="csv"):
    """
    Control-M: JOB-DM-001-GENERATE
    Depende de: nenhum (inicio do DAG)
    Bloqueia: JOB-DM-002-VALIDATE

    Args:
        scenario: Cenario de dados ('baseline', 'non_breaking', 'breaking').
        run_id: Identificador da run para rastreio.
        fmt: Formato de saida ('csv', 'json', 'fixed').
    """
    _log("JOB-DM-001", "GENERATE", "STARTED", "scenario={} format={}".format(scenario, fmt))
    try:
        from src.generators.writers import SUPPORTED_FORMATS
        if fmt not in SUPPORTED_FORMATS:
            raise ValueError(
                "Formato invalido: '{}'. Opcoes validas: {}".format(fmt, ', '.join(SUPPORTED_FORMATS))
            )
        storage  = get_storage()
        produced = generate_all(storage, scenario=scenario, fmt=fmt)
        _log("JOB-DM-001", "GENERATE", "ENDED_OK",
             "tables={} backend={} format={}".format(len(produced), type(storage).__name__, fmt))
        return [
            {
                "table"            : p["table"],
                "filename"         : p["filename"],
                "contract_filename": p["contract_filename"],
                "scenario"         : scenario,
                "format"           : fmt,
            }
            for p in produced
        ]
    except Exception as e:
        _log("JOB-DM-001", "GENERATE", "ENDED_NOTOK", str(e))
        raise


@task(name="JOB-DM-002-VALIDATE", retries=0)
def task_validate(item, run_id):
    """
    Control-M: JOB-DM-002-VALIDATE
    exit_code 2 (DLQ) isola a tabela afetada sem bloquear as demais.
    """
    table = item["table"]
    _log("JOB-DM-002", "VALIDATE/{}".format(table), "STARTED",
         "file=bronze/{}".format(item["filename"]))
    try:
        storage = get_storage()
        result  = validate(
            storage,
            item["filename"],
            item["contract_filename"],
            scenario=item["scenario"],
        )
        ec = _exit_code(result.status)
        _log("JOB-DM-002", "VALIDATE/{}".format(table),
             "ENDED_OK" if ec < 2 else "ENDED_NOTOK",
             "status={} exit_code={} layer={} evolution={}".format(
                 result.status, ec,
                 "quarantine" if result.status == "DLQ" else "bronze",
                 result.evolution_type))
        return {
            **item,
            "validation_status": result.status,
            "evolution_type"   : result.evolution_type,
            "rows_total"       : result.rows_total,
            "rows_valid"       : result.rows_valid,
            "duplicate_count"  : result.duplicate_count,
            "null_violations"  : result.null_violations,
            "issues"           : result.issues,
            "warnings"         : result.warnings,
            "exit_code"        : ec,
        }
    except Exception as e:
        _log("JOB-DM-002", "VALIDATE/{}".format(table), "ENDED_NOTOK", str(e))
        raise


@task(name="JOB-DM-003-PROFILE", retries=1, retry_delay_seconds=5)
def task_profile(validated):
    """
    Control-M: JOB-DM-003-PROFILE
    Skipa automaticamente se upstream retornou DLQ.
    Promove o arquivo de BRONZE para SILVER apos profiling.
    """
    table = validated["table"]
    if validated["validation_status"] == "DLQ":
        _log("JOB-DM-003", "PROFILE/{}".format(table), "SKIPPED", "upstream DLQ")
        return {**validated, "profiler_payload": {
            "table": table, "rows": 0, "profiling_ms": 0, "columns": {}}}

    _log("JOB-DM-003", "PROFILE/{}".format(table), "STARTED",
         "reading bronze/{}".format(validated["filename"]))
    try:
        storage  = get_storage()
        csv_path = storage.read_path("bronze", validated["filename"])
        payload  = profile(csv_path)
        storage.move(validated["filename"], "bronze", "silver")
        _log("JOB-DM-003", "PROFILE/{}".format(table), "ENDED_OK",
             "rows={} ms={} promoted=bronze->silver".format(
                 payload["rows"], payload["profiling_ms"]))
        return {**validated, "profiler_payload": payload}
    except Exception as e:
        _log("JOB-DM-003", "PROFILE/{}".format(table), "ENDED_NOTOK", str(e))
        raise


@task(name="JOB-DM-004-ENRICH", retries=1, retry_delay_seconds=30)
def task_enrich_slm(profiled):
    """
    Control-M: JOB-DM-004-ENRICH
    Timeout recomendado no Control-M: 600s por tabela (CPU lenta).
    Falha do SLM e nao-fatal — retorna SKIPPED sem bloquear metricas.
    """
    table = profiled["table"]
    if profiled["validation_status"] == "DLQ":
        _log("JOB-DM-004", "ENRICH/{}".format(table), "SKIPPED", "upstream DLQ")
        return {**profiled, "slm_result": {
            "table": table, "status": "SKIPPED", "inference_ms": 0}}

    _log("JOB-DM-004", "ENRICH/{}".format(table), "STARTED", "calling Ollama")
    try:
        storage = get_storage()
        slm     = enrich(storage, profiled["contract_filename"], profiled["profiler_payload"])
        _log("JOB-DM-004", "ENRICH/{}".format(table), "ENDED_OK",
             "slm_status={} ms={} ai_status=DRAFT".format(
                 slm["status"], slm["inference_ms"]))
        return {**profiled, "slm_result": slm}
    except Exception as e:
        _log("JOB-DM-004", "ENRICH/{}".format(table), "ENDED_NOTOK", str(e))
        return {**profiled, "slm_result": {
            "table": table, "status": "ERROR", "inference_ms": 0}}


@task(name="JOB-DM-005-METRICS")
def task_collect_metrics(enriched, run_id):
    """Control-M: JOB-DM-005-METRICS"""
    table = enriched["table"]
    _log("JOB-DM-005", "METRICS/{}".format(table), "STARTED", "")

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
    _log("JOB-DM-005", "METRICS/{}".format(table), "ENDED_OK",
         "score={}".format(metrics["quality_score"]))
    return metrics


@task(name="JOB-DM-006-REPORT")
def task_report(all_metrics, run_id):
    """
    Control-M: JOB-DM-006-REPORT
    Fan-in: aguarda conclusao de todos os JOB-DM-005.
    Roda mesmo se alguns jobs anteriores retornaram WARNING.
    """
    _log("JOB-DM-006", "REPORT", "STARTED", "tables={}".format(len(all_metrics)))
    report_path = generate_report(all_metrics, REPORTS_DIR)

    summary_path = METRICS_DIR / "{}_summary.json".format(run_id)
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(all_metrics, f, ensure_ascii=False, indent=2)

    _log("JOB-DM-006", "REPORT", "ENDED_OK", "report={}".format(report_path.name))
    return str(report_path)


# ─────────────────────────────────────────────────────────────────────────────
# Flow principal
# ─────────────────────────────────────────────────────────────────────────────

@flow(
    name="data-masters-pipeline",
    description="Pipeline lakehouse bancaria com contratos, profiler e SLM.",
    version="1.0.0",
)
def pipeline_flow(scenario="baseline", run_id=None, fmt="csv"):
    """
    DAG completo. Cada tabela passa pelos jobs 002-005 em sequencia.
    Com Prefect server ativo, as tres tabelas rodam em paralelo automaticamente.

    DAG de dependencias:
        [001-GENERATE]
              |
        +-----+-----+----------+
        v           v          v
    [002-VAL]  [002-VAL]  [002-VAL]
    tb_clientes tb_trans  tb_contratos
        |           |          |
    [003-PROF] [003-PROF] [003-PROF]
        |           |          |
    [004-ENRICH]...        ...
        |           |          |
    [005-MTR]  [005-MTR]  [005-MTR]
        +-----+-----+----------+
                    | fan-in
              [006-REPORT]
    """
    if run_id is None:
        run_id = "run_{}_{}".format(
            datetime.now().strftime("%Y%m%d_%H%M%S"),
            str(uuid.uuid4())[:6]
        )

    _log("PIPELINE", "FLOW", "STARTED", "run_id={} scenario={} format={}".format(run_id, scenario, fmt))

    produced    = task_generate_data(scenario, run_id, fmt)
    all_metrics = []

    for item in produced:
        validated = task_validate(item, run_id)
        profiled  = task_profile(validated)
        enriched  = task_enrich_slm(profiled)
        metrics   = task_collect_metrics(enriched, run_id)
        all_metrics.append(metrics)

    report_path  = task_report(all_metrics, run_id)
    worst_exit   = max(_exit_code(m["validation_status"]) for m in all_metrics)

    _print_summary(all_metrics, run_id)
    _log("PIPELINE", "FLOW",
         "ENDED_OK" if worst_exit < 2 else "ENDED_NOTOK",
         "exit_code={} report={}".format(worst_exit, report_path))

    return {
        "run_id"     : run_id,
        "scenario"   : scenario,
        "exit_code"  : worst_exit,
        "report_path": report_path,
        "metrics"    : all_metrics,
    }


def _print_summary(all_metrics, run_id):
    status_tag = {"PASS": "[PASS]", "WARNING": "[WARN]", "DLQ": "[DLQ]"}
    print("\n" + "=" * 66)
    print("  RUN: {}".format(run_id))
    print("=" * 66)
    print("  {:<30} {:<14} {:<10} {:>6}".format("Tabela", "Cenario", "Status", "Score"))
    print("  " + "-" * 62)
    for m in all_metrics:
        tag = status_tag.get(m["validation_status"], "[?]")
        print("  {:<30} {:<14} {} {:<8} {:>6.1f}/100".format(
            m["table"], m["scenario"], tag,
            m["validation_status"], m["quality_score"]))
    avg = round(sum(m["quality_score"] for m in all_metrics) / len(all_metrics), 1) if all_metrics else 0
    print("  " + "-" * 62)
    print("  {:<55} {:>6.1f}/100\n".format("Score medio", avg))


# ─────────────────────────────────────────────────────────────────────────────
# Entry point CLI
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Projeto Nimbus Pipeline")
    parser.add_argument(
        "--scenario", choices=["baseline", "non_breaking", "breaking", "all"],
        default="all",
    )
    parser.add_argument(
        "--format", choices=["csv", "json", "fixed", "all"],
        default="csv", dest="fmt",
        help="Formato de saida dos dados gerados (csv|json|fixed|all).",
    )
    parser.add_argument(
        "--no-prefect", action="store_true",
        help="Executa sem registrar no servidor Prefect (compativel com Control-M)",
    )
    parser.add_argument(
        "--run-id", default=None,
        help="Run ID externo (util para rastreio Control-M)",
    )
    args = parser.parse_args()

    scenarios = (
        ["baseline", "non_breaking", "breaking"]
        if args.scenario == "all"
        else [args.scenario]
    )

    base_run_id = args.run_id or "run_{}_{}".format(
        datetime.now().strftime("%Y%m%d_%H%M%S"),
        str(uuid.uuid4())[:6]
    )

    worst_global = 0
    for sc in scenarios:
        run_id = "{}_{}".format(base_run_id, sc) if len(scenarios) > 1 else base_run_id
        # Expande "all" em todos os formatos suportados
        fmt_list = ["csv", "json", "fixed"] if args.fmt == "all" else [args.fmt]
        for fmt in fmt_list:
            result = pipeline_flow(scenario=sc, run_id=run_id, fmt=fmt)
            worst_global = max(worst_global, result["exit_code"])
        continue
    sys.exit(worst_global)
