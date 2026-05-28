"""
Motor de validação de contratos de dados.

Detecta schema evolution (breaking vs non-breaking) e roteia
arquivos inválidos para quarentena (DLQ).
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import pandas as pd
import yaml

from src.validation.contracts import DataContract


def _load_contract_from_storage(storage, contract_filename: str) -> DataContract:
    """Carrega contrato via Storage (local ou MinIO)."""
    path = storage.read_path("contracts", contract_filename)
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return DataContract.from_dict(raw)


@dataclass
class ValidationResult:
    table          : str
    status         : str
    scenario       : str = "baseline"
    evolution_type : Optional[str] = None
    issues         : list = field(default_factory=list)
    warnings       : list = field(default_factory=list)
    rows_total     : int = 0
    rows_valid     : int = 0
    null_violations: dict = field(default_factory=dict)
    duplicate_count: int = 0

    def to_dict(self) -> dict:
        return self.__dict__


_PANDAS_TYPE_MAP = {
    "string"  : ["object", "string", "str"],      # pandas 2.x usa StringDtype
    "integer" : ["int64", "int32", "int16", "Int64", "int8"],
    "float"   : ["float64", "float32", "Float64"],
    "boolean" : ["bool", "boolean"],
    "date"    : ["object", "datetime64[ns]", "string", "str"],
    "datetime": ["object", "datetime64[ns]", "string", "str"],
}


def _can_coerce(series: pd.Series, expected_type: str) -> bool:
    """Verifica se os valores não-nulos de uma coluna podem ser convertidos ao tipo esperado."""
    sample = series.dropna().head(50)
    if len(sample) == 0:
        return True
    try:
        if expected_type in ("integer",):
            sample.apply(lambda x: int(str(x).strip()))
        elif expected_type in ("float",):
            sample.apply(lambda x: float(str(x).strip()))
        elif expected_type == "boolean":
            valid = {"true", "false", "1", "0", "yes", "no", "sim", "não", "nao"}
            return all(str(x).strip().lower() in valid for x in sample)
        # string, date, datetime: qualquer string é aceitável na landing zone
        return True
    except (ValueError, TypeError):
        return False


def _detect_schema_evolution(
    contract: DataContract, df: pd.DataFrame
) -> tuple:
    """
    Compara colunas do DataFrame com o contrato.
    Retorna: (evolution_type, issues_criticos, warnings)
    """
    contract_cols = set(contract.column_names())
    data_cols     = set(df.columns)
    issues, warnings = [], []

    missing_in_data = contract_cols - data_cols
    extra_in_data   = data_cols - contract_cols

    # Colunas não-anuláveis ausentes → BREAKING
    required_missing = [
        c for c in missing_in_data
        if not next((col.nullable for col in contract.schema if col.name == c), True)
    ]
    if required_missing:
        issues.append(f"Colunas obrigatórias ausentes: {required_missing}")
        return "BREAKING", issues, warnings

    # Chave primária ausente → BREAKING
    pk_missing = [pk for pk in contract.get_primary_keys() if pk in missing_in_data]
    if pk_missing:
        issues.append(f"Chave primária ausente: {pk_missing}")
        return "BREAKING", issues, warnings

    # Coerção de tipo apenas para colunas de chave primária (dado vem como string do CSV)
    type_map = contract.column_type_map()
    for pk in contract.get_primary_keys():
        if pk not in df.columns:
            continue
        expected = type_map.get(pk, "string")
        if not _can_coerce(df[pk], expected):
            issues.append(
                f"PK '{pk}' contém valores não conversíveis para {expected} - possivel breaking change"
            )
            return "BREAKING", issues, warnings

    # Colunas extras → NON-BREAKING
    if extra_in_data:
        warnings.append(f"Novas colunas detectadas (non-breaking): {sorted(extra_in_data)}")
        return "NON_BREAKING", issues, warnings

    return None, issues, warnings


def _check_nulls(contract: DataContract, df: pd.DataFrame) -> tuple[list[str], dict]:
    issues = {}
    for col in contract.get_non_nullable():
        if col not in df.columns:
            continue
        null_pct = df[col].isna().mean() * 100
        if null_pct > 0:
            issues[col] = round(null_pct, 2)
    return issues


# ─────────────────────────────────────────────────────────────────────────────
# Função principal
# ─────────────────────────────────────────────────────────────────────────────
def validate(
    storage          ,          # StorageBase — local ou MinIO
    filename         : str,
    contract_filename: str,
    scenario         : str = "baseline",
) -> ValidationResult:
    """
    Valida um arquivo da camada Bronze contra seu contrato de dados.

    Em caso de BREAKING CHANGE, roteia para a camada Quarantine (DLQ).
    Em caso de PASS/WARNING, o arquivo permanece no Bronze até ser
    promovido para Silver pelo módulo chamador.
    """
    table  = contract_filename.split("_non_breaking")[0].split("_breaking")[0].replace(".yaml","")
    result = ValidationResult(table=table, status="PASS", scenario=scenario)

    # 1. Carregar contrato da camada contracts
    try:
        contract = _load_contract_from_storage(storage, contract_filename)
    except Exception as e:
        result.status = "DLQ"
        result.issues.append(f"Manifesto YAML invalido: {e}")
        return result

    # 2. Ler dado da camada Bronze — sempre como string (dado bruto do legado)
    try:
        df = storage.read("bronze", filename)
    except Exception as e:
        result.status = "DLQ"
        result.issues.append(f"Arquivo ilegivel: {e}")
        return result

    result.rows_total = len(df)

    # 3. Aviso de manifesto DRAFT — não bloqueia, mas registra no resultado
    if not contract.is_validated():
        result.warnings.append(
            "Manifesto em status DRAFT — documentacao gerada sem validacao humana. "
            "Execute: python -m src.manifest.manifest_validator --file <contrato.yaml> --steward 'Nome'"
        )

    # 4. Schema evolution
    evolution_type, issues, warnings = _detect_schema_evolution(contract, df)
    result.evolution_type = evolution_type
    result.issues.extend(issues)
    result.warnings.extend(warnings)

    if issues:  # BREAKING → Quarantine
        result.status = "DLQ"
        storage.write("quarantine", filename, df)
        print(f"   [DLQ] [{table}] BREAKING CHANGE -> quarantine/{filename}")
        return result

    if warnings:
        result.status = "WARNING"
        print(f"   [WARN] [{table}] NON-BREAKING CHANGE detectado")
        for w in warnings:
            print(f"          -> {w}")

    # 5. Nulos em colunas obrigatórias
    null_violations = _check_nulls(contract, df)
    if null_violations:
        result.null_violations = null_violations
        result.warnings.append(f"Nulos em colunas obrigatorias: {null_violations}")
        if result.status == "PASS":
            result.status = "WARNING"

    # 6. Duplicatas
    pk_cols = contract.get_primary_keys()
    if pk_cols:
        dup_count = df.duplicated(subset=pk_cols).sum()
        result.duplicate_count = int(dup_count)
        dup_pct = dup_count / len(df) * 100
        if dup_count > 0 and not contract.tolerance.allow_duplicates:
            result.warnings.append(f"{dup_count} duplicatas detectadas ({dup_pct:.1f}%)")
            if result.status == "PASS":
                result.status = "WARNING"

    result.rows_valid = result.rows_total - result.duplicate_count
    if result.status == "PASS":
        print(f"   [OK] [{table}] Validacao OK - {result.rows_total} linhas")

    return result
