"""
src/ingestion/idempotency.py — Idempotencia e reprocessamento por dat_ref.

A data de referencia (dat_ref) e a identidade da carga, nao o run_id: o run_id
muda a cada execucao, a dat_ref identifica a janela de dados. Duas execucoes da
mesma dat_ref sobrescrevem a mesma particao, em vez de acumular duplicata.

A dat_ref sozinha, porem, nao distingue "rodei de novo o mesmo arquivo" de
"recebi um arquivo diferente para a mesma janela". Por isso cada carga tambem
registra o SHA-256 do arquivo de entrada, e o ledger classifica a carga em tres
situacoes:

    FIRST_LOAD          primeira carga da chave (tabela, dat_ref, formato)
    REPROCESS_IDENTICAL mesma dat_ref, arquivo byte a byte igual
    REPROCESS_MODIFIED  mesma dat_ref, arquivo diferente  <- exige atencao

REPROCESS_MODIFIED e o caso perigoso: a particao vai ser sobrescrita por um
conteudo que nao e o que foi auditado antes. O pipeline continua permitindo
(reprocessar e legitimo), mas nunca em silencio — e `--skip-existing` jamais
pula uma carga cujo arquivo mudou, porque ai o "ja ingerido" seria mentira.

O ledger e gravado na camada de metricas (`_ingest_ledger.json`), pelo storage
configurado, e por isso funciona igual em LocalStorage e MinIO/S3.
"""

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path

LEDGER_NAME = "_ingest_ledger.json"

# Situacoes de carga reconhecidas pelo ledger.
FIRST_LOAD          = "FIRST_LOAD"
REPROCESS_IDENTICAL = "REPROCESS_IDENTICAL"
REPROCESS_MODIFIED  = "REPROCESS_MODIFIED"

# Leitura em blocos: o hash nao pode depender do arquivo caber na memoria.
_HASH_CHUNK = 1024 * 1024

_DAT_REF_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def resolve_dat_ref(run_id, cli_value=None):
    """Precedencia: --dat-ref > DAT_REF (env) > data do run_id > hoje."""
    import config as cfg

    explicit = cli_value or getattr(cfg, "DAT_REF", None)
    if explicit:
        if not _DAT_REF_RE.match(str(explicit)):
            raise ValueError("dat_ref invalida: '{}' (esperado YYYY-MM-DD)".format(explicit))
        return str(explicit)
    m = re.match(r"^run_(\d{4})(\d{2})(\d{2})_", run_id or "")
    return "-".join(m.groups()) if m else datetime.now().strftime("%Y-%m-%d")


def file_sha256(path):
    """SHA-256 do arquivo de entrada, lido em blocos.

    Retorna None quando o caminho nao existe ou nao e legivel: a ausencia de
    hash degrada o controle para "somente dat_ref", nunca interrompe a carga.
    """
    if not path:
        return None
    p = Path(path)
    if not p.is_file():
        return None
    h = hashlib.sha256()
    try:
        with open(p, "rb") as f:
            for chunk in iter(lambda: f.read(_HASH_CHUNK), b""):
                h.update(chunk)
    except OSError:
        return None
    return h.hexdigest()


def short_sha(value, size=12):
    """Prefixo do hash para log — o hash inteiro nao cabe na tela."""
    return (value or "")[:size] or "-"


def _key(table, dat_ref, fmt):
    return "{}|{}|{}".format(table, dat_ref, fmt)


def load_ledger(storage):
    """Ledger completo; dict vazio quando ainda nao existe ou esta corrompido."""
    if not storage.exists("metrics", LEDGER_NAME):
        return {}
    try:
        with open(storage.read_path("metrics", LEDGER_NAME), encoding="utf-8") as f:
            return json.load(f) or {}
    except (ValueError, OSError):
        print("   [IDEMPOTENCIA] ledger ilegivel - tratando como primeira carga")
        return {}


