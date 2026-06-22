"""
run_pipeline.py — Entry point da Pipeline Data Masters (PoC local)

Executa os três cenários de teste em sequência:
  1. baseline     → fluxo feliz, dados válidos
  2. non_breaking → nova coluna anulável detectada (WARNING, avança)
  3. breaking     → tipo de PK alterado (HALT → quarentena)

Uso:
    python run_pipeline.py                  # roda os 3 cenários
    python run_pipeline.py --scenario baseline
    python run_pipeline.py --scenario non_breaking
    python run_pipeline.py --scenario breaking
"""

import argparse
import json
import uuid
from datetime import datetime
from pathlib import Path

from config import METRICS_DIR, REPORTS_DIR, DATA_DIR
from src.storage.storage import get_storage
from src.generators.data_generator import generate_all
from src.validation.validator import validate
from src.profiler.duckdb_profiler import profile
from src.slm.ollama_enrichment import enrich
from src.metrics.metrics_collector import collect, generate_report

BANNER = """
╔══════════════════════════════════════════════════════════════════╗
║          🏦  PIPELINE DATA MASTERS — PoC LOCAL                  ║
║          Lakehouse  ·  Contratos  ·  Profiler  ·  SLM           ║
╚══════════════════════════════════════════════════════════════════╝
"""


def run_scenario(scenario: str, run_id: str, fmt: str = "csv") -> list[dict]:
    """Executa um único cenário end-to-end usando a camada Storage."""
    print(f"\n{chr(9552)*66}")
    print(f"  CENARIO: {scenario.upper()}")
    print(f"{chr(9552)*66}")

    # Instancia o backend de storage (local ou MinIO conforme config.py)
    storage = get_storage()

    # ── 1. Bronze: geração de dados ───────────────────────────────────────
    produced = generate_all(storage, scenario=scenario, fmt=fmt)

    # ── 2. Loop por tabela ────────────────────────────────────────────────
    scenario_metrics = []
    for item in produced:
        table             = item["table"]
        filename          = item["filename"]
        contract_filename = item["contract_filename"]

        print(f"\n  -- {table} --")

        # Silver: validação (DLQ → quarantine, OK → permanece no bronze)
        val_result = validate(storage, filename, contract_filename, scenario=scenario)

        if val_result.status == "DLQ":
            slm_result       = {"table": table, "status": "SKIPPED", "inference_ms": 0, "documentation": ""}
            profiler_payload = {"table": table, "rows": 0, "profiling_ms": 0, "columns": {}}
        else:
            # Profiling via path local (DuckDB/Pandas)
            csv_path         = storage.read_path("bronze", filename)
            profiler_payload = profile(csv_path)

            # Enriquecimento SLM
            slm_result = enrich(storage, contract_filename, profiler_payload)

            # Promoção Bronze → Silver
            storage.move(filename, "bronze", "silver")

        # Gold: métricas agregadas
        m = collect(run_id, val_result, profiler_payload, slm_result, METRICS_DIR)
        scenario_metrics.append(m)

    return scenario_metrics


def print_summary(all_metrics: list[dict]) -> None:
    """Imprime tabela de resultados no terminal."""
    print(f"\n{'='*66}")
    print("  RESUMO DA EXECUÇÃO")
    print(f"{'='*66}")

    header = f"{'Tabela':<30} {'Cenario':<14} {'Status':<10} {'Score':>6}"
    print(header)
    print("-" * 66)

    icons = {"PASS": "[PASS]", "WARNING": "[WARN]", "DLQ": "[DLQ]"}
    for m in all_metrics:
        icon = icons.get(m["validation_status"], "⚪")
        print(
            f"{m['table']:<30} {m['scenario']:<14} "
            f"{icon} {m['validation_status']:<8} {m['quality_score']:>6.1f}/100"
        )

    avg = round(sum(m["quality_score"] for m in all_metrics) / len(all_metrics), 1)
    print("-" * 66)
    print(f"{'Score medio':>55} {avg:>6.1f}/100")
    print()


def main():
    parser = argparse.ArgumentParser(description="Pipeline Data Masters — PoC Local")
    parser.add_argument(
        "--scenario",
        choices=["baseline", "non_breaking", "breaking", "all"],
        default="all",
        help="Cenario a executar (padrao: all)",
    )
    parser.add_argument(
        "--format",
        choices=["csv", "json", "fixed", "all"],
        default="csv",
        dest="fmt",
        help="Formato de saida (csv|json|fixed|all). Padrao: csv",
    )
    args = parser.parse_args()

    print(BANNER)

    run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:6]}"
    print(f"  Run ID : {run_id}")
    print(f"  Modelo : {__import__('config').OLLAMA_MODEL}")
    print(f"  Ollama : {__import__('config').OLLAMA_HOST}")

    scenarios = (
        ["baseline", "non_breaking", "breaking"]
        if args.scenario == "all"
        else [args.scenario]
    )

    fmt_list = ["csv", "json", "fixed"] if args.fmt == "all" else [args.fmt]

    all_metrics: list[dict] = []
    for scenario in scenarios:
        for fmt in fmt_list:
            metrics = run_scenario(scenario, run_id, fmt=fmt)
            all_metrics.extend(metrics)

    # Relatório consolidado
    print_summary(all_metrics)
    report_path = generate_report(all_metrics, REPORTS_DIR)

    # Salva JSON consolidado
    summary_path = METRICS_DIR / f"{run_id}_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(all_metrics, f, ensure_ascii=False, indent=2)

    print(f"  Metricas JSON : {summary_path}")
    print(f"  Relatorio MD  : {report_path}")
    print("\n  Pipeline concluida.\n")


if __name__ == "__main__":
    main()
