"""
src/manifest/extractor_base.py — Interface base para extratores de manifesto.

Cada formato de arquivo (SAS7BDAT, CSV, fixed-width, JSON…) implementa
esta interface e devolve um dict compatível com o schema do manifesto estendido.
"""

from abc import ABC, abstractmethod
from pathlib import Path


class ExtractorBase(ABC):
    """Interface comum para todos os extratores de manifesto."""

    @abstractmethod
    def extract(self, file_path: Path, table_name: str) -> dict:
        """
        Lê os metadados do arquivo e retorna um dict pronto para ser
        serializado como manifesto YAML.

        Contrato de retorno:
          - manifest_status sempre "DRAFT"
          - Campos não inferíveis ficam como None ou lista vazia
          - Campos marcados com "# TODO: preencher" indicam revisão manual
        """

    @abstractmethod
    def supported_formats(self) -> list[str]:
        """Extensões suportadas por este extrator. Ex: ['.sas7bdat']"""

    # ── Helpers de detecção regulatória ──────────────────────────────────────

    _LGPD_PATTERNS = [
        "cpf", "cnpj", "rg", "passaporte", "nome", "email",
        "telefone", "celular", "endereco", "nascimento", "mae",
    ]
    _SCR_PATTERNS = [
        "renda", "salario", "limite", "credito", "divida",
        "inadimplencia", "score", "rating",
    ]
    _RESTRICTED_PATTERNS = [
        "senha", "token", "chave", "secret", "hash", "pin",
    ]

    def _detect_regulatory_flags(self, col_name: str, label: str = "") -> list:
        """
        Detecta flags regulatórias por heurística no nome e label da coluna.
        Resultado é sempre DRAFT — requer confirmação do Data Steward.
        """
        text = f"{col_name} {label}".lower()
        flags = []
        if any(p in text for p in self._LGPD_PATTERNS):
            flags.append("LGPD_SENSITIVE")
        if any(p in text for p in self._SCR_PATTERNS):
            flags.append("SCR_CANDIDATE")
        if any(p in text for p in self._RESTRICTED_PATTERNS):
            flags.append("RESTRICTED")
        return flags

    def _detect_table_regulatory_tags(self, columns: list) -> list:
        """Agrega tags regulatórias a partir das colunas detectadas."""
        flags = set()
        for col in columns:
            flags.update(col.get("regulatory_flags", []))
        tags = []
        if "LGPD_SENSITIVE" in flags:
            tags.append("LGPD")
        if "SCR_CANDIDATE" in flags:
            tags.append("SCR")
        if flags:
            tags.append("BACEN_4658")
        return tags

    def _normalize_column_name(self, raw_name: str) -> str:
        """
        Normaliza nomes de variáveis SAS/legado para snake_case.
        Ex: "CD CLIENTE", "CD_CLIENTE", "CdCliente" → "cd_cliente"
        """
        import re
        # Substitui espaços e hífens por underscore
        name = raw_name.strip().replace(" ", "_").replace("-", "_")
        # CamelCase → snake_case
        name = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
        name = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", name)
        # Remove caracteres especiais, lowercase
        name = re.sub(r"[^\w]", "_", name).lower()
        # Remove underscores duplicados
        name = re.sub(r"_+", "_", name).strip("_")
        return name
