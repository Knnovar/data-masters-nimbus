#!/usr/bin/env python3
"""
nimbus_up.py — Sobe o object storage local em um comando (Projeto Nimbus)

Idempotente: na primeira execucao gera o .env com credencial aleatoria; nas
seguintes reaproveita a credencial existente. Regenerar credencial com o volume
antigo no lugar produz SignatureDoesNotMatch, por isso o .env nunca e sobrescrito.

Uso:
    python scripts/nimbus_up.py             # sobe minio, cria buckets, mostra o resumo
    python scripts/nimbus_up.py --reset     # apaga o volume e recria do zero
    python scripts/nimbus_up.py --print-env # imprime as linhas de export (para `eval`)
"""

import argparse
import os
import secrets
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT     = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT / ".env"
TEMPLATE = ROOT / ".env.example"

ENDPOINT      = "localhost:9000"
CONSOLE       = "http://localhost:9001"
HEALTH_URL    = "http://localhost:9000/minio/health/live"
HEALTH_TIMEOUT = 90


def _log(msg: str) -> None:
    print("[nimbus-up] {}".format(msg))


def _compose(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    cmd = ["docker", "compose", *args]
    return subprocess.run(cmd, cwd=ROOT, check=check, text=True,
                          capture_output=True)


def read_env_file() -> dict[str, str]:
    """Le o .env em pares chave=valor, ignorando comentarios e linhas vazias."""
    if not ENV_FILE.exists():
        return {}
    valores: dict[str, str] = {}
    for linha in ENV_FILE.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        chave, _, valor = linha.partition("=")
        valores[chave.strip()] = valor.strip().strip('"').strip("'")
    return valores


def ensure_credentials() -> tuple[str, str, bool]:
    """Garante MINIO_ACCESS_KEY/MINIO_SECRET_KEY no .env. Nunca sobrescreve."""
    valores = read_env_file()
    access, secret = valores.get("MINIO_ACCESS_KEY", ""), valores.get("MINIO_SECRET_KEY", "")
    if access and secret:
        return access, secret, False

    if not ENV_FILE.exists():
        base = TEMPLATE.read_text(encoding="utf-8") if TEMPLATE.exists() else ""
        ENV_FILE.write_text(base, encoding="utf-8")

    novo_access = access or "nimbus-" + secrets.token_hex(6)
    novo_secret = secret or secrets.token_urlsafe(32)

    conteudo = ENV_FILE.read_text(encoding="utf-8").splitlines()
    saida, vistos = [], set()
    for linha in conteudo:
        chave = linha.split("=", 1)[0].strip() if "=" in linha else ""
        if chave == "MINIO_ACCESS_KEY":
            saida.append("MINIO_ACCESS_KEY={}".format(novo_access))
            vistos.add(chave)
        elif chave == "MINIO_SECRET_KEY":
            saida.append("MINIO_SECRET_KEY={}".format(novo_secret))
            vistos.add(chave)
        else:
            saida.append(linha)
    if "MINIO_ACCESS_KEY" not in vistos:
        saida.append("MINIO_ACCESS_KEY={}".format(novo_access))
    if "MINIO_SECRET_KEY" not in vistos:
        saida.append("MINIO_SECRET_KEY={}".format(novo_secret))

    ENV_FILE.write_text("\n".join(saida).rstrip() + "\n", encoding="utf-8")
    try:
        ENV_FILE.chmod(0o600)
    except OSError:
        pass
    return novo_access, novo_secret, True


def wait_health(timeout: int = HEALTH_TIMEOUT) -> bool:
    limite = time.time() + timeout
    while time.time() < limite:
        try:
            with urllib.request.urlopen(HEALTH_URL, timeout=3) as resp:
                if resp.status == 200:
                    return True
        except (urllib.error.URLError, OSError):
            pass
        time.sleep(2)
    return False


def create_buckets(access: str, secret: str) -> list[str]:
    """Cria os buckets pelo mesmo codigo do pipeline (get_storage)."""
    os.environ.update({
        "USE_MINIO"       : "true",
        "MINIO_ENDPOINT"  : ENDPOINT,
        "MINIO_ACCESS_KEY": access,
        "MINIO_SECRET_KEY": secret,
    })
    sys.path.insert(0, str(ROOT))
    import config as cfg
    cfg.USE_MINIO        = True
    cfg.MINIO_ENDPOINT   = ENDPOINT
    cfg.MINIO_ACCESS_KEY = access
    cfg.MINIO_SECRET_KEY = secret
    from src.storage.storage import get_storage

    storage = get_storage()               # cria os buckets que faltarem
    camadas = sorted(storage._layers)
    for camada in camadas:
        storage.list(camada)              # falha aqui = credencial divergente
    return [storage._layers[c] for c in camadas]


def print_env_lines(access: str, secret: str) -> None:
    print("export USE_MINIO=true")
    print("export MINIO_ENDPOINT={}".format(ENDPOINT))
    print("export MINIO_ACCESS_KEY={}".format(access))
    print("export MINIO_SECRET_KEY={}".format(secret))


def main() -> int:
    parser = argparse.ArgumentParser(description="Sobe o MinIO local do Nimbus")
    parser.add_argument("--reset", action="store_true",
                        help="apaga o volume minio_data antes de subir")
    parser.add_argument("--print-env", action="store_true",
                        help="imprime apenas as linhas de export (para eval/source)")
    args = parser.parse_args()

    access, secret, gerada = ensure_credentials()

    if args.print_env:
        print_env_lines(access, secret)
        return 0

    _log("credencial gerada agora no .env" if gerada else "credencial reaproveitada do .env")

    if args.reset:
        _log("removendo containers e volumes (--reset)")
        _compose("down", "-v", check=False)

    _log("subindo o servico minio")
    resultado = _compose("up", "-d", "minio", check=False)
    if resultado.returncode != 0:
        print(resultado.stderr.strip(), file=sys.stderr)
        return resultado.returncode

    _log("aguardando health check")
    if not wait_health():
        _log("ERRO: MinIO nao respondeu em {}s. Veja: docker compose logs minio".format(HEALTH_TIMEOUT))
        return 1

    _log("criando buckets")
    try:
        buckets = create_buckets(access, secret)
    except Exception as exc:                                  # noqa: BLE001
        texto = str(exc)
        if "SignatureDoesNotMatch" in texto or "InvalidAccessKeyId" in texto:
            _log("ERRO: o volume minio_data guarda uma credencial diferente da do .env.")
            _log("      Rode: python scripts/nimbus_up.py --reset  (apaga os dados do MinIO local)")
            return 1
        _log("ERRO ao criar buckets: {}".format(texto))
        return 1

    print()
    print("MinIO pronto.")
    print("  endpoint : {}".format(ENDPOINT))
    print("  console  : {}  (usuario/senha = MINIO_ACCESS_KEY/MINIO_SECRET_KEY do .env)".format(CONSOLE))
    print("  buckets  : {}".format(", ".join(buckets)))
    print("  credencial: no .env (fora do Git); veja com  python tasks.py minio-creds")
    print()
    print("Rodar o pipeline sem exportar nada:   python tasks.py demo")
    print("Exportar no shell atual (bash/zsh):   eval \"$(python scripts/nimbus_up.py --print-env)\"")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
