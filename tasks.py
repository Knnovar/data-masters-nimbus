#!/usr/bin/env python3
"""
tasks.py — Runner de tarefas cross-platform (Projeto Nimbus)

Substitui o Makefile em ambientes Windows, onde `make` nao e nativo.
Funciona identico em Windows, Mac e Linux.

Uso:
    python tasks.py <comando> [opcoes]
    python tasks.py help
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent


def run(cmd: list[str]) -> int:
    print(f"$ {' '.join(cmd)}\n")
    return subprocess.call(cmd, cwd=ROOT)


# ── Pipeline ──────────────────────────────────────────────────────────────────

def cmd_run(args):
    # Executa todos os cenarios (baseline/non_breaking/breaking) nos
    # tres formatos suportados (csv/json/fixed) — execucao completa.
    return run(["python", "run_pipeline.py", "--scenario", "all", "--format", "all"])

def cmd_baseline(args):
    fmt = _get_opt(args, "--format") or "all"
    return run(["python", "run_pipeline.py", "--scenario", "baseline", "--format", fmt])

def cmd_non_breaking(args):
    fmt = _get_opt(args, "--format") or "all"
    return run(["python", "run_pipeline.py", "--scenario", "non_breaking", "--format", fmt])

def cmd_breaking(args):
    fmt = _get_opt(args, "--format") or "all"
    return run(["python", "run_pipeline.py", "--scenario", "breaking", "--format", fmt])

def cmd_all_formats(args):
    return run(["python", "run_pipeline.py", "--scenario", "baseline", "--format", "all"])


# ── Dashboard ─────────────────────────────────────────────────────────────────

def cmd_metrics(args):
    return run(["python", "show_metrics.py"])

def cmd_metrics_all(args):
    return run(["python", "show_metrics.py", "--all"])

def cmd_issues(args):
    return run(["python", "show_metrics.py", "--issues"])

def cmd_slm(args):
    return run(["python", "show_metrics.py", "--slm"])

def cmd_export(args):
    return run(["python", "show_metrics.py", "--csv", "data/metrics_export.csv"])


# ── Manifest ──────────────────────────────────────────────────────────────────

def cmd_check_manifest(args):
    file = _get_opt(args, "--file")
    if not file:
        print("Uso: python tasks.py check-manifest --file data/contracts/tb_clientes.yaml")
        return 1
    return run(["python", "-m", "src.manifest.manifest_validator", "--file", file, "--check-only"])

def cmd_validate_manifest(args):
    file    = _get_opt(args, "--file")
    steward = _get_opt(args, "--steward")
    if not file or not steward:
        print('Uso: python tasks.py validate-manifest --file <path> --steward "Nome"')
        return 1
    return run(["python", "-m", "src.manifest.manifest_validator",
                "--file", file, "--steward", steward])

def cmd_extract_sas(args):
    file  = _get_opt(args, "--file")
    table = _get_opt(args, "--table")
    if not file or not table:
        print("Uso: python tasks.py extract-sas --file <path.sas7bdat> --table tb_nome")
        return 1
    output = f"data/contracts/{table}.yaml"
    return run(["python", "-m", "src.manifest.extractor_sas7bdat",
                "--file", file, "--table", table, "--output", output, "--enrich"])

def cmd_extract_csv(args):
    file  = _get_opt(args, "--file")
    table = _get_opt(args, "--table")
    if not file or not table:
        print("Uso: python tasks.py extract-csv --file <path.csv> --table tb_nome")
        return 1
    output = f"data/contracts/{table}.yaml"
    return run(["python", "-m", "src.manifest.extractor_csv",
                "--file", file, "--table", table, "--output", output, "--enrich"])


# ── Prefect ───────────────────────────────────────────────────────────────────

def cmd_prefect_setup(args):
    return run(["python", "setup_prefect.py"])

def cmd_prefect_run(args):
    return run(["prefect", "deployment", "run", "data-masters-pipeline/baseline-manual"])


# ── Testes ────────────────────────────────────────────────────────────────────

def cmd_test(args):
    return run(["python", "tests/run_tests.py", "-v"])


# ── Setup e limpeza ───────────────────────────────────────────────────────────

def cmd_setup(args):
    return run(["pip", "install", "-r", "requirements.txt"])

def cmd_clean(args):
    import shutil
    removed = 0
    for path in ROOT.rglob("__pycache__"):
        shutil.rmtree(path, ignore_errors=True)
        removed += 1
    print(f"Removidos {removed} diretorios __pycache__")
    return 0

def cmd_clean_data(args):
    confirm = input("Isso remove TODOS os dados gerados em data/. Confirma? [s/N] ")
    if confirm.lower() != "s":
        print("Cancelado.")
        return 0
    import shutil
    for sub in ["landing", "processed", "quarantine", "contracts", "metrics", "reports"]:
        d = ROOT / "data" / sub
        if d.exists():
            for f in d.glob("*"):
                if f.is_file():
                    f.unlink()
    print("Dados removidos.")
    return 0


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_opt(args: list[str], flag: str) -> str | None:
    if flag in args:
        idx = args.index(flag)
        if idx + 1 < len(args):
            return args[idx + 1]
    return None


COMMANDS = {
    "run"               : (cmd_run,              "Executa TODOS os cenarios x TODOS os formatos (csv/json/fixed)"),
    "baseline"          : (cmd_baseline,          "Cenario baseline, todos os formatos (use --format csv|json|fixed p/ restringir)"),
    "non-breaking"      : (cmd_non_breaking,      "Cenario non_breaking, todos os formatos (use --format p/ restringir)"),
    "breaking"          : (cmd_breaking,          "Cenario breaking/DLQ, todos os formatos (use --format p/ restringir)"),
    "all-formats"       : (cmd_all_formats,       "Atalho: baseline nos 3 formatos (equivalente a baseline sem --format)"),
    "metrics"           : (cmd_metrics,           "Resumo do ultimo run"),
    "metrics-all"       : (cmd_metrics_all,       "Historico completo de runs"),
    "issues"            : (cmd_issues,            "Lista apenas problemas (DLQ/WARNING)"),
    "slm"               : (cmd_slm,               "Status do enriquecimento SLM"),
    "export"            : (cmd_export,            "Exporta metricas para CSV"),
    "check-manifest"    : (cmd_check_manifest,    "Verifica pendencias de um manifest (--file)"),
    "validate-manifest" : (cmd_validate_manifest, "Promove DRAFT->VALIDATED (--file --steward)"),
    "extract-sas"       : (cmd_extract_sas,       "Extrai manifest de SAS7BDAT (--file --table)"),
    "extract-csv"       : (cmd_extract_csv,       "Extrai manifest de CSV (--file --table)"),
    "prefect-setup"     : (cmd_prefect_setup,     "Cria work pool e registra deployments"),
    "prefect-run"       : (cmd_prefect_run,       "Dispara run baseline via Prefect"),
    "test"              : (cmd_test,              "Roda a suite de testes (148 testes)"),
    "setup"             : (cmd_setup,             "Instala dependencias"),
    "clean"             : (cmd_clean,             "Remove __pycache__"),
    "clean-data"        : (cmd_clean_data,        "Remove dados gerados (pede confirmacao)"),
}


def print_help():
    print("\nProjeto Nimbus — Task Runner\n")
    print("Uso: python tasks.py <comando> [opcoes]\n")
    print("Comandos disponiveis:\n")
    width = max(len(c) for c in COMMANDS)
    for name, (_, desc) in COMMANDS.items():
        print(f"  {name:<{width}}  {desc}")
    print()


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("help", "-h", "--help"):
        print_help()
        sys.exit(0)

    command = sys.argv[1]
    args    = sys.argv[2:]

    if command not in COMMANDS:
        print(f"Comando desconhecido: '{command}'\n")
        print_help()
        sys.exit(1)

    func, _ = COMMANDS[command]
    sys.exit(func(args) or 0)


if __name__ == "__main__":
    main()
