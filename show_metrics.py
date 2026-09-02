"""
show_metrics.py - Dashboard de metricas da pipeline no terminal.

Le todos os JSONs de /data/metrics/ e exibe:
  - Evolucao do quality score entre runs
  - Comparativo por tabela e cenario
  - Tendencias de nulos, duplicatas e DLQ
  - Export opcional para CSV

Uso:
    python show_metrics.py                    # ultimo run de cada cenario
    python show_metrics.py --all              # todos os runs
    python show_metrics.py --table tb_clientes
    python show_metrics.py --csv metrics_export.csv
"""

import argparse
import csv
import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from config import METRICS_DIR


# ─────────────────────────────────────────────────────────────────────────────
# Carregamento
# ─────────────────────────────────────────────────────────────────────────────

def load_all_metrics(metrics_dir: Path) -> list[dict]:
    """Carrega todos os registros de metricas, excluindo arquivos summary."""
    records = []
    for path in sorted(metrics_dir.glob("*.json")):
        if "summary" in path.name:
            continue
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            # Arquivo individual de tabela
            if isinstance(data, dict):
                records.append(data)
            # Arquivo summary com lista
            elif isinstance(data, list):
                records.extend(data)
        except Exception:
            continue

    # Ordena por timestamp
    records.sort(key=lambda r: r.get("timestamp", ""))
    return records


def filter_records(
    records: list[dict],
    table: str | None = None,
    scenario: str | None = None,
    last_only: bool = False,
) -> list[dict]:
    if table:
        records = [r for r in records if r.get("table") == table]
    if scenario:
        records = [r for r in records if r.get("scenario") == scenario]
    if last_only:
        # Mantém apenas o run mais recente de cada (table, scenario)
        seen: dict[tuple, dict] = {}
        for r in records:
            key = (r.get("table"), r.get("scenario"))
            seen[key] = r   # sobrescreve - ultimo ganha
        records = list(seen.values())
    return records


# ─────────────────────────────────────────────────────────────────────────────
# Formatacao
# ─────────────────────────────────────────────────────────────────────────────

def _status_tag(status: str) -> str:
    return {"PASS": "[PASS]", "WARNING": "[WARN]", "DLQ": "[DLQ]"}.get(status, "[?]")


def _slm_tag(status: str) -> str:
    return {"SUCCESS": "[OK]", "SKIPPED": "[SKIP]", "ERROR": "[ERR]"}.get(status, "[-]")


def _score_bar(score: float, width: int = 20) -> str:
    """Barra de progresso ASCII para o quality score."""
    filled = int(score / 100 * width)
    bar    = "#" * filled + "-" * (width - filled)
    return f"[{bar}] {score:5.1f}"


def _trend(values: list[float]) -> str:
    """Indica tendencia com base nos dois ultimos valores."""
    if len(values) < 2:
        return "  "
    diff = values[-1] - values[-2]
    if diff > 1:   return "(+)"
    if diff < -1:  return "(-)"
    return "(=)"


# ─────────────────────────────────────────────────────────────────────────────
# Views
# ─────────────────────────────────────────────────────────────────────────────

def view_summary(records: list[dict]) -> None:
    """Resumo geral: ultima run de cada tabela por cenario."""
    if not records:
        print("[INFO] Nenhuma metrica encontrada em data/metrics/")
        return

    # Agrupa por (table, scenario)
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for r in records:
        groups[(r.get("table","?"), r.get("scenario","?"))].append(r)

    print("\n" + "=" * 72)
    print("  DASHBOARD DE METRICAS - PROJETO NIMBUS")
    total_runs = len({r.get("run_id") for r in records})
    print(f"  Runs registrados: {total_runs} | Registros: {len(records)}")
    print("=" * 72)

    # Cabecalho
    print(f"\n  {'Tabela':<30} {'Cenario':<14} {'Status':<8} {'Score':>22}  {'Trend'}")
    print(f"  {'-'*30} {'-'*14} {'-'*8} {'-'*22}  {'-'*5}")

    for (table, scenario), recs in sorted(groups.items()):
        scores = [r.get("quality_score", 0) for r in recs]
        last   = recs[-1]
        tag    = _status_tag(last.get("validation_status","?"))
        bar    = _score_bar(scores[-1])
        trend  = _trend(scores)
        print(f"  {table:<30} {scenario:<14} {tag:<8} {bar}  {trend}")

    # Score medio geral
    all_scores = [r.get("quality_score", 0) for r in records]
    avg = sum(all_scores) / len(all_scores) if all_scores else 0
    print(f"\n  {'Score medio geral':>55}: {avg:5.1f}/100")


