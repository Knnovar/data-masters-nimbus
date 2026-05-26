"""
Modelos Pydantic para os manifestos YAML de Contrato de Dados.
"""

from dataclasses import dataclass, field
from typing import Literal, Optional

# Pydantic é usado quando disponível; fallback para dataclasses puras
try:
    from pydantic import BaseModel, field_validator
    _USE_PYDANTIC = True
except ImportError:
    _USE_PYDANTIC = False


@dataclass
class ColumnContract:
    name        : str
    type        : str   # "string"|"integer"|"float"|"boolean"|"date"|"datetime"
    nullable    : bool = True
    primary_key : bool = False

    @classmethod
    def from_dict(cls, d: dict) -> "ColumnContract":
        return cls(
            name        = d["name"],
            type        = d["type"],
            nullable    = d.get("nullable", True),
            primary_key = d.get("primary_key", False),
        )


@dataclass
class TolerancePolicy:
    max_null_pct    : float = 20.0
    allow_duplicates: bool  = False

    @classmethod
    def from_dict(cls, d: dict) -> "TolerancePolicy":
        return cls(
            max_null_pct    = d.get("max_null_pct", 20.0),
            allow_duplicates= d.get("allow_duplicates", False),
        )


@dataclass
class DataContract:
    table      : str
    description: str
    owner      : str
    version    : str
    tolerance  : TolerancePolicy
    schema     : list

    @classmethod
    def from_dict(cls, d: dict) -> "DataContract":
        parts = d.get("version", "1.0.0").split(".")
        if len(parts) != 3 or not all(p.isdigit() for p in parts):
            raise ValueError(f"Versão inválida: {d.get('version')}")
        tol = TolerancePolicy.from_dict(d.get("tolerance", {}))
        cols = [ColumnContract.from_dict(c) for c in d.get("schema", [])]
        return cls(
            table      = d["table"],
            description= d.get("description", ""),
            owner      = d.get("owner", ""),
            version    = d["version"],
            tolerance  = tol,
            schema     = cols,
        )

    def get_primary_keys(self) -> list:
        return [c.name for c in self.schema if c.primary_key]

    def get_non_nullable(self) -> list:
        return [c.name for c in self.schema if not c.nullable]

    def column_names(self) -> list:
        return [c.name for c in self.schema]

    def column_type_map(self) -> dict:
        return {c.name: c.type for c in self.schema}
