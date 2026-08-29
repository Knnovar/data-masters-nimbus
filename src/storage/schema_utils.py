"""
src/storage/schema_utils.py — Utilitários de schema para tipagem governada pelo Manifest.

Responsabilidade única: converter tipos declarados no Manifest para PyArrow
e aplicar o schema ao DataFrame antes da serialização Parquet.

Não sabe nada de storage, pipeline ou orquestração.

Fluxo esperado:
    contract = DataContract(...)           # contrato já carregado
    schema   = manifest_to_arrow_schema(contract)
    df_typed = apply_manifest_schema(df_raw, contract)
    df_typed.to_parquet(path, schema=schema)
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd
import pyarrow as pa

# ─────────────────────────────────────────────────────────────────────────────
# Constantes
# ─────────────────────────────────────────────────────────────────────────────

# Mapeamento de tipos semânticos do Manifest para tipos físicos PyArrow
_MANIFEST_TO_ARROW: dict[str, pa.DataType] = {
    "string"   : pa.string(),
    "str"      : pa.string(),
    "text"     : pa.string(),
    "integer"  : pa.int64(),
    "int"      : pa.int64(),
    "long"     : pa.int64(),
    "float"    : pa.float64(),
    "double"   : pa.float64(),
    "decimal"  : pa.float64(),
    "numeric"  : pa.float64(),
    "boolean"  : pa.bool_(),
    "bool"     : pa.bool_(),
    "date"     : pa.date32(),
    "datetime" : pa.timestamp("us"),
    "timestamp": pa.timestamp("us"),
}

# Domínios reconhecidos como booleano (case-insensitive)
_BOOL_TRUE  = {"1", "s", "sim", "true",  "yes", "y", "t", "v", "verdadeiro"}
_BOOL_FALSE = {"0", "n", "nao", "não", "false", "no",  "f", "falso"}

# Formatos de data tentados em sequência quando o formato não está declarado
_DATE_FORMATS = [
    "%d/%m/%Y", "%d-%m-%Y",
    "%Y-%m-%d", "%Y/%m/%d",
    "%d/%m/%y", "%d-%m-%y",
]

# Threshold de falha de cast — se mais que CAST_FAIL_THRESHOLD dos valores
# não puderem ser convertidos, mantém como string e emite WARNING
CAST_FAIL_THRESHOLD = 0.05   # 5%


# ─────────────────────────────────────────────────────────────────────────────
# API pública
# ─────────────────────────────────────────────────────────────────────────────

def manifest_to_arrow_schema(contract, extra_columns: Optional[list] = None) -> pa.Schema:
    """
    Converte os tipos declarados no Manifest em um schema PyArrow.

    Args:
        contract       : DataContract carregado do YAML.
        extra_columns  : Colunas presentes no dado mas ausentes no Manifest
                         (cenário NON_BREAKING). Entram como pa.string().

    Returns:
        pa.Schema com os campos na ordem do Manifest, seguidos de extra_columns.
    """
    fields = []

    for col in contract.schema:
        manifest_type = (col.type or "string").lower().strip()
        arrow_type    = _MANIFEST_TO_ARROW.get(manifest_type, pa.string())
        nullable      = col.nullable if col.nullable is not None else True
        fields.append(pa.field(col.name, arrow_type, nullable=nullable))

    # Colunas extras (NON_BREAKING) entram como string não-governada
    for col_name in (extra_columns or []):
        fields.append(pa.field(col_name, pa.string(), nullable=True))

    return pa.schema(fields)


def apply_manifest_schema(
    df: pd.DataFrame,
    contract,
    source_status: str = "manifest_validated",
) -> tuple[pd.DataFrame, list[str]]:
    """
    Aplica os tipos do Manifest ao DataFrame, coluna por coluna.

    O processo é não-destrutivo: se o cast falhar em mais de CAST_FAIL_THRESHOLD
    dos valores, a coluna é mantida como string e o evento é registrado nos warnings.

    Args:
        df            : DataFrame com colunas em dtype=str (Bronze bruto).
        contract      : DataContract carregado do YAML.
        source_status : Status do manifest ('manifest_validated' | 'manifest_draft').

    Returns:
        Tupla (df_typed, warnings) onde:
          df_typed  = DataFrame com tipos aplicados
          warnings  = Lista de strings descrevendo os eventos de cast
    """
    df      = df.copy()
    warnings: list[str] = []

    # Mapeia colunas do contrato pelo nome (case-insensitive)
    contract_cols = {c.name.lower(): c for c in contract.schema}
    df_cols_lower = {c.lower(): c for c in df.columns}

    # --- Colunas no Manifest mas ausentes no dado ---
    for col_name, col_def in contract_cols.items():
        if col_name not in df_cols_lower:
            if not col_def.nullable:
                warnings.append(
                    "MISSING_REQUIRED: coluna '{}' declarada como not-nullable "
                    "nao encontrada no dado.".format(col_name)
                )

    # --- Aplica cast em cada coluna do DataFrame ---
    for df_col in df.columns:
        df_col_lower = df_col.lower()
        col_def      = contract_cols.get(df_col_lower)

        if col_def is None:
            # Coluna extra (NON_BREAKING) — mantém como string
            warnings.append(
                "EXTRA_COLUMN: '{}' nao declarada no Manifest, "
                "mantida como string.".format(df_col)
            )
            continue

        manifest_type = (col_def.type or "string").lower().strip()
        date_fmt      = _extract_date_format(col_def)

        result, cast_warnings = _cast_column(
            df[df_col], df_col, manifest_type, date_fmt
        )
        df[df_col] = result
        warnings.extend(cast_warnings)

    return df, warnings


def build_parquet_metadata(contract, warnings: list[str]) -> dict[bytes, bytes]:
    """
    Constrói o dicionário de metadata customizada para embutir no Parquet.

    Esse metadata fica armazenado no footer do arquivo e é acessível via
    pyarrow.parquet.read_metadata() sem precisar carregar os dados.

    Args:
        contract : DataContract.
        warnings : Lista de warnings gerados pelo apply_manifest_schema.

    Returns:
        Dict com chaves e valores em bytes (exigência do PyArrow).
    """
    import json
    from datetime import datetime

    is_validated = getattr(contract, "manifest_status", "DRAFT") == "VALIDATED"

    meta = {
        "nimbus.schema_source"    : "manifest_validated" if is_validated else "manifest_draft",
        "nimbus.manifest_version" : getattr(contract, "version", "unknown"),
        "nimbus.table"            : getattr(contract, "table", "unknown"),
        "nimbus.generated_at"     : datetime.now().isoformat(),
        "nimbus.warnings_count"   : str(len(warnings)),
    }

    if warnings:
        # Guarda apenas os primeiros 10 para não inflar o footer
        meta["nimbus.warnings"] = json.dumps(warnings[:10])

    return {k.encode(): v.encode() for k, v in meta.items()}


# ─────────────────────────────────────────────────────────────────────────────
# Helpers internos
# ─────────────────────────────────────────────────────────────────────────────

def _cast_column(
    series: pd.Series,
    col_name: str,
    manifest_type: str,
    date_format: Optional[str],
) -> tuple[pd.Series, list[str]]:
    """
    Tenta converter uma Series para o tipo declarado no Manifest.

    Retorna (series_convertida, warnings). Se o cast falhar acima do threshold,
    retorna a series original como string e registra o WARNING.
    """
    warnings: list[str] = []

    if manifest_type == "string":
        return series.astype(str).where(series.notna(), other=None), warnings

    if manifest_type in ("integer", "int", "long"):
        return _cast_numeric(series, col_name, pa.int64(), warnings, integer=True)

    if manifest_type in ("float", "double", "decimal", "numeric"):
        return _cast_numeric(series, col_name, pa.float64(), warnings, integer=False)

    if manifest_type in ("boolean", "bool"):
        return _cast_boolean(series, col_name, warnings)

    if manifest_type == "date":
        return _cast_date(series, col_name, date_format, warnings, as_datetime=False)

    if manifest_type in ("datetime", "timestamp"):
        return _cast_date(series, col_name, date_format, warnings, as_datetime=True)

    # Tipo desconhecido — mantém como string
    warnings.append(
        "UNKNOWN_TYPE: tipo '{}' em '{}' nao reconhecido, "
        "mantido como string.".format(manifest_type, col_name)
    )
    return series, warnings


def _cast_numeric(
    series: pd.Series,
    col_name: str,
    arrow_type: pa.DataType,
    warnings: list,
    integer: bool,
) -> tuple[pd.Series, list[str]]:
    """Cast para int64 ou float64 com verificação de threshold."""
    non_null   = series.dropna().replace("", pd.NA).dropna()
    converted  = pd.to_numeric(non_null, errors="coerce")
    fail_count = converted.isna().sum()
    fail_rate  = fail_count / len(non_null) if len(non_null) > 0 else 0

    if fail_rate > CAST_FAIL_THRESHOLD:
        warnings.append(
            "CAST_FAIL: '{}' declarada como {} mas {:.1f}% dos valores "
            "nao puderam ser convertidos. Mantida como string.".format(
                col_name,
                "integer" if integer else "float",
                fail_rate * 100,
            )
        )
        return series.astype(object), warnings

    result = pd.to_numeric(series, errors="coerce")
    if integer:
        # Int64 (nullable) para preservar NaN sem virar float
        result = result.astype("Int64")
    return result, warnings


def _cast_boolean(
    series: pd.Series,
    col_name: str,
    warnings: list,
) -> tuple[pd.Series, list[str]]:
    """Cast para boolean usando os domínios reconhecidos."""
    def _to_bool(val):
        if pd.isna(val) or val == "":
            return None
        v = str(val).strip().lower()
        if v in _BOOL_TRUE:  return True
        if v in _BOOL_FALSE: return False
        return None  # valor fora do domínio → null

    non_null   = series.dropna().replace("", pd.NA).dropna()
    mapped     = non_null.apply(_to_bool)
    fail_count = mapped.isna().sum()
    fail_rate  = fail_count / len(non_null) if len(non_null) > 0 else 0

    if fail_rate > CAST_FAIL_THRESHOLD:
        warnings.append(
            "CAST_FAIL: '{}' declarada como boolean mas {:.1f}% dos valores "
            "nao pertencem a nenhum dominio reconhecido (S/N, 0/1, True/False). "
            "Mantida como string.".format(col_name, fail_rate * 100)
        )
        return series.astype(object), warnings

    result = series.apply(_to_bool)
    # boolean nullable via pd.BooleanDtype (pandas 3.x compativel)
    try:
        return result.astype(pd.BooleanDtype()), warnings
    except Exception:
        return result, warnings


def _cast_date(
    series: pd.Series,
    col_name: str,
    date_format: Optional[str],
    warnings: list,
    as_datetime: bool,
) -> tuple[pd.Series, list[str]]:
    """Cast para date32 ou timestamp, tentando formatos conhecidos."""
    formats_to_try = [date_format] if date_format else []
    formats_to_try += [f for f in _DATE_FORMATS if f != date_format]

    non_null = series.dropna().replace("", pd.NA).dropna()

    for fmt in formats_to_try:
        try:
            converted  = pd.to_datetime(non_null, format=fmt, errors="coerce")
            fail_count = converted.isna().sum()
            fail_rate  = fail_count / len(non_null) if len(non_null) > 0 else 0

            if fail_rate <= CAST_FAIL_THRESHOLD:
                # Formato funcionou
                result = pd.to_datetime(series, format=fmt, errors="coerce")
                if not as_datetime:
                    result = result.dt.date
                if fmt != date_format and date_format is not None:
                    warnings.append(
                        "DATE_FORMAT_FALLBACK: '{}' — formato declarado '{}' falhou, "
                        "usando '{}'. Atualize o Manifest.".format(
                            col_name, date_format, fmt
                        )
                    )
                return result, warnings
        except (ValueError, TypeError):
            continue

    # Nenhum formato especifico funcionou — tenta inferencia automatica
    try:
        converted  = pd.to_datetime(non_null, errors="coerce")
        fail_count = converted.isna().sum()
        fail_rate  = fail_count / len(non_null) if len(non_null) > 0 else 0
        if fail_rate <= CAST_FAIL_THRESHOLD:
            result = pd.to_datetime(series, errors="coerce")
            if not as_datetime:
                result = result.dt.date
            return result, warnings
    except Exception:
        pass

    warnings.append(
        "CAST_FAIL: '{}' declarada como {} mas nenhum formato de data "
        "reconhecido funcionou. Mantida como string.".format(
            col_name, "datetime" if as_datetime else "date"
        )
    )
    return series.astype(object), warnings


def _extract_date_format(col_def) -> Optional[str]:
    """
    Extrai o formato de data do campo business_rules do Manifest.
    O extractor_csv grava o formato detectado como:
        'Formato detectado: %d/%m/%Y'
    """
    for rule in (col_def.business_rules or []):
        if "Formato detectado" in rule or "formato" in rule.lower():
            for fmt in _DATE_FORMATS:
                if fmt in rule:
                    return fmt
    return None