def view_evolution(records: list[dict], table: str | None = None) -> None:
    """Evolucao do quality score por run para cada tabela."""
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for r in records:
        groups[(r.get("table","?"), r.get("scenario","?"))].append(r)

    print("\n" + "=" * 72)
    print("  EVOLUCAO POR RUN")
    print("=" * 72)

    for (tbl, scenario), recs in sorted(groups.items()):
        if table and tbl != table:
            continue
        print(f"\n  {tbl} / {scenario}")
        print(f"  {'Run':<32} {'Data':<12} {'Status':<8} {'Score':>22}  {'Nulos%':>7}  {'Dups':>5}")
        print(f"  {'-'*32} {'-'*12} {'-'*8} {'-'*22}  {'-'*7}  {'-'*5}")
        for r in recs:
            ts       = r.get("timestamp","")[:10]
            run_id   = r.get("run_id","")[-18:]
            tag      = _status_tag(r.get("validation_status","?"))
            bar      = _score_bar(r.get("quality_score",0))
            nulls    = f"{r.get('avg_null_pct',0):5.1f}%"
            dups     = str(r.get("duplicate_count",0))
            print(f"  {run_id:<32} {ts:<12} {tag:<8} {bar}  {nulls:>7}  {dups:>5}")


def view_issues(records: list[dict]) -> None:
    """Lista todos os registros com issues ou status DLQ/WARNING."""
    problems = [r for r in records if r.get("validation_status") in ("DLQ","WARNING")
                or r.get("issues") or r.get("warnings")]

    if not problems:
        print("\n  [OK] Nenhum problema registrado nos runs carregados.")
        return

    print("\n" + "=" * 72)
    print(f"  PROBLEMAS REGISTRADOS ({len(problems)} registros)")
    print("=" * 72)

    for r in problems:
        ts    = r.get("timestamp","")[:16].replace("T"," ")
        tag   = _status_tag(r.get("validation_status","?"))
        print(f"\n  {tag} {r.get('table','?')} / {r.get('scenario','?')} [{ts}]")
        for issue in r.get("issues",[]):
            print(f"       [ERR]  {issue}")
        for warn in r.get("warnings",[]):
            # Omite o aviso de DRAFT para nao poluir o dashboard
            if "DRAFT" not in warn:
                print(f"       [WARN] {warn}")


