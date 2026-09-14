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

from src.storage.storage import get_storage
from src.generators.data_generator import generate_all
from src.validation.validator import validate
from src.profiler.duckdb_profiler import profile
from src.slm.ollama_enrichment import enrich
from src.metrics.metrics_collector import collect, generate_report, save_summary
from src.ingestion.idempotency import (announce, file_sha256, record_load,
                                       resolve_dat_ref, short_sha)

BANNER = """
╔══════════════════════════════════════════════════════════════════╗
║          🏦  PIPELINE PROJETO NIMBUS — PoC LOCAL                  ║
║          Lakehouse  ·  Contratos  ·  Profiler  ·  SLM           ║
╚══════════════════════════════════════════════════════════════════╝
"""

def evaluate_gate(table: str, reject_report: dict, contract=None) -> dict:
    """Decide se a tabela pode ser publicada.

    Dois criterios, nesta Ordem:
    
    1. Governanca (opcional, `REQUIRE_VALIDATED_MANIFEST`): manifesto ainda em
    DRAFT nao publica, porque o schema da Silver e a documentacao do catalogo
    nao passaram pela validacao do Data Steward. Desligado por padrao.
    2. Qualidade: taxa de linhas rejeitadas por tipo divergente do Manifest contra
    a tolerancia declarada no contrato(`tolerance.max_reject_pct`, com fallback
    para `max_null_pct`). Rejeicao dentro da tolerancia publica com aviso; acima
    dela bloqueia a publicacao e o exit code da run
    """
    import config

    if getattr(config, "REQUIRE_VALIDATED_MANIFEST", False) and contract is not None \
        and not contract.is_validated():
        detail = "manifesto em {} - promova com: python -m src.manifest.manifest_validator" \
                 " --file <contrato.yaml> --steward 'Nome'".format(
                     getattr(contract, "manifest_status", "DRAFT")
                 )
        print("     [GATE] [{}] BLOQUEADO: {}".format(table, detail))
        return{"status": "BLOCKED", "reason": "MANIFEST_NOT_VALIDATED", "detail": detail,
               "reject_pct": reject_report.get("reject_pct"),
               "limit_pct": reject_report.get("limit_pct")}

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
class SilverCollisionGuard:
    """Avisa quando a mesma tabela Silver e reescrita na mesma run.
    
    A Silver e por entidade de negocio e idempotente por dat_ref: tanto o
    Parquet local quanto o part-<dat_ref> do Volume sao sobrescritos. Em
    --format all os tres formatos promovem a mesma entidade, entao a ultima
    carga vence em silencio. O guard nao impede a sobrescrita - declara quem 
    sobrescreveu quem, para a contagem da Silver nunca ficar sem explicacao."""
    def __init__(self):
        self._seen: dict[str, str] = {}
        self.warnings: list[str] = []

    def check(self, table_name: str, filename: str) -> str | None:
        origem = Path(filename).name
        anterior = self._seen.get(table_name)
        self._seen[table_name] = origem
        if anterior is None or anterior == origem:
            return None
        msg = "silver/{} reescrita nesta run: {} sobrescreve {}".format(
            table_name, origem, anterior
        )
        print("     [SILVER] [WARN] {}".format(msg))
        self.warnings.append(msg)
        return msg
    
_SILVER_GUARDS: dict[str, SilverCollisionGuard] = {}

def silver_guard(run_id: str) -> SilverCollisionGuard:
    """Guard por run: compartilhado entre cenarios, formatos e os dois runners."""
    return _SILVER_GUARDS.setdefault(run_id, SilverCollisionGuard())

def publish_quarantine_files(storage, filename: str, run_id: str,
                             reject_report: dict | None = None,
                             dlq: bool = False, dat_ref: str | None = None) -> list[dict]:
    from src.connectors.bronze_uploader import publish_quarantine
    candidates = []
    if (reject_report or {}).get("rows_rejected"):
        candidates.append("reject_"+ Path(filename).stem + ".csv")
    if dlq:
        candidates.append(filename)
    out = []
    for name in candidates:
        if not storage.exists("quarantine", name):
            continue
        out.append(publish_quarantine(storage.read_path("quarantine", name),
                                      table_name=Path(filename).stem, run_id=run_id,
                                      dat_ref=dat_ref))
    return out

