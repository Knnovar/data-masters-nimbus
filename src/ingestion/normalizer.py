"""
src/ingestion/normalizer.py — Normalizador de encoding para a landing zone.

Atua ANTES do validator garantindo que qualquer arquivo chegue
ao pipeline em UTF-8 com terminadores LF.

Responsabilidades:
  1. Detectar encoding via chardet
  2. Converter para UTF-8
  3. Normalizar line endings (CRLF/CR -> LF)
  4. Remover BOM se presente
  5. Preservar original em _originals/
  6. EBCDIC: detecta, avisa e nao converte (encaminha para quarentena)
"""

import shutil
from datetime import datetime
from pathlib import Path

import chardet

_SUPPORTED = {
    "utf-8","utf-8-sig","latin-1","iso-8859-1","iso-8859-15",
    "cp1252","windows-1252","cp850","cp437",
}
_EBCDIC_VARIANTS = {"cp037","cp500","cp1140","ibm037","ebcdic"}
_CONFIDENCE_THRESHOLD = 0.80


def normalize(file_path: Path, backup: bool = True, originals_dir=None) -> dict:
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Arquivo nao encontrado: {file_path}")

    result = {
        "status": "ok", "original_encoding": "unknown", "confidence": 0.0,
        "bom_removed": False, "line_endings": "LF",
        "backup_path": None, "normalized_at": datetime.now().isoformat(),
        "warning": None,
    }

    raw_bytes  = file_path.read_bytes()
    detected   = chardet.detect(raw_bytes[:8192])
    enc_raw    = (detected.get("encoding") or "latin-1").lower().replace("-","").replace("_","")
    enc_chardet= detected.get("encoding") or "latin-1"
    confidence = detected.get("confidence") or 0.0

    result["original_encoding"] = enc_chardet
    result["confidence"]        = round(confidence, 3)

    if any(e in enc_raw for e in _EBCDIC_VARIANTS):
        result["status"]  = "ebcdic"
        result["warning"] = (
            f"Encoding EBCDIC detectado ({enc_chardet}). "
            "Solicite ao time de infraestrutura a reconversao via middleware."
        )
        print(f"   [NORM] [{file_path.name}] EBCDIC detectado - requer conversao manual")
        return result

    if confidence < _CONFIDENCE_THRESHOLD and enc_raw not in {e.replace("-","") for e in _SUPPORTED}:
        result["warning"] = (
            f"Encoding ({enc_chardet}) com confianca baixa ({confidence:.0%}). "
            "Usando latin-1 como fallback."
        )
        enc_chardet = "latin-1"
        result["original_encoding"] = "latin-1 (fallback)"

    bom_removed = False
    if raw_bytes.startswith(b"\xef\xbb\xbf"):
        raw_bytes   = raw_bytes[3:]
        bom_removed = True
    elif raw_bytes.startswith(b"\xff\xfe"):
        raw_bytes   = raw_bytes[2:]
        bom_removed = True
    result["bom_removed"] = bom_removed

    is_utf8 = enc_raw in {"utf8","utf8sig","ascii"}
    if is_utf8 and not bom_removed:
        content   = raw_bytes.decode("utf-8", errors="replace")
        le_status = _detect_line_endings(content)
        if le_status == "LF":
            result["status"] = "already_utf8"
            result["line_endings"] = "LF"
            print(f"   [NORM] [{file_path.name}] Ja e UTF-8/LF - sem alteracao")
            return result

    if backup:
        orig_dir = originals_dir or (file_path.parent / "_originals")
        Path(orig_dir).mkdir(parents=True, exist_ok=True)
        backup_path = Path(orig_dir) / file_path.name
        shutil.copy2(file_path, backup_path)
        result["backup_path"] = str(backup_path)

    try:
        content = raw_bytes.decode(enc_chardet, errors="replace")
    except (LookupError, UnicodeDecodeError):
        content = raw_bytes.decode("latin-1", errors="replace")
        result["warning"] = f"Fallback para latin-1: codec {enc_chardet} nao disponivel."

    le_status         = _detect_line_endings(content)
    content           = content.replace("\r\n", "\n").replace("\r", "\n")
    result["line_endings"] = f"{le_status}->LF" if le_status != "LF" else "LF"

    file_path.write_bytes(content.encode("utf-8"))
    print(f"   [NORM] [{file_path.name}] {enc_chardet} -> UTF-8 | {result['line_endings']}")
    return result


def _detect_line_endings(content: str) -> str:
    has_crlf = "\r\n" in content
    # Remove os \n que fazem parte de \r\n antes de verificar \n isolado
    without_crlf = content.replace("\r\n", "")
    has_lone_lf  = "\n" in without_crlf
    has_cr       = "\r" in without_crlf
    if has_crlf and has_lone_lf: return "mixed"
    if has_crlf: return "CRLF"
    if has_cr:   return "CR"
    return "LF"