def view_slm(records: list[dict]) -> None:
    """Status do enriquecimento SLM por run."""
    print("\n" + "=" * 72)
    print("  STATUS SLM")
    print("=" * 72)
    print(f"\n  {'Tabela':<30} {'Cenario':<14} {'SLM':<7} {'Inference (ms)':>15} "
          f"{'Modelo':<14} {'Tok/s':>7} {'Cobertura':>10}")
    print(f"  {'-'*30} {'-'*14} {'-'*7} {'-'*15} {'-'*14} {'-'*7} {'-'*10}")

    # Ultimo registro de cada (table, scenario)
    seen: dict[tuple, dict] = {}
    for r in records:
        seen[(r.get("table"), r.get("scenario"))] = r

    slm_ok   = sum(1 for r in seen.values() if r.get("slm_status") == "SUCCESS")
    slm_skip = sum(1 for r in seen.values() if r.get("slm_status") == "SKIPPED")
    slm_err  = sum(1 for r in seen.values() if r.get("slm_status") == "ERROR")

    for (table, scenario), r in sorted(seen.items()):
        tag = _slm_tag(r.get("slm_status","?"))
        ms  = r.get("slm_inference_ms", 0)
        ms_str = f"{ms:,.0f} ms" if ms else "-"
        model = r.get("slm_model") or "-"
        tps = r.get("slm_tokens_per_s")
        cov = r.get("slm_column_coverage_pct")
        trunc = " *" if r.get("slm_truncated") else ""
        print(f"  {table:<30} {scenario:<14} {tag:<7} {ms_str:>15} "
              f"{model:<14} {(f'{tps:,.1f}' if tps else '-'):>7} " 
              f"{(f'{cov:,.1f}%' if cov else '-'):>10}{trunc}")

    if any(r.get("slm_truncated") for r in seen.values()):
        print(" (*) resposta truncada pelo num_predict (SLM_NUM_PREDICT)")
    if slm_ok:
        print(" [INFO] Comparativo entre modelos: python show_metrics.py --models")
    print(f"\n  Documentadas: {slm_ok} | Ignoradas: {slm_skip} | Erro: {slm_err}")
    if slm_skip > 0:
        print("  [INFO] Para ativar o SLM: ollama serve && ollama pull phi3.5")

def view_models(records: list[dict]) -> None:
    """Compara modelos SLM: velocidade e caracteristicas de saida.
    
    Usa todos os runs (nao so o ultimo), agrupando por slm_model - e assim 
    que se compara phi3.5 x phi4 sobre as mesmas tabelas.
    """
    runs =[r for r in records if r.get("slm_status") == "SUCCESS" and r.get("slm_model")]
    print("\n" + "=" * 100)
    print("  COMPARATIVO DE MODELOS SLM")
    print("=" * 100)
    if not runs:
        print("\n  [INFO] Nenhuma inferencia bem-sucedida nesta execucao.")
        return
    by_model: dict[str, list[dict]] = {}
    for r in runs:
        by_model.setdefault(r["slm_model"], []).append(r)

    def avg(rows, key):
        vals = [x[key] for x in rows if isinstance(x.get(key), (int,float))]
        return sum(vals) / len(vals) if vals else 0

    print(f"\n  {'Modelo':<16} {'Runs':>5} {'Wall (ms)':>15} {'Carga':>10} {'Prompt(ms)':>11} "
          f"{'Geracao(ms)':>12} {'Tok saida':>10} {'Tok/s':>8} {'Cobertura':>10} {'Trunc':>6}")
    print(" " + "-" * 98)

    for model, rows in sorted(by_model.items()):
        trunc= sum(1 for x in rows if x.get("slm_truncated"))
        print(f"  {model:<16} {len(rows):>5} "
              f"{avg(rows, 'slm_inference_ms'):>10,.0f} "
                f"{avg(rows, 'slm_load_ms'):>10,.0f} "
                f"{avg(rows, 'slm_prompt_eval_ms'):>11,.0f} "
                f"{avg(rows, 'slm_eval_ms'):>12,.0f} "
                f"{avg(rows, 'slm_output_tokens'):>10,.0f} "
                f"{avg(rows, 'slm_tokens_per_s'):>8,.1f} "
                f"{avg(rows, 'slm_column_coverage_pct'):>9,.1f}% "
                f"{trunc:>6}")
    print("\n  Por tabela:")
    print(f"  {'Tabela':<30} {'Modelo':<16} {'Wall(ms)':>10}  {'Tokens':>8} {'Tok saida':>10} {'Cobertura':>10}")
    print("  " + "-" * 84)
    for r in sorted(runs, key=lambda x: (x.get("table"), x.get("slm_model"))):
        print(f"  {r.get('table'):<26} {r.get('slm_model'):<16} "
              f"{r.get('slm_inference_ms') or 0:>10,.0f} "
              f"{r.get('slm_tokens_per_s') or 0:>8,.1f} "
              f"{r.get('slm_output_tokens') or 0:>10,.0f} "
              f"{r.get('slm_column_coverage_pct') or 0:>9,.1f}%")    
    missing = {r['slm_model']: r.get("slm_columns_missing") or [] for r in runs}
    for model, cols in sorted(missing.items()):
        if cols:
            print(f"\n  [INFO] Colunas ausentes no modelo {model}: {', '.join(cols)}")

    print("\n Wall = tempo total do request | Carga = load do modelo (alto no 1o run) | "
          "\n Geracao = eval_duration | Tok/s = tokens de saida / tempo de geracao")

