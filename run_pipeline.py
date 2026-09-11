"""
run_pipeline.py — Entry point da Pipeline Projeto Nimbus (PoC local)

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
import sys
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
║          🏦  PIPELINE PROJETO NIMBUS — PoC LOCAL                  ║
║          Lakehouse  ·  Contratos  ·  Profiler  ·  SLM           ║
╚══════════════════════════════════════════════════════════════════╝
"""

def evaluate_gate(table: str, reject_report: dict) -> dict:
    """Decide se a tabela pode ser publicada.
    
    O criterio e a taxa de linhas rejeitadas por tipo divergente do Manifest
    contra a tolerancia declarada no contrato (`tolerance.max_reject_pct`, com 
    fallback para `max_null_pct`). Rejeicao dentro da tolerancia publica com 
    aviso; acima dela bloqueia a publicacao e o exit code da run.
    """
    import config

    reject_pct = reject_report.get("reject_pct")
    limit_pct = reject_report.get("limit_pct")
    rejected = reject_report.get("rows_rejected", 0)

    if reject_pct is None:
        return {"status": "PASS", "reason": "NO_REJECT_REPORT",
                "detail": "sem relatorio de rejeicao (tipagem tolerante)",
                "reject_pct": None, "limit_pct": None}
    detail = "{} linha(s) rejeitada(s) ({:.2f}% | tolerancia {:.2f}%)".format(
        rejected, reject_pct, limit_pct or 0.0)
    if not reject_report.get("within_limit", True) and getattr(config, "QUALITY_GATE", True):
        print("     [GATE] [{}] BLOQUEADO: {}".format(table, detail))
        return {"status": "BLOCKED", "reason": "REJECT_ABOVE_TOLERANCE", "detail": detail,
                "reject_pct": reject_pct, "limit_pct": limit_pct}
    if rejected:
        print("     [GATE] [{}] LIBERADO com rejeicao: {}".format(table, detail))
        return {"status": "PASS_WITH_REJECTS", "reason": "REJECT_WITHIN_TOLERANCE", "detail": detail,
                "reject_pct": reject_pct, "limit_pct": limit_pct}
    
    return{"status": "PASS", "reason": "CONFORMANT", "detail": "nenhuma linha rejeitada",
           "reject_pct": 0.0, "limit_pct": limit_pct}

def run_scenario(scenario: str, run_id: str, fmt: str = "csv") -> tuple[list[dict], list[dict]]:
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
    publications = []
    for item in produced:
        table             = item["table"]
        filename          = item["filename"]
        contract_filename = item["contract_filename"]

        print(f"\n  -- {table} --")

        from src.connectors.bronze_uploader import publish_bronze
        publications.append(publish_bronze(storage.read_path("bronze", filename),
                                           table_name=Path(filename).stem, run_id=run_id))

        # Silver: validação (DLQ → quarantine, OK → permanece no bronze)
        val_result = validate(storage, filename, contract_filename, scenario=scenario)

        contract = None
        if contract_filename and storage.exists("contracts", contract_filename):
            try:
                import yaml
                from src.validation.contracts import DataContract
                cp = storage.read_path("contracts", contract_filename)
                with open(cp, encoding="utf-8") as f:
                    contract = DataContract.from_dict(yaml.safe_load(f))
            except Exception as ce:
                print(f" [SCHEMA] Contrato Nao Carregado: {ce}")
        cast_report = {}
        reject_report = {}

        if val_result.status == "DLQ":
            slm_result       = {"table": table, "status": "SKIPPED", "inference_ms": 0, "documentation": ""}
            profiler_payload = {"table": table, "rows": 0, "profiling_ms": 0, "columns": {}}
            gate             = {"status": "BLOCKED", "reason": "VALIDATION_DLQ",
                                "detail": "quarentena na validacao ({})".format(val_result.evolution_type or "regra de contrato"),
                                "reject_pct": None, "limit_pct": None}
            print("     [GATE] [{}] BLOQUEADO: {}".format(table, gate["detail"]))
        else:

            csv_path         = storage.read_path("bronze", filename)
            profiler_payload = profile(csv_path)

            slm_result = enrich(storage, contract_filename, profiler_payload)
            parquet_filename = storage.promote_to_parquet(filename, "bronze", "silver", contract=contract)
            cast_report = dict(getattr(storage, "last_cast_report", {}) or {})
            reject_report = dict(getattr(storage, "last_reject_report", {}) or {})
            gate = evaluate_gate(table, reject_report)
            if gate["status"] == "BLOCKED":
                publications.append({"table": table, "status": "BLOCKED", "layer": "silver",
                                     "error": gate["detail"], "rows": 0})
            else:
                from src.connectors.databricks_uploader import publish_table
                pub = publish_table(storage.read_path("silver", parquet_filename),
                                    table_name=Path(filename).stem, contract=contract, run_id=run_id)
                publications.append(pub)
        
        # Gold: métricas agregadas
        m = collect(run_id, val_result, profiler_payload, slm_result, METRICS_DIR, 
                    contract=contract, cast_report=cast_report, fmt = fmt,
                    reject_report=reject_report, gate=gate)
        scenario_metrics.append(m)

    return scenario_metrics, publications