def previous_load(storage, table, dat_ref, fmt):
    """Carga anterior de (tabela, dat_ref, formato), ou None."""
    return load_ledger(storage).get(_key(table, dat_ref, fmt))


def classify_load(prev, input_sha=None):
    """Classifica a carga em FIRST_LOAD / REPROCESS_IDENTICAL / REPROCESS_MODIFIED.

    Sem carga anterior, e primeira carga. Com carga anterior e sem hash de um
    dos dois lados, nao ha como afirmar que o conteudo mudou — assume-se
    identico, que e o comportamento anterior a este controle.
    """
    if not prev:
        return FIRST_LOAD
    prev_sha = prev.get("input_sha256")
    if not prev_sha or not input_sha:
        return REPROCESS_IDENTICAL
    return REPROCESS_IDENTICAL if prev_sha == input_sha else REPROCESS_MODIFIED


def record_load(storage, table, dat_ref, fmt, run_id, status, rows=0,
                input_sha=None, input_file=None):
    """Registra a carga concluida - uma entrada por (tabela, dat_ref, formato).

    Alem do hash desta carga, guarda o hash anterior quando o conteudo mudou
    (`previous_sha256`), para que a divergencia continue auditavel depois de a
    particao ter sido sobrescrita.
    """
    ledger = load_ledger(storage)
    prev   = ledger.get(_key(table, dat_ref, fmt), {})
    situation = classify_load(prev, input_sha)
    entry = {
        "table"      : table,
        "dat_ref"    : dat_ref,
        "format"     : fmt,
        "run_id"     : run_id,
        "status"     : status,
        "rows"       : rows,
        "ingested_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "reprocess_count": prev.get("reprocess_count", -1) + 1,
        "input_file"    : input_file or prev.get("input_file"),
        "input_sha256"  : input_sha or prev.get("input_sha256"),
        "input_situation": situation,
    }
    if situation == REPROCESS_MODIFIED:
        entry["previous_sha256"] = prev.get("input_sha256")
    ledger[_key(table, dat_ref, fmt)] = entry
    storage.write_text("metrics", LEDGER_NAME,
                       json.dumps(ledger, ensure_ascii=False, indent=2))
    return entry


def announce(storage, table, dat_ref, fmt, skip_existing=False, input_sha=None):
    """Declara no log se e primeira carga, reprocessamento igual ou divergente.

    Retorna True quando a tabela deve ser pulada (--skip-existing com carga
    anterior bem-sucedida e mesmo arquivo). Reprocessar e permitido por padrao:
    o que nao pode e reprocessar em silencio — e arquivo diferente na mesma
    dat_ref nunca e pulado, mesmo com --skip-existing.
    """
    prev = previous_load(storage, table, dat_ref, fmt)
    if not prev:
        return False

    situation = classify_load(prev, input_sha)
    origem = "run {} em {}".format(prev.get("run_id"), prev.get("ingested_at"))
    concluida = prev.get("status") in ("PASS", "WARNING")

    if situation == REPROCESS_MODIFIED:
        print("     [IDEMPOTENCIA] ENTRADA DIVERGENTE em {} dat_ref={}: arquivo "
              "difere da carga anterior ({}) - sha {} -> {}".format(
                  table, dat_ref, origem,
                  short_sha(prev.get("input_sha256")), short_sha(input_sha)))
        if skip_existing and concluida:
            print("     [IDEMPOTENCIA] --skip-existing ignorado: o conteudo mudou, "
                  "a particao precisa ser reprocessada")
        return False

    if skip_existing and concluida:
        print("     [IDEMPOTENCIA] {} dat_ref={} ja ingerida ({}) - pulada".format(
            table, dat_ref, origem))
        return True

    print("     [IDEMPOTENCIA] reprocessamento de {} dat_ref={} ({}, status {}, "
          "arquivo identico sha {}) - a particao sera sobrescrita".format(
              table, dat_ref, origem, prev.get("status"),
              short_sha(prev.get("input_sha256") or input_sha)))
    return False