# ─────────────────────────────────────────────────────────────────────────────
# Export CSV
# ─────────────────────────────────────────────────────────────────────────────

def export_csv(records: list[dict], output_path: Path) -> None:
    """Exporta todos os registros para CSV (analise no Excel)."""
    if not records:
        print("[INFO] Nenhum registro para exportar.")
        return

    fields = [
        "run_id", "timestamp", "table", "scenario",
        "validation_status", "evolution_type",
        "rows_total", "rows_valid", "duplicate_count",
        "avg_null_pct", "profiling_ms",
        "slm_status", "slm_inference_ms", "quality_score",
        "slm_model", "slm_num_predict", "slm_load_ms", "slm_prompt_eval_ms", 
        "slm_prompt_tokens", "slm_output_words", "slm_output_tokens", "slm_eval_ms",
        "slm_tokens_per_s", "slm_column_coverage_pct", "slm_truncated",
        "slm_output_chars",
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)

    print(f"\n  [OK] {len(records)} registros exportados para: {output_path}")


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Dashboard de metricas - Projeto Nimbus")
    parser.add_argument("--all",      action="store_true", help="Exibe todos os runs (padrao: ultimo por tabela/cenario)")
    parser.add_argument("--table",    default=None,        help="Filtra por tabela (ex: tb_clientes)")
    parser.add_argument("--scenario", default=None,        help="Filtra por cenario (baseline|non_breaking|breaking)")
    parser.add_argument("--issues",   action="store_true", help="Exibe apenas registros com problemas")
    parser.add_argument("--slm",      action="store_true", help="Exibe status do enriquecimento SLM")
    parser.add_argument("--csv",      default=None,        help="Exporta para CSV (ex: --csv metricas.csv)")
    parser.add_argument( "--models",  action="store_true", help = "Compara desempenho de modelos SLM (ex: phi3.5 x phi4)")
    args = parser.parse_args()

    records = load_all_metrics(METRICS_DIR)

    if args.models:
            view_models(filter_records(records, table=args.table, scenario=args.scenario, last_only = False))
    elif args.issues:
        view_issues(filter_records(records, table=args.table, scenario=args.scenario))
    elif args.slm:
        view_slm(filtered)
        

    if not records:
        print("[INFO] Nenhuma metrica encontrada. Execute o pipeline primeiro:")
        print("       python run_pipeline.py --scenario baseline")
        sys.exit(0)

    filtered = filter_records(
        records,
        table    = args.table,
        scenario = args.scenario,
        last_only= not args.all,
    )

    if args.csv:
        export_csv(filtered, Path(args.csv))
        return

    # Exibe views conforme flags
    if args.issues:
        view_issues(filter_records(records, table=args.table, scenario=args.scenario))
    elif args.slm:
        view_slm(filtered)
    else:
        view_summary(filtered)
        if args.all or args.table:
            view_evolution(
                filter_records(records, table=args.table, scenario=args.scenario),
                table=args.table,
            )
        view_issues(filter_records(records, table=args.table, scenario=args.scenario))
        view_slm(filtered)

    print()


if __name__ == "__main__":
    main()
