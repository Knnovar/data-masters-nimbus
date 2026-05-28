"""
Modelos de contrato de dados — compatível com manifestos antigos e estendidos.

Todos os campos novos são opcionais (default=None) para garantir que
manifestos existentes continuem válidos sem alteração.

Hierarquia de dataclasses:
    DataContract
    ├── SourceInfo           origem e formato do arquivo
    ├── RegulatoryInfo       classificação e tags regulatórias
    ├── StewardInfo          responsável e contato
    ├── TolerancePolicy      limites de qualidade
    ├── SampleQuery          exemplo de query para Devin
    └── ColumnContract[]
            ├── LayoutField  apenas para fixed_width
            └── campos base  name, type, nullable, etc.
"""

from dataclasses import dataclass, field
from typing import Optional


# ─────────────────────────────────────────────────────────────────────────────
# Dataclasses auxiliares — campos estendidos
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class SourceInfo:
    """Informações sobre a origem e formato do arquivo."""
    system           : Optional[str] = None   # nome do sistema de origem
    format           : str = "csv"            # csv|fixed_width|sas7bdat|json|xlsx|xml|parquet
    encoding         : str = "utf-8"          # utf-8|latin-1|ebcdic|cp1252
    os               : Optional[str] = None   # windows|unix|mainframe
    delimiter        : Optional[str] = None   # apenas para csv
    update_frequency : Optional[str] = None   # daily|weekly|monthly|event_driven
    contact          : Optional[str] = None   # e-mail do time de origem

    @classmethod
    def from_dict(cls, d: dict) -> "SourceInfo":
        return cls(
            system           = d.get("system"),
            format           = d.get("format", "csv"),
            encoding         = d.get("encoding", "utf-8"),
            os               = d.get("os"),
            delimiter        = d.get("delimiter"),
            update_frequency = d.get("update_frequency"),
            contact          = d.get("contact"),
        )


@dataclass
class RegulatoryInfo:
    """Classificação regulatória e de segurança da informação."""
    tags                : list = field(default_factory=list)
    data_classification : str = "internal"   # public|internal|confidential|restricted
    retention_years     : Optional[int] = None

    @classmethod
    def from_dict(cls, d: dict) -> "RegulatoryInfo":
        return cls(
            tags                = d.get("tags", []),
            data_classification = d.get("data_classification", "internal"),
            retention_years     = d.get("retention_years"),
        )


@dataclass
class StewardInfo:
    """Data Steward responsável pela tabela."""
    name  : Optional[str] = None
    email : Optional[str] = None

    @classmethod
    def from_dict(cls, d: dict) -> "StewardInfo":
        return cls(name=d.get("name"), email=d.get("email"))


@dataclass
class SampleQuery:
    """Exemplo de query útil para consumo pelo Devin via RAG."""
    description : str = ""
    sql         : str = ""

    @classmethod
    def from_dict(cls, d: dict) -> "SampleQuery":
        return cls(description=d.get("description", ""), sql=d.get("sql", ""))


@dataclass
class LayoutField:
    """Definição de campo para arquivos posicionais (fixed_width)."""
    field : str
    start : int
    end   : int
    dtype : str = "string"

    @classmethod
    def from_dict(cls, d: dict) -> "LayoutField":
        return cls(
            field = d["field"],
            start = d["start"],
            end   = d["end"],
            dtype = d.get("dtype", "string"),
        )


# ─────────────────────────────────────────────────────────────────────────────
# ColumnContract — estendido
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ColumnContract:
    """Contrato de uma coluna — campos base + campos estendidos opcionais."""
    # Campos originais
    name        : str
    type        : str
    nullable    : bool = True
    primary_key : bool = False

    # Campos estendidos — gerados pelo extrator ou pela SLM
    description      : Optional[str] = None   # descrição de negócio da coluna
    sas_label        : Optional[str] = None   # label original do SAS7BDAT
    regulatory_flags : list = field(default_factory=list)  # ex: ["LGPD_SENSITIVE"]
    business_rules   : list = field(default_factory=list)  # regras de negócio observadas

    @classmethod
    def from_dict(cls, d: dict) -> "ColumnContract":
        return cls(
            name             = d["name"],
            type             = d["type"],
            nullable         = d.get("nullable", True),
            primary_key      = d.get("primary_key", False),
            description      = d.get("description"),
            sas_label        = d.get("sas_label"),
            regulatory_flags = d.get("regulatory_flags", []),
            business_rules   = d.get("business_rules", []),
        )


# ─────────────────────────────────────────────────────────────────────────────
# TolerancePolicy — inalterado
# ─────────────────────────────────────────────────────────────────────────────

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


# ─────────────────────────────────────────────────────────────────────────────
# DataContract — raiz
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class DataContract:
    """
    Contrato de dados completo.

    Campos originais são obrigatórios para compatibilidade retroativa.
    Todos os campos estendidos são opcionais — manifestos antigos
    continuam sendo carregados sem erro.
    """
    # Campos originais — obrigatórios
    table      : str
    description: str
    owner      : str
    version    : str
    tolerance  : TolerancePolicy
    schema     : list   # list[ColumnContract]

    # Campos estendidos — opcionais
    manifest_status  : str = "DRAFT"     # DRAFT | VALIDATED
    validated_by     : Optional[str] = None
    validated_at     : Optional[str] = None
    source           : Optional[SourceInfo] = None
    regulatory       : Optional[RegulatoryInfo] = None
    steward          : Optional[StewardInfo] = None
    business_context : Optional[str] = None
    dependencies     : list = field(default_factory=list)
    sample_queries   : list = field(default_factory=list)  # list[SampleQuery]

    @classmethod
    def from_dict(cls, d: dict) -> "DataContract":
        parts = d.get("version", "1.0.0").split(".")
        if len(parts) != 3 or not all(p.isdigit() for p in parts):
            raise ValueError(f"Versão inválida: {d.get('version')}")

        return cls(
            table      = d["table"],
            description= d.get("description", ""),
            owner      = d.get("owner", ""),
            version    = d["version"],
            tolerance  = TolerancePolicy.from_dict(d.get("tolerance", {})),
            schema     = [ColumnContract.from_dict(c) for c in d.get("schema", [])],

            manifest_status  = d.get("manifest_status", "DRAFT"),
            validated_by     = d.get("validated_by"),
            validated_at     = d.get("validated_at"),
            source           = SourceInfo.from_dict(d["source"]) if d.get("source") else None,
            regulatory       = RegulatoryInfo.from_dict(d["regulatory"]) if d.get("regulatory") else None,
            steward          = StewardInfo.from_dict(d["steward"]) if d.get("steward") else None,
            business_context = d.get("business_context"),
            dependencies     = d.get("dependencies", []),
            sample_queries   = [SampleQuery.from_dict(q) for q in d.get("sample_queries", [])],
        )

    # ── Métodos auxiliares ────────────────────────────────────────────────────

    def get_primary_keys(self) -> list:
        return [c.name for c in self.schema if c.primary_key]

    def get_non_nullable(self) -> list:
        return [c.name for c in self.schema if not c.nullable]

    def column_names(self) -> list:
        return [c.name for c in self.schema]

    def column_type_map(self) -> dict:
        return {c.name: c.type for c in self.schema}

    def is_validated(self) -> bool:
        return self.manifest_status == "VALIDATED"

    def has_extended_metadata(self) -> bool:
        return any([
            self.business_context,
            self.source,
            self.regulatory,
            self.steward,
        ])

    def lgpd_sensitive_columns(self) -> list:
        return [
            c.name for c in self.schema
            if "LGPD_SENSITIVE" in c.regulatory_flags
        ]
