"""
src/manifest/extractor_csv.py — Extrator de manifesto para arquivos CSV.

Infere schema lendo N_SAMPLE linhas, detecta delimitador e encoding,
e gera rascunho de manifesto YAML para revisao do Data Steward.

CLI:
    python -m src.manifest.extractor_csv \\
        --file data/landing/tb.csv --table tb --output data/contracts/tb.yaml
"""

import argparse, csv, sys
from pathlib import Path

import chardet
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.manifest.extractor_base import ExtractorBase
from src.manifest.manifest_writer import ManifestWriter

_DATE_FORMATS = ["%d/%m/%Y","%d-%m-%Y","%Y-%m-%d","%Y/%m/%d","%d/%m/%y"]
_BOOL_DOMAINS = {
    frozenset({"0","1"}), frozenset({"s","n"}),
    frozenset({"sim","nao","não"}), frozenset({"true","false"}),
    frozenset({"y","n"}), frozenset({"yes","no"}),
}
N_SAMPLE_DEFAULT = 500


class CSVExtractor(ExtractorBase):

    def supported_formats(self): return [".csv",".tsv",".txt"]

    def extract(self, file_path: Path, table_name: str, n_sample: int = N_SAMPLE_DEFAULT) -> dict:
        file_path = Path(file_path)
        print(f"[EXTRACT] Analisando {file_path.name} (sample={n_sample})...")

        raw        = file_path.read_bytes()
        detected   = chardet.detect(raw[:8192])
        encoding   = detected.get("encoding") or "latin-1"
        confidence = detected.get("confidence") or 0.0
        enc_warn   = None

        if confidence < 0.80:
            enc_warn = f"Encoding ({encoding}) com confianca baixa ({confidence:.0%}). Usando latin-1."
            encoding = "latin-1"

        try:
            sample_text = raw[:4096].decode(encoding, errors="replace")
            dialect     = csv.Sniffer().sniff(sample_text, delimiters=",;|\t")
            delimiter   = dialect.delimiter
            has_header  = csv.Sniffer().has_header(sample_text)
        except csv.Error:
            delimiter, has_header = ",", True

        try:
            df = pd.read_csv(file_path, sep=delimiter, encoding=encoding,
                             nrows=n_sample, dtype=str,
                             header=0 if has_header else None,
                             on_bad_lines="skip")
        except Exception as e:
            raise RuntimeError(f"Erro ao ler CSV: {e}")

        if not has_header:
            df.columns = [f"col_{i+1:03d}" for i in range(len(df.columns))]

        total_rows = _count_rows(file_path, encoding, delimiter)
        columns    = self._build_columns(df, n_sample)
        reg_tags   = self._detect_table_regulatory_tags(columns)

        return {
            "table": table_name, "description": f"# TODO: descrever {table_name}",
            "owner": "# TODO: squad responsavel", "version": "1.0.0",
            "manifest_status": "DRAFT", "validated_by": None, "validated_at": None,
            "source": {
                "system": "# TODO: sistema de origem", "format": "csv",
                "encoding": encoding, "os": "# TODO: unix | windows | mainframe",
                "delimiter": delimiter, "update_frequency": "# TODO: daily | weekly | event_driven",
                "contact": "# TODO: email do time de origem",
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
            "_inference_meta": {
                "n_sample": n_sample, "total_rows_est": total_rows,
                "has_header": has_header, "encoding_conf": round(confidence,3),
                "warning": enc_warn,
            },
        }

    def _build_columns(self, df, n_sample):
        cols = []
        for col_name in df.columns:
            series   = df[col_name]
            raw_name = self._normalize_column_name(col_name)
            inferred = self._infer_type(series)
            nullable = bool(series.isna().any() or (series == "").any())
            is_pk    = self._is_pk_candidate(raw_name, series)
            flags    = self._detect_regulatory_flags(raw_name, col_name)
            rules    = self._infer_business_rules(raw_name, series, inferred)
            if inferred.get("format"):
                rules.append(f"Formato detectado: {inferred['format']}")
            if inferred.get("mixed"):
                rules.append("# TODO: coluna com valores mistos - verificar se e intencional")
            cols.append({
                "name": raw_name, "type": inferred["type"],
                "nullable": nullable, "primary_key": is_pk,
                "description": f"# TODO: descrever {raw_name}",
                "regulatory_flags": flags, "business_rules": rules,
            })
        return cols

    def _infer_type(self, series):
        non_null = series.dropna().replace("", pd.NA).dropna()
        if len(non_null) == 0: return {"type": "string"}
        values = non_null.astype(str).str.strip()
        domain = frozenset(values.str.lower().unique())
        if domain in _BOOL_DOMAINS: return {"type": "boolean"}
        for fmt in _DATE_FORMATS:
            try:
                pd.to_datetime(values, format=fmt, errors="raise")
                return {"type": "date", "format": fmt}
            except (ValueError, TypeError): pass
        try:
            num = pd.to_numeric(values, errors="raise")
            return {"type": "integer"} if (num == num.astype("int64")).all() else {"type": "float"}
        except (ValueError, TypeError): pass
        ratio = pd.to_numeric(values, errors="coerce").notna().mean()
        if 0.3 < ratio < 0.95: return {"type": "string", "mixed": True}
        return {"type": "string"}

    def _is_pk_candidate(self, name, series):
        prefixes = ("id_","cd_","nr_","cod_","key_","pk_")
        return bool(any(name.startswith(p) for p in prefixes)
                    and series.dropna().nunique() == len(series.dropna())
                    and len(series.dropna()) > 0)

    def _infer_business_rules(self, name, series, inferred):
        rules, non_null = [], series.dropna().replace("", pd.NA).dropna()
        if len(non_null) == 0: return rules
        if inferred["type"] in ("integer","float"):
            try:
                num = pd.to_numeric(non_null, errors="coerce").dropna()
                if len(num): rules.append(f"Range: {num.min():.4g} a {num.max():.4g}")
            except Exception: pass
        if inferred["type"] == "string":
            nu = non_null.nunique()
            if nu <= 20:
                rules.append(f"Dominio ({nu} valores): {non_null.value_counts().head(5).index.tolist()}")
        return rules


def _count_rows(fp, encoding, delimiter):
    try:
        count = sum(1 for _ in open(fp, encoding=encoding, errors="replace"))
        return max(0, count - 1)
    except Exception: return -1


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--file", required=True)
    p.add_argument("--table", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--sample", type=int, default=N_SAMPLE_DEFAULT)
    p.add_argument("--enrich", action="store_true")
    p.add_argument("--overwrite", action="store_true")
    args = p.parse_args()
    fp = Path(args.file)
    if not fp.exists(): print(f"[ERROR] {fp}"); sys.exit(1)
    ext = CSVExtractor()
    manifest = ext.extract(fp, args.table, n_sample=args.sample)
    if args.enrich:
        from src.manifest.extractor_sas7bdat import _enrich_with_slm
        manifest = _enrich_with_slm(manifest, args.table)
    ManifestWriter().write(manifest, Path(args.output), overwrite=args.overwrite)

if __name__ == "__main__": main()