def quarantine_blocked_silver(storage, parquet_filename: str | None) -> str | None:
    """Retira da Silver o Parquet de uma carga reprovada pelo gate.

    O gate so pode decidir depois do cast, porque e o cast que produz a taxa de
    rejeicao — entao o Parquet ja existe quando o bloqueio acontece. Deixa-lo na
    Silver significa que quem le a camada le dado reprovado sem saber; move-lo
    para a quarentena mantem o artefato auditavel e fora do caminho do consumidor.

    Returns:
        O nome do arquivo movido, ou None quando nada foi movido.
    """
    import config

    if not config.QUARANTINE_BLOCKED_SILVER:
        return None
    if not parquet_filename or not storage.exists("silver", parquet_filename):
        return None
    storage.move(parquet_filename, "silver", "quarantine")
    print("     [GATE] silver/{} retirada da Silver -> quarentena (carga bloqueada)".format(
        parquet_filename))
    return parquet_filename

def run_scenario(scenario: str, run_id: str, fmt: str = "csv", dat_ref: str | None = None,
                 skip_existing: bool = False) -> tuple[list[dict], list[dict]]:
    """Executa um único cenário end-to-end usando a camada Storage."""
    print(f"\n{chr(9552)*66}")
    print(f"  CENARIO: {scenario.upper()}")
    print(f"{chr(9552)*66}")

    # Instancia o backend de storage (local ou MinIO conforme config.py)
    storage = get_storage()
    dat_ref = dat_ref or resolve_dat_ref(run_id)

    # ── 1. Bronze: geração de dados ───────────────────────────────────────
    produced = generate_all(storage, scenario=scenario, fmt=fmt, dat_ref=dat_ref)

    # ── 2. Loop por tabela ────────────────────────────────────────────────
    scenario_metrics = [] 
    publications = []
    for item in produced:
        table             = item["table"]
        filename          = item["filename"]
        contract_filename = item["contract_filename"]

        print(f"\n  -- {table} --")

        # Idempotencia: identidade da carga e (dat_ref + conteudo do arquivo),
        # por isso o SHA-256 do input entra antes de qualquer decisao de pular.
        input_sha = file_sha256(storage.read_path("bronze", filename))
        print(f"     [IDEMPOTENCIA] input sha256={short_sha(input_sha)} ({filename})")
        if announce(storage, table, dat_ref, fmt, skip_existing=skip_existing,
                    input_sha=input_sha):
            continue

        from src.connectors.bronze_uploader import publish_bronze
        publications.append(publish_bronze(storage.read_path("bronze", filename),
                                                   table_name=Path(filename).stem, run_id=run_id,
                                                   dat_ref=dat_ref))

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
            silver_guard(run_id).check(Path(filename).stem, filename)
            parquet_filename = storage.promote_to_parquet(filename, "bronze", "silver", contract=contract, run_id=run_id, dat_ref=dat_ref)
            cast_report = dict(getattr(storage, "last_cast_report", {}) or {})
            reject_report = dict(getattr(storage, "last_reject_report", {}) or {})
            gate = evaluate_gate(table, reject_report, contract=contract)
            if gate["status"] == "BLOCKED":
                retirado = quarantine_blocked_silver(storage, parquet_filename)
                publications.append({"table": table, "status": "BLOCKED", "layer": "silver",
                                     "error": gate["detail"], "rows": 0,
                                     "quarantined_file": retirado})
            else:
                from src.connectors.databricks_uploader import publish_table
                pub = publish_table(storage.read_path("silver", parquet_filename),
                                    table_name=Path(filename).stem, contract=contract, run_id=run_id,
                                    dat_ref=dat_ref)
                publications.append(pub)

        publications.extend(publish_quarantine_files(
            storage,filename, run_id, reject_report=reject_report, dlq=val_result.status == "DLQ",
            dat_ref=dat_ref
            ))
        
        # Gold: métricas agregadas
        m = collect(run_id, val_result, profiler_payload, slm_result,
                    contract=contract, cast_report=cast_report, fmt = fmt,
                    reject_report=reject_report, gate=gate, dat_ref=dat_ref)
        scenario_metrics.append(m)

        # Ledger: a carga concluida passa a ser reconhecivel como reprocessavel
        record_load(storage, table, dat_ref, fmt, run_id,
                    "BLOCKED" if gate["status"] == "BLOCKED" else val_result.status,
                    rows=val_result.rows_valid,
                    input_sha=input_sha, input_file=filename)

    return scenario_metrics, publications

