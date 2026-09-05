"""src/storage/schema_utils.py — Tipagem governada pelo Manifest para Parquet."""
from __future__ import annotations
from pathlib import Path
from typing import Optional
import pandas as pd
import pyarrow as pa

_MANIFEST_TO_ARROW = {
    "string":"string","str":"string","text":"string",
    "integer":"int64","int":"int64","long":"int64",
    "float":"float64","double":"float64","decimal":"float64","numeric":"float64",
    "boolean":"bool_","bool":"bool_",
    "date":"date32","datetime":"timestamp_us","timestamp":"timestamp_us",
}
_BOOL_TRUE  = {"1","s","sim","true","yes","y","t","v","verdadeiro"}
_BOOL_FALSE = {"0","n","nao","não","false","no","f","falso"}
_DATE_FORMATS = ["%d/%m/%Y","%d-%m-%Y","%Y-%m-%d","%Y/%m/%d","%d/%m/%y","%d-%m-%y"]
CAST_FAIL_THRESHOLD = 0.05

def manifest_to_arrow_schema(contract, extra_columns=None):
    type_map = {
        "string":pa.string(),"str":pa.string(),"text":pa.string(),
        "integer":pa.int64(),"int":pa.int64(),"long":pa.int64(),
        "float":pa.float64(),"double":pa.float64(),"decimal":pa.float64(),"numeric":pa.float64(),
        "boolean":pa.bool_(),"bool":pa.bool_(),
        "date":pa.date32(),"datetime":pa.timestamp("us"),"timestamp":pa.timestamp("us"),
    }
    fields = []
    for col in contract.schema:
        t = type_map.get((col.type or "string").lower().strip(), pa.string())
        fields.append(pa.field(col.name, t, nullable=col.nullable if col.nullable is not None else True))
    for c in (extra_columns or []):
        fields.append(pa.field(c, pa.string(), nullable=True))
    return pa.schema(fields)

def apply_manifest_schema(df, contract, source_status="manifest_validated", report=None):
    df = df.copy()
    warnings = []
    contract_cols = {c.name.lower(): c for c in contract.schema}
    for col_def in contract.schema:
        if col_def.name.lower() not in {c.lower() for c in df.columns}:
            if not (col_def.nullable if col_def.nullable is not None else True):
                warnings.append("MISSING_REQUIRED: '{}' nao encontrada no dado.".format(col_def.name))
                if report is not None:
                    report[col_def.name] = {"declared": (col_def.type or "string"),
                                            "cast_ok": False, "fail_pct":100.0, "missing": True}
    for df_col in df.columns:
        col_def = contract_cols.get(df_col.lower())
        if col_def is None:
            warnings.append("EXTRA_COLUMN: '{}' nao declarada no Manifest, mantida como string.".format(df_col))
            continue
        mt = (col_def.type or "string").lower().strip()
        fmt = _extract_date_format(col_def)
        stats = {"declared": mt, "cast_ok": True, "fail_pct": 0.0, "missing": False}
        result, cw = _cast_column(df[df_col], df_col, mt, fmt, stats)
        df[df_col] = result
        warnings.extend(cw)
        if report is not None:
            report[col_def.name] = stats
    return df, warnings

def build_parquet_metadata(contract, warnings):
    import json
    from datetime import datetime
    is_val = getattr(contract, "manifest_status", "DRAFT") == "VALIDATED"
    meta = {
        "nimbus.schema_source"    : "manifest_validated" if is_val else "manifest_draft",
        "nimbus.manifest_version" : getattr(contract, "version", "unknown"),
        "nimbus.table"            : getattr(contract, "table", "unknown"),
        "nimbus.generated_at"     : datetime.now().isoformat(),
        "nimbus.warnings_count"   : str(len(warnings)),
    }
    if warnings:
        meta["nimbus.warnings"] = json.dumps(warnings[:10])
    return {k.encode(): v.encode() for k, v in meta.items()}

