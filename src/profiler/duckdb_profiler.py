"""
Profiler estatístico — DuckDB preferencial, fallback para Pandas.

Em produção (Databricks), esta lógica migra para funções PySpark nativas.
"""

import time
from pathlib import Path
from typing import Any

import pandas as pd

try:
    import duckdb
    _HAS_DUCKDB = True
except ImportError:
    _HAS_DUCKDB = False


def _safe(val: Any) -> Any:
    if val is None:
        return None
    if hasattr(val, "item"):
        return val.item()
    try:
        import math
        if math.isnan(float(val)):
            return None
    except (TypeError, ValueError):
        pass
    return val


def _profile_with_pandas(csv_path: Path) -> dict:
    """Fallback: profiling via pandas quando DuckDB não está disponível."""
    df = pd.read_csv(csv_path, low_memory=False, dtype=str)
    total_rows = len(df)
    columns_payload = {}

    for col in df.columns:
        series = df[col]
        null_count = series.isna().sum() + (series == "").sum()
        stats: dict[str, Any] = {
            "dtype"       : "VARCHAR",
            "null_count"  : int(null_count),
            "null_pct"    : round(null_count / total_rows * 100, 2) if total_rows else 0,
            "unique_count": int(series.nunique()),
        }
        non_null = series.dropna()
        try:
            numeric = pd.to_numeric(non_null, errors="raise")
            stats["min"]  = _safe(round(float(numeric.min()), 4))
            stats["max"]  = _safe(round(float(numeric.max()), 4))
            stats["mean"] = _safe(round(float(numeric.mean()), 4))
        except (ValueError, TypeError):
            pass

        top = series.value_counts().head(5)
        stats["top_values"] = [{"value": str(k), "count": int(v)} for k, v in top.items()]
        columns_payload[col] = stats

    return {"columns": columns_payload, "rows": total_rows}


def profile(csv_path: Path) -> dict:
    t0    = time.perf_counter()
    table = csv_path.stem

    if _HAS_DUCKDB:
        import duckdb
        con = duckdb.connect()
        con.execute(f"CREATE VIEW src AS SELECT * FROM read_csv_auto('{csv_path}', ALL_VARCHAR=TRUE)")
        total_rows = con.execute("SELECT COUNT(*) FROM src").fetchone()[0]
        col_info   = con.execute("DESCRIBE src").fetchall()
        columns_payload = {}
        for col_name, raw_dtype, *_ in col_info:
            stats: dict[str, Any] = {"dtype": raw_dtype}
            null_count = con.execute(
                f"SELECT COUNT(*) FROM src WHERE \"{col_name}\" IS NULL OR TRIM(\"{col_name}\") = ''"
            ).fetchone()[0]
            stats["null_count"] = null_count
            stats["null_pct"]   = round(null_count / total_rows * 100, 2) if total_rows else 0
            stats["unique_count"] = con.execute(
                f"SELECT COUNT(DISTINCT \"{col_name}\") FROM src"
            ).fetchone()[0]
            try:
                nr = con.execute(
                    f'SELECT MIN(TRY_CAST("{col_name}" AS DOUBLE)), MAX(TRY_CAST("{col_name}" AS DOUBLE)), '
                    f'AVG(TRY_CAST("{col_name}" AS DOUBLE)) FROM src '
                    f'WHERE TRY_CAST("{col_name}" AS DOUBLE) IS NOT NULL'
                ).fetchone()
                if nr and nr[0] is not None:
                    stats["min"]  = _safe(round(nr[0], 4))
                    stats["max"]  = _safe(round(nr[1], 4))
                    stats["mean"] = _safe(round(nr[2], 4))
            except Exception:
                pass
            top = con.execute(
                f'SELECT "{col_name}", COUNT(*) FROM src WHERE "{col_name}" IS NOT NULL '
                f'GROUP BY "{col_name}" ORDER BY 2 DESC LIMIT 5'
            ).fetchall()
            stats["top_values"] = [{"value": str(r[0]), "count": r[1]} for r in top]
            columns_payload[col_name] = stats
        con.close()
        result = {"columns": columns_payload, "rows": total_rows}
        engine = "DuckDB"
    else:
        result = _profile_with_pandas(csv_path)
        engine = "Pandas"

    elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)
    result.update({"table": table, "profiling_ms": elapsed_ms})
    print(
        f"   📊  [{table}] Profiling via {engine} — "
        f"{elapsed_ms} ms | {result['rows']} linhas × {len(result['columns'])} colunas"
    )
    return result
