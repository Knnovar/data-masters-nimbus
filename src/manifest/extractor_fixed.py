"""
src/manifest/extractor_fixed.py — Extrator para arquivos posicionais (fixed-width).

Modo A: leiaute fornecido (TXT / CSV / XLSX em data/layouts/)
Modo B: inferencia experimental (--infer)

Convencao de nome automatica:
  data/layouts/<table>_layout.txt  (prioridade 1)
  data/layouts/<table>_layout.csv  (prioridade 2)
  data/layouts/<table>_layout.xlsx (prioridade 3)
"""

import argparse, csv, sys, tempfile, os
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.manifest.extractor_base  import ExtractorBase
from src.manifest.manifest_writer import ManifestWriter

_LAYOUTS_DIR = Path("data/layouts")

_FIXED_TYPE_MAP = {
    "char":"string","character":"string","c":"string","varchar":"string","alpha":"string","an":"string",
    "numeric":"float","num":"float","n":"float","decimal":"float","dec":"float","packed":"float",
    "integer":"integer","int":"integer","9":"integer",
    "date":"date","d":"date","datetime":"datetime","dt":"datetime",
    "binary":"string","b":"string",
}


class FixedWidthExtractor(ExtractorBase):

    def supported_formats(self): return [".txt",".dat",".pos",".fix"]

    def extract(self, file_path, table_name, layout_path=None, infer=False):
        file_path = Path(file_path)
        print(f"[EXTRACT] Arquivo posicional: {file_path.name}")

        if layout_path:
            layout_path = Path(layout_path)
        elif not infer:
            layout_path = _find_layout(table_name)
            if not layout_path:
                raise FileNotFoundError(
                    f"Leiaute nao encontrado para '{table_name}' em {_LAYOUTS_DIR}. "
                    "Use --layout <path> ou --infer."
                )

        if infer:
            columns, warnings = _infer_layout(file_path)
            manifest_status   = "DRAFT_EXPERIMENTAL"
            layout_source     = "inferencia experimental"
        else:
            columns, warnings = _load_layout(layout_path)
            manifest_status   = "DRAFT"
            layout_source     = layout_path.name

        for col in columns:
            col["regulatory_flags"] = self._detect_regulatory_flags(
                col["name"], col.get("sas_label",""))

        reg_tags = self._detect_table_regulatory_tags(columns)

        # Extrai layout section antes de limpar os campos temporarios
        layout_section = [
            {"field": c["name"], "start": c["_start"], "end": c["_end"], "dtype": c["type"]}
            for c in columns if "_start" in c
        ]
        for col in columns:
            col.pop("_start", None)
            col.pop("_end", None)

        manifest = {
            "table": table_name, "description": f"# TODO: descrever {table_name}",
            "owner": "# TODO: squad responsavel", "version": "1.0.0",
            "manifest_status": manifest_status, "validated_by": None, "validated_at": None,
            "source": {
                "system": "# TODO: sistema de origem", "format": "fixed_width",
                "encoding": "# TODO: utf-8 | latin-1 | cp1252",
                "os": "# TODO: unix | windows | mainframe",
                "update_frequency": "# TODO: daily | weekly | event_driven",
                "contact": "# TODO: email do time de origem",
                "layout_source": layout_source,
            },
            "regulatory": {
                "tags": reg_tags or ["# TODO: revisar tags"],
                "data_classification": "confidential" if any(
                    "LGPD_SENSITIVE" in c.get("regulatory_flags",[]) for c in columns
                ) else "internal",
                "retention_years": None,
            },
            "steward": {"name": "# TODO: nome", "email": "# TODO: email"},
            "business_context": f"# TODO: descrever {table_name}.",
            "tolerance": {"max_null_pct": 20, "allow_duplicates": False},
            "dependencies": [], "sample_queries": [],
            "schema": columns,
            "layout": layout_section,
            "_warnings": warnings or None,
        }

        print(f"[EXTRACT] {table_name}: {len(columns)} campos | {layout_source}"
              + (" | EXPERIMENTAL" if infer else ""))
        for w in warnings:
            print(f"   [WARN] {w}")
        return manifest


def _find_layout(table_name):
    for ext in (".txt",".csv",".xlsx"):
        p = _LAYOUTS_DIR / f"{table_name}_layout{ext}"
        if p.exists(): return p
    return None


def _load_layout(layout_path):
    ext = layout_path.suffix.lower()
    if ext == ".xlsx": return _load_xlsx_layout(layout_path)
    if ext == ".csv":  return _load_csv_layout(layout_path)
    return _load_txt_layout(layout_path)


def _load_txt_layout(path):
    columns, warnings = [], []
    with open(path, encoding="utf-8", errors="replace") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("#"): continue
            parts = line.split()
            if len(parts) < 3:
                warnings.append(f"Linha {lineno} ignorada: {line!r}")
                continue
            try:
                col = _make_column(parts[0], int(parts[1]), int(parts[2]),
                                   parts[3].lower() if len(parts)>3 else "char",
                                   " ".join(parts[4:]) if len(parts)>4 else None)
                columns.append(col)
            except (ValueError, IndexError):
                warnings.append(f"Linha {lineno} com formato invalido: {line!r}")
    cols, w2 = _validate_layout(columns)
    return cols, warnings + w2


