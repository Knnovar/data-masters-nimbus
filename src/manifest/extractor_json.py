"""
src/manifest/extractor_json.py — Extrator para arquivos JSON.
Normaliza estruturas aninhadas em schema tabular via pandas.json_normalize.
"""

import argparse, json, sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.manifest.extractor_base import ExtractorBase
from src.manifest.extractor_csv  import CSVExtractor
from src.manifest.manifest_writer import ManifestWriter

N_SAMPLE_DEFAULT = 500


class JSONExtractor(ExtractorBase):

    def supported_formats(self): return [".json",".jsonl",".ndjson"]

    def extract(self, file_path, table_name, root_key=None, max_level=2, n_sample=N_SAMPLE_DEFAULT):
        file_path = Path(file_path)
        print(f"[EXTRACT] Analisando {file_path.name} (max_level={max_level})...")

        ext = file_path.suffix.lower()
        if ext in (".jsonl",".ndjson"):
            records, structure = _load_jsonlines(file_path, n_sample)
            detected_root_key  = None
        else:
            records, structure, detected_root_key = _load_json(file_path, root_key, n_sample)
            root_key = detected_root_key  # usa o detectado se nao foi fornecido

        if not records:
            raise ValueError(f"Nenhum registro encontrado em {file_path.name}")

        try:
            df = pd.json_normalize(records, max_level=max_level, sep="__")
        except Exception as e:
            raise RuntimeError(f"Erro ao normalizar JSON: {e}")

        # Normaliza preservando __ como separador de nivel
        import re as _re
        def _norm_part(s):
            s = _re.sub(r"[^\w]","_",s.strip().lower())
            return _re.sub(r"_+","_",s).strip("_")
        def _norm_json_col(col):
            return "__".join(_norm_part(p) for p in col.split("__"))

        # Renomeia colunas para uso interno mas mantem mapeamento
        col_map  = {c: _norm_json_col(c) for c in df.columns}
        df       = df.rename(columns=col_map)

        # Constroi colunas diretamente sem dupla normalizacao
        csv_ext  = CSVExtractor()
        columns  = []
        for col_name in df.columns:
            series = df[col_name]

            # Detecta se a coluna contém dicts/listas (campo colapsado)
            try:
                has_complex = series.dropna().apply(
                    lambda x: isinstance(x, (dict, list))
                ).any()
            except Exception:
                has_complex = False

            if has_complex:
                series   = series.apply(lambda x: str(x) if isinstance(x, (dict, list)) else x)
                inferred = {"type": "string"}
                nullable = True
                is_pk    = False
                flags    = self._detect_regulatory_flags(col_name, col_name)
                rules    = [
                    f"Campo colapsado de estrutura aninhada (nivel > {max_level}). "
                    "Considere aumentar max_level ou normalizar a origem."
                ]
            else:
                inferred = csv_ext._infer_type(series)
                nullable = bool(series.isna().any() or (series == "").any())
                is_pk    = csv_ext._is_pk_candidate(col_name, series)
                flags    = self._detect_regulatory_flags(col_name, col_name)
                rules    = csv_ext._infer_business_rules(col_name, series, inferred)
                if inferred.get("format"):
                    rules.append(f"Formato detectado: {inferred['format']}")
                if inferred.get("mixed"):
                    rules.append("# TODO: coluna com valores mistos")

            columns.append({
                "name": col_name, "type": inferred["type"],
                "nullable": nullable, "primary_key": is_pk,
                "description": f"# TODO: descrever {col_name}",
                "regulatory_flags": flags, "business_rules": rules,
            })
        reg_tags  = self._detect_table_regulatory_tags(columns)
        return {
            "table": table_name, "description": f"# TODO: descrever {table_name}",
            "owner": "# TODO: squad responsavel", "version": "1.0.0",
            "manifest_status": "DRAFT", "validated_by": None, "validated_at": None,
            "source": {
                "system": "# TODO: sistema de origem", "format": "json",
                "encoding": "utf-8", "os": "# TODO: unix | windows",
                "update_frequency": "# TODO: daily | weekly | event_driven",
                "contact": "# TODO: email do time de origem",
                "json_root_key": root_key, "json_structure": structure,
                "json_max_level": max_level,
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
            "dependencies": [], "sample_queries": [], "schema": columns,
        }


def _load_json(file_path, root_key, n_sample):
    with open(file_path, encoding="utf-8", errors="replace") as f:
        data = json.load(f)
    detected_key = root_key
    if root_key is None and isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, list): detected_key = k; break
    if detected_key and isinstance(data, dict):
        data = data.get(detected_key, data)
    if isinstance(data, list):   return data[:n_sample], "list", detected_key
    if isinstance(data, dict):   return [data], "object", detected_key
    raise ValueError(f"Estrutura JSON nao suportada: {type(data).__name__}")


def _load_jsonlines(file_path, n_sample):
    records = []
    with open(file_path, encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f):
            if i >= n_sample: break
            line = line.strip()
            if line:
                try: records.append(json.loads(line))
                except json.JSONDecodeError: continue
    return records, "jsonlines"


def _find_collapsed(records, max_level):
    collapsed = set()
    def _walk(obj, level, path):
        if level > max_level and isinstance(obj, dict):
            key = "__".join(str(p) for p in path[:max_level+1]).lower()
            collapsed.add(key)
            return   # nao desce mais
        if isinstance(obj, dict):
            for k, v in obj.items():
                _walk(v, level+1, path+[str(k)])
        elif isinstance(obj, list) and obj:
            _walk(obj[0], level+1, path)
    for r in records[:10]:
        if isinstance(r, dict):
            _walk(r, 0, [])
    return collapsed


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--file",      required=True)
    p.add_argument("--table",     required=True)
    p.add_argument("--output",    required=True)
    p.add_argument("--root-key",  default=None, dest="root_key")
    p.add_argument("--max-level", default=2, dest="max_level", type=int)
    p.add_argument("--sample",    default=N_SAMPLE_DEFAULT, type=int)
    p.add_argument("--enrich",    action="store_true")
    p.add_argument("--overwrite", action="store_true")
    args = p.parse_args()
    fp = Path(args.file)
    if not fp.exists(): print(f"[ERROR] {fp}"); sys.exit(1)
    ext      = JSONExtractor()
    manifest = ext.extract(fp, args.table, root_key=args.root_key,
                           max_level=args.max_level, n_sample=args.sample)
    if args.enrich:
        from src.manifest.extractor_sas7bdat import _enrich_with_slm
        manifest = _enrich_with_slm(manifest, args.table)
    ManifestWriter().write(manifest, Path(args.output), overwrite=args.overwrite)

if __name__ == "__main__": main()