def print_summary(all_metrics: list[dict]) -> None:
    """Imprime tabela de resultados no terminal."""
    print(f"\n{'='*66}")
    print("  RESUMO DA EXECUÇÃO")
    print(f"{'='*66}")

    header = f"{'Tabela':<26} {'Cenario':<13} {'Status':<15} {'Publicacao':<12} {'Score':>6}"
    print(header)
    print("-" * 78)

    icons = {"PASS": "[PASS]", "WARNING": "[WARN]", "DLQ": "[DLQ]"}
    gate_icons = {"BLOCKED": "[BLOQUEADO]", "PASS_WITH_REJECTS": "[C/ REJEICAO]", "PASS": "[LIBERADA]"}
    for m in all_metrics:
        icon = icons.get(m["validation_status"], "⚪")
        gate = gate_icons.get(m.get("gate_status"), "[LIBERADA]")
        print(
            f"{m['table']:<26} {m['scenario']:<13} "
            f"{icon} {m['validation_status']:<8} {gate:<12} {m['quality_score']:>6.1f}/100"
        )

    avg = round(sum(m["quality_score"] for m in all_metrics) / len(all_metrics), 1)
    print("-" * 78)
    print(f"{'Score medio':>55} {avg:>6.1f}/100")
    print()

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Pipeline Projeto Nimbus — PoC Local")
    parser.add_argument(
             "--scenario",
             choices=["baseline", "non_breaking", "breaking", "type_drift", "all"],
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
    return parser

def main():
    args = build_parser().parse_args()

    print(BANNER)

    run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:6]}"
    print(f"  Run ID : {run_id}")
    print(f"  Modelo : {__import__('config').OLLAMA_MODEL}")
    print(f"  Ollama : {__import__('config').OLLAMA_HOST}")

    scenarios = (
        ["baseline", "non_breaking", "breaking", "type_drift"]
        if args.scenario == "all"
        else [args.scenario]
    )

    fmt_list = ["csv", "json", "fixed"] if args.fmt == "all" else [args.fmt]

    all_metrics: list[dict] = []
    publications: list[dict] = []
    for scenario in scenarios:
        for fmt in fmt_list:
            metrics, pubs = run_scenario(scenario, run_id, fmt=fmt)
            all_metrics.extend(metrics)
            publications.extend(pubs)

    # Relatório consolidado
    print_summary(all_metrics)
    report_path = generate_report(all_metrics, REPORTS_DIR)

    # Salva JSON consolidado
    summary_path = METRICS_DIR / f"{run_id}_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(all_metrics, f, ensure_ascii=False, indent=2)

    print(f"  Metricas JSON : {summary_path}")
    print(f"  Relatorio MD  : {report_path}")
    attempted = [p for p in publications if p["status"] not in ("DISABLED", "SKIPPED", "BLOCKED")]
    skipped = [p for p in publications if p["status"] == "SKIPPED"]
    failed = [p for p in publications if p["status"] == "ERROR"]
    blocked = [p for p in publications if p["status"] == "BLOCKED"]
    if attempted:
        for layer in ("bronze", "silver"):
          rows = [p for p in attempted if p.get("layer", "silver") == layer]
          if rows:  
            ok = sum( 1 for p in rows if p["status"] in ("OK", "UPLOADED"))
            print(f"Databricks: {layer}: {ok}/{len(rows)} tabelas publicadas")
    if skipped:
        print(f"Databricks: {len(skipped)} publicacao(oes) ignorada(s): {skipped[0]['error']}")
    for p in failed:
        print(f" [DATABRICKS] {p.get('layer', 'silver')}/{p['table']}: {p['error']}")
    for p in blocked:
        print(f" [GATE] {p['table']} nao publicada: {p['error']}")
    print("\n  Pipeline concluida.\n")

    return 2 if (failed or blocked) else 0


if __name__ == "__main__":
    sys.exit(main())
    