def _load_csv_layout(path):
    df = pd.read_csv(path, dtype=str, encoding="utf-8", on_bad_lines="skip")
    df.columns = [c.strip().lower() for c in df.columns]
    col_map = {
        "campo":"name","field":"name","nome":"name",
        "inicio":"start","start":"start","ini":"start",
        "fim":"end","end":"end","fin":"end",
        "tipo":"type","type":"type","dtype":"type",
        "descricao":"desc","description":"desc","desc":"desc",
    }
    df = df.rename(columns={c: col_map.get(c,c) for c in df.columns})
    required = {"name","start","end"}
    if not required.issubset(set(df.columns)):
        raise ValueError(f"Layout CSV deve ter: {required}. Encontradas: {list(df.columns)}")
    columns, warnings = [], []
    for _, row in df.iterrows():
        try:
            col = _make_column(
                str(row["name"]).strip(), int(row["start"]), int(row["end"]),
                str(row.get("type","char")).strip().lower(),
                str(row["desc"]).strip() if "desc" in row and pd.notna(row.get("desc")) else None,
            )
            columns.append(col)
        except (ValueError, KeyError) as e:
            warnings.append(f"Linha ignorada: {e}")
    cols, w2 = _validate_layout(columns)
    return cols, warnings + w2


def _load_xlsx_layout(path):
    try:
        import openpyxl
        df = pd.read_excel(path, dtype=str)
    except ImportError:
        raise ImportError("openpyxl nao instalado. Execute: pip install openpyxl")
    tmp = tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w", encoding="utf-8")
    df.to_csv(tmp.name, index=False)
    tmp.close()
    try:
        return _load_csv_layout(Path(tmp.name))
    finally:
        os.unlink(tmp.name)


def _make_column(name, start, end, stype, desc):
    import re as _re
    def _norm(raw):
        n = raw.strip().replace(" ","_").replace("-","_")
        n = _re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", n)
        n = _re.sub(r"([a-z\d])([A-Z])", r"\1_\2", n)
        n = _re.sub(r"[^\w]","_",n).lower()
        return _re.sub(r"_+","_",n).strip("_")
    norm_name = _norm(name)
    return {
        "name": norm_name, "type": _FIXED_TYPE_MAP.get(stype,"string"),
        "nullable": True, "primary_key": False,
        "description": desc or f"# TODO: descrever {norm_name}",
        "sas_label": name, "regulatory_flags": [],
        "business_rules": ["Campo binario — verificar conversao"] if stype in ("binary","b") else [],
        "_start": start, "_end": end,
    }


def _validate_layout(columns):
    warnings = []
    if not columns: return columns, warnings
    sorted_cols = sorted(columns, key=lambda c: c.get("_start",0))
    prev_end = 0
    for col in sorted_cols:
        s, e = col.get("_start",0), col.get("_end",0)
        if e < s:
            warnings.append(f"'{col['name']}': end ({e}) < start ({s})")
        if s <= prev_end and prev_end > 0:
            warnings.append(f"Sobreposicao em '{col['name']}' (start={s} <= prev_end={prev_end})")
        if s > prev_end + 1 and prev_end > 0:
            warnings.append(f"Lacuna de {s-prev_end-1} byte(s) antes de '{col['name']}'")
        prev_end = e
    return sorted_cols, warnings


def _infer_layout(file_path, n_lines=200):
    warnings = ["MODO EXPERIMENTAL: layout inferido automaticamente. Revisao obrigatoria."]
    with open(file_path, encoding="latin-1", errors="replace") as f:
        lines = [f.readline().rstrip("\n") for _ in range(n_lines)]
    lines = [l for l in lines if l]
    if not lines:
        return [], warnings + ["Arquivo vazio."]
    line_len   = max(len(l) for l in lines)
    space_freq = [
        sum(1 for l in lines if pos < len(l) and l[pos] == " ") / len(lines)
        for pos in range(line_len)
    ]
    boundaries, in_space = [0], False
    for pos, freq in enumerate(space_freq):
        if freq >= 0.7 and not in_space:
            in_space = True; boundaries.append(pos)
        elif freq < 0.7 and in_space:
            in_space = False; boundaries.append(pos)
    boundaries.append(line_len)
    columns = []
    for i, (start, end) in enumerate(zip(boundaries[::2], boundaries[1::2])):
        if end - start < 2: continue
        columns.append(_make_column(f"campo_{i+1:03d}", start+1, end, "char", None))
    if len(columns) <= 1:
        warnings.append("Inferencia nao identificou campos. Use --layout.")
    return columns, warnings


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--file", required=True)
    p.add_argument("--table", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--layout", default=None)
    p.add_argument("--infer", action="store_true")
    p.add_argument("--enrich", action="store_true")
    p.add_argument("--overwrite", action="store_true")
    args = p.parse_args()
    fp = Path(args.file)
    if not fp.exists(): print(f"[ERROR] {fp}"); sys.exit(1)
    ext = FixedWidthExtractor()
    manifest = ext.extract(fp, args.table,
                           layout_path=Path(args.layout) if args.layout else None,
                           infer=args.infer)
    if args.enrich:
        from src.manifest.extractor_sas7bdat import _enrich_with_slm
        manifest = _enrich_with_slm(manifest, args.table)
    ManifestWriter().write(manifest, Path(args.output), overwrite=args.overwrite)

if __name__ == "__main__": main()
