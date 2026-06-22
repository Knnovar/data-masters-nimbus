#!/usr/bin/env python
"""
setup_prefect.py — Prepara o ambiente Prefect local para a PoC.

Executa tudo que precisa ser feito UMA VEZ antes do primeiro deploy:
  1. Cria o work pool local
  2. Faz o deploy de todos os deployments definidos no prefect.yaml
  3. Imprime os comandos para disparar cada run

Uso:
    # Terminal 1 — servidor Prefect (mantém aberto)
    prefect server start

    # Terminal 2 — setup (roda uma vez)
    python setup_prefect.py

    # Terminal 3 — worker (mantém aberto para executar as runs)
    prefect worker start --pool data-masters-local
"""

import subprocess
import sys


def run(cmd: str, check: bool = True) -> subprocess.CompletedProcess:
    print(f"\n$ {cmd}")
    result = subprocess.run(cmd, shell=True, text=True, capture_output=False)
    if check and result.returncode != 0:
        print(f"  ⚠️  Comando retornou exit code {result.returncode} — continuando.")
    return result


def main():
    print("=" * 60)
    print("  Setup Prefect — Projeto Nimbus PoC")
    print("=" * 60)

    # 1. Work pool
    print("\n── 1. Criando work pool local ──")
    run(
        'prefect work-pool create data-masters-local --type process',
        check=False   # ignora erro se já existir
    )

    # 2. Deploy
    print("\n── 2. Registrando deployments ──")
    run("prefect deploy --all")

    # 3. Instruções finais
    print("\n" + "=" * 60)
    print("  ✅  Setup concluído!")
    print("=" * 60)
    print("""
PRÓXIMOS PASSOS:

  # Em um terminal separado, inicie o worker:
  prefect worker start --pool data-masters-local

  # Depois dispare qualquer deployment:
  prefect deployment run 'data-masters-pipeline/baseline-manual'
  prefect deployment run 'data-masters-pipeline/non-breaking-watch'
  prefect deployment run 'data-masters-pipeline/breaking-watch'

  # Para alterar o cenário em tempo de execução:
  prefect deployment run 'data-masters-pipeline/all-manual' \\
      --param scenario=non_breaking

  # UI: http://localhost:4200
""")


if __name__ == "__main__":
    main()