def _cast_column(series, col_name, manifest_type, date_format, stats=None):
    warnings = []
    if manifest_type == "string":
        return series.astype(object), warnings
    if manifest_type in ("integer","int","long"):
        return _cast_numeric(series, col_name, warnings, integer=True, stats=stats)
    if manifest_type in ("float","double","decimal","numeric"):
        return _cast_numeric(series, col_name, warnings, integer=False, stats=stats)
    if manifest_type in ("boolean","bool"):
        return _cast_boolean(series, col_name, warnings, stats=stats)
    if manifest_type == "date":
        return _cast_date(series, col_name, date_format, warnings, as_datetime=False, stats=stats)
    if manifest_type in ("datetime","timestamp"):
        return _cast_date(series, col_name, date_format, warnings, as_datetime=True, stats=stats)
    warnings.append("UNKNOWN_TYPE: tipo '{}' em '{}', mantido como string.".format(manifest_type, col_name))
    _mark_fail(stats, 100.0)
    return series, warnings

def _mark_fail(stats, fail_pct):
    if stats is not None:
        stats["cast_ok"] = False
        stats["fail_pct"] = round(fail_pct, 2)

def _cast_numeric(series, col_name, warnings, integer):
    non_null = series.dropna().replace("", pd.NA).dropna()
    if len(non_null) == 0:
        return series, warnings
    converted = pd.to_numeric(non_null, errors="coerce")
    fail_rate = converted.isna().sum() / len(non_null)
    if fail_rate > CAST_FAIL_THRESHOLD:
        warnings.append("CAST_FAIL: '{}' como {} — {:.1f}% falhou. Mantida como string.".format(
            col_name, "integer" if integer else "float", fail_rate * 100))
        return series.astype(object), warnings
    result = pd.to_numeric(series, errors="coerce")
    if integer:
        result = result.astype("Int64")
    return result, warnings

def _cast_boolean(series, col_name, warnings):
    def _to_bool(val):
        if pd.isna(val) or val == "": return None
        v = str(val).strip().lower()
        if v in _BOOL_TRUE:  return True
        if v in _BOOL_FALSE: return False
        return None
    non_null = series.dropna().replace("", pd.NA).dropna()
    if len(non_null) == 0:
        return series, warnings
    mapped = non_null.apply(_to_bool)
    fail_rate = mapped.isna().sum() / len(non_null)
    if fail_rate > CAST_FAIL_THRESHOLD:
        warnings.append("CAST_FAIL: '{}' como boolean — {:.1f}% fora do dominio. Mantida como string.".format(
            col_name, fail_rate * 100))
        return series.astype(object), warnings
    result = series.apply(_to_bool)
    try:
        return result.astype(pd.BooleanDtype()), warnings
    except Exception:
        return result, warnings

def _cast_date(series, col_name, date_format, warnings, as_datetime):
    non_null = series.dropna().replace("", pd.NA).dropna()
    if len(non_null) == 0:
        return series, warnings
    formats_to_try = [date_format] if date_format else []
    formats_to_try += [f for f in _DATE_FORMATS if f != date_format]
    for fmt in formats_to_try:
        try:
            converted = pd.to_datetime(non_null, format=fmt, errors="coerce")
            if converted.isna().sum() / len(non_null) <= CAST_FAIL_THRESHOLD:
                result = pd.to_datetime(series, format=fmt, errors="coerce")
                if fmt != date_format and date_format:
                    warnings.append("DATE_FORMAT_FALLBACK: '{}' — usando '{}' em vez de '{}'.".format(
                        col_name, fmt, date_format))
                return (result.dt.date if not as_datetime else result), warnings
        except (ValueError, TypeError):
            continue
    try:
        converted = pd.to_datetime(non_null, errors="coerce")
        if converted.isna().sum() / len(non_null) <= CAST_FAIL_THRESHOLD:
            result = pd.to_datetime(series, errors="coerce")
            return (result.dt.date if not as_datetime else result), warnings
    except Exception:
        pass
    warnings.append("CAST_FAIL: '{}' como {} — nenhum formato funcionou. Mantida como string.".format(
        col_name, "datetime" if as_datetime else "date"))
    return series.astype(object), warnings

def _extract_date_format(col_def):
    for rule in (col_def.business_rules or []):
        for fmt in _DATE_FORMATS:
            if fmt in rule:
                return fmt
    return None