_GATE_LABELS = {
    "MANIFEST_NOT_VALIDATED": "[GOVERNANCA]",
    "VALIDATION_DLQ"        : "[QUARENTENA]",
    "REJECT_ABOVE_TOLERANCE": "[QUALIDADE]",
}

def gate_label(metrics: dict) -> str:
    """Rotulo da coluna publicacao: distingue o motivo de bloqueio
    
    Tres coisas diferentes apareciam como [BLOQUEADO]: manifesto nao validado
    (governanca), tabela em quarentena por schema (DLQ) e rejeicao acima da
    tolerancia (qualidade). A acao do steward e diferente em cada caso.
    """

    status = metrics.get("gate_status")
    if status == "BLOCKED":
        return _GATE_LABELS.get(metrics.get("gate_reason"), "[BLOQUEADO]")
    if status == "PASS_WITH_REJECTS":
        return "[C/ REJEICAO]"
    return "[LIBERADA]"

def pipeline_exit_code(all_metrics: list[dict], publications: list[dict]) -> int:
    dlq = [m for m in all_metrics if m["validation_status"] in ("DLQ", "ERROR")]
    blocked = [m for m in all_metrics if m.get("gate_status") == "BLOCKED"]
    failed = [p for p in publications if p["status"] == "ERROR"]
    return 2 if (dlq or blocked or failed) else 0

def print_summary(all_metrics: list[dict]) -> None:
    """Imprime tabela de resultados no terminal."""
    print(f"\n{'='*66}")
    print("  RESUMO DA EXECUÇÃO")
    print(f"{'='*66}")

    header = f"{'Tabela':<26} {'Cenario':<13} {'Status':<15} {'Publicacao':<12} {'Score':>6}"
    print(header)
    print("-" * 78)

    icons = {"PASS": "[PASS]", "WARNING": "[WARN]", "DLQ": "[DLQ]"}
    for m in all_metrics:
        icon = icons.get(m["validation_status"], "⚪")
        gate = gate_label(m)
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
    parser.add_argument(
             "--dat-ref",
             dest="dat_ref",
             default=None,
             help="Data de referencia da carga (YYYY-MM-DD). Padrao: data do run_id. "
                  "Reprocessar a mesma dat_ref sobrescreve a particao.",
         )
    parser.add_argument(
             "--skip-existing",
             action="store_true",
             help="Pula tabela cuja dat_ref ja foi ingerida com sucesso (carga incremental).",
         )
    return parser

def main():
    args = build_parser().parse_args()

    print(BANNER)

    run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:6]}"
    dat_ref = resolve_dat_ref(run_id, args.dat_ref)
    print(f"  Run ID : {run_id}")
    print(f"  dat_ref: {dat_ref}" + ("  (informada)" if args.dat_ref else "  (do run_id)"))
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
            metrics, pubs = run_scenario(scenario, run_id, fmt=fmt, dat_ref=dat_ref,
                                         skip_existing=args.skip_existing)
            all_metrics.extend(metrics)
            publications.extend(pubs)

    if not all_metrics:
        print("\n  Nada a processar: todas as tabelas da dat_ref {} ja estavam "
              "ingeridas (--skip-existing).\n".format(dat_ref))
        return 0

    # Relatório consolidado
    print_summary(all_metrics)


    # Salva JSON consolidado
    report_name = generate_report(all_metrics)
    summary_name = save_summary(run_id, all_metrics)

    print(f"  Metricas JSON : {summary_name}")
    print(f"  Relatorio MD  : {report_name}")
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
    colisoes = silver_guard(run_id).warnings
    if colisoes:
        print(f" [SILVER] {len(colisoes)} tabela(s) reescrita(s) nesta run "
              f"(idempotencia por dat_ref; ver _ingest_format/_ingest_file na Silver):")
        for msg in colisoes:
            print(f"        {msg}")
    print("\n  Pipeline concluida.\n")

    code = pipeline_exit_code(all_metrics, publications)
    print(" Exit Code   :{} ({})".format(
        code, "tabelas liberadas" if code == 0 else "bloqueio de gate/quarentena"
    ))
    return code


if __name__ == "__main__":
    sys.exit(main())
    
