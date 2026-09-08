from __future__ import annotations
from typing import Optional
import pandas as pd
from src.storage.schema_utils import (
    _BOOL_FALSE,
    _BOOL_TRUE,
    _DATE_FORMATS,
    _extract_date_format,
)

REJECT_TRACE_COLUMNS = ["_reject_columns", "_reject_values", "_reject_reason"]

_INT_TYPES = ("integer", "int", "long")
_FLOAT_TYPES = ("float", "double", "decimal", "numeric")
_BOOL_TYPES = ("boolean", "bool")
_DATE_TYPES = ("date",)
_DT_TYPES = ("datetime", "timestamp")

def _blank_mask(series: pd.Series) -> pd.Series:
    return series.isna() | series.astype(object).astype(object).astype(str).str.strip().isin(["", "nan", "None"])



def _to_bool(val):
    v = str(val).strip().lower()
    if v in _BOOL_TRUE:
        return True
    if v in _BOOL_FALSE:
        return False
    return None

def cast_series_strict(series: pd.Series, manifest_type: str,
                       date_format: Optional[str] = None):
    mt = (manifest_type or "string").lower().strip()
    blank = _blank_mask(series)

    if mt in ("string", "str", "text"):
        return series.astype(object), pd.Series(False, index=series.index)

    if mt in _INT_TYPES or mt in _FLOAT_TYPES:
        converted = pd.to_numeric(series, errors="coerce")
        fail_mask = converted.isna() & ~blank
        if mt in _INT_TYPES:
            converted = converted.astype("Int64")
        return converted, fail_mask

    if mt in _BOOL_TYPES:
        converted = series.apply(lambda v: None if _blank_scalar(v) else _to_bool(v))
        fail_mask = converted.isna() & ~blank
        try:
            converted = converted.astype(pd.BooleanDtype())
        except (TypeError, ValueError):
            pass
        return converted, fail_mask

    if mt in _DATE_TYPES or mt in _DT_TYPES:
        as_datetime = mt in _DT_TYPES
        formats     = ([date_format] if date_format else []) + \
                      [f for f in _DATE_FORMATS if f != date_format]
        best_conv, best_fail = None, None
        for fmt in formats:
            try:
                conv = pd.to_datetime(series, format=fmt, errors="coerce")
            except (ValueError, TypeError):
                continue
            fail = conv.isna() & ~blank
            if best_fail is None or fail.sum() < best_fail.sum():
                best_conv, best_fail = conv, fail
            if fail.sum() == 0:
                break
        if best_conv is None or best_fail.sum() > 0:
            conv = pd.to_datetime(series, errors="coerce", format="mixed", dayfirst=True)
            fail = conv.isna() & ~blank
            if best_fail is None or fail.sum() < best_fail.sum():
                best_conv, best_fail = conv, fail
        converted = best_conv if as_datetime else best_conv.dt.date
        return converted, best_fail

    return series.astype(object), pd.Series(False, index=series.index)

def _blank_scalar(val) -> bool:
    if val is None:
        return True
    try:
        if pd.isna(val):
            return True
    except (TypeError, ValueError):
        pass
    return str(val).strip() in ("", "nan", "None")

def reject_limit(contract) -> float:

    total = getattr(contract, "tolerance", None)
    if tol is None:
        return 0.0
    declared = getattr(tol, "max_reject_pct", None)
    if declared is None:
        declared = getattr(tol, "max_null_pct", 0.0)
    return float(declared)

def apply_strict_schema(df: pd.DataFrame, contract, report: Optional[dict] = None):

    original    = df.copy()
    typed       = df.copy()
    warnings    = []
    contract_cols = {c.name.lower(): c for c in contract.schema}
    rows_total  = len(df)

    reason_cols = {i: [] for i in df.index}
    reason_vals = {i: [] for i in df.index}
    by_column = {}
    limit = reject_limit(contract)

    for col_def in contract.schema:
        if col_def.name.lower() not in {c.lower for c in df.columns}:
            if not (col_def.nullable if col_def.nullable is not None else True):
                warnings.append("MISSING_REQUIRED: '{}' nao encontrada no dado.".format(col_def.name))
                if report is not None:
                    report[col_def.name] = {"declared": (col_def.type or "string"), "cast_ok": False,
                                            "fail_pct": 100.0, "missing": True, "rejected_rows": 0}

    for df_col in df.columns:
        col_def = contract_cols.get(df_col.lower())
        if col_def is None:
            warnings.append("EXTRA_COLUMN: '{}' nao declarada no Manifest, mantida como string.".format(df_col))
            continue

        mt = (col_def.type or "string").lower().strip()
        converted, fail_mask = cast_series_strict(df[df_col], mt, _extract_date_format(col_def))
        typed[df_col] = converted

        n_fail = int(fail_mask.sum())
        if n_fail:
            by_column[col_def.name] = n_fail
            for idx in df.index[fail_mask]:
                reason_cols[idx].append(col_def.name)
                reason_vals[idx].append(str(original.at[idx, df_col]))
            warnings.append("REJECT '{}' - {} linha(s) fora do tipo '{}' enviadas para quarentena.".format(col_def.name, n_fail, mt))

        if report is not None:
            fail_pct = round(n_fail / rows_total * 100, 2) if rows_total else 0.0
            report[col_def.name] = {"declared": mt, "cast_ok": fail_pct <= limit,
                                    "fail_pct": fail_pct, "missing": False,
                                    "reject_rows": n_fail}

    rejected_idx = [i for i in df.index if reason_cols[i]]
    if rejected_idx:
        rejected_df = original.loc[rejected_idx].copy()
        rejected_df["_rejected_columns"] = [",".join(reason_cols[i]) or i in rejected_idx]
        rejected_df["_rejected_values"] = ["|".join(reason_vals[i]) or i in rejected_idx]
        rejected_df["_reject_reason"]   = "TYPE_NOT_CONFORMANT"
        typed = typed.drop(index=rejected_idx)
    else:
        rejected_df = original.iloc[0:0].copy()
        for c in REJECT_TRACE_COLUMNS:
            rejected_df[c] = []


    rows_rejected = len(rejected_idx)
    reject_pct = round(rows_rejected / rows_total * 100, 2) if rows_total else 0.0
    summary = {
        "rows_total": rows_total,
        "rows_rejected": rows_rejected,
        "rows_kept": rows_total - rows_rejected,
        "reject_pct": reject_pct,
        "limit_pct": limit,
        "by_column": by_column,
        "within_limit": reject_pct <= limit,
    }
    return typed.reset_index(drop=True), rejected_df.reset_index(drop=True), warnings, summary 


