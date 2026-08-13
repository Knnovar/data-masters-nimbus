"""
src/manifest/extractor_sas7bdat.py — Extrator de manifesto para arquivos SAS7BDAT.

Lê metadados internos do arquivo .sas7bdat via pyreadstat (metadataonly=True)
e gera um rascunho de manifesto YAML sem precisar carregar os dados em memória.

Uso via CLI:
    python -m src.manifest.extractor_sas7bdat \\
        --file data/landing/tb_clientes.sas7bdat \\
        --table tb_clientes \\
        --output data/contracts/tb_clientes.yaml

    # Com enriquecimento SLM (requer ollama serve):
    python -m src.manifest.extractor_sas7bdat \\
        --file data/landing/tb_clientes.sas7bdat \\
        --table tb_clientes \\
        --output data/contracts/tb_clientes.yaml \\
        --enrich
"""

import argparse
import sys
from pathlib import Path

# Garante que o projeto é encontrado quando rodado como módulo
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.manifest.extractor_base import ExtractorBase
from src.manifest.manifest_writer import ManifestWriter


# ── Mapeamento de formatos SAS para tipos do manifesto ────────────────────────
# Formatos SAS → type canônico
_SAS_FORMAT_MAP = {
    # Numéricos inteiros
    "best"   : "float",
    "comma"  : "float",
    "dollar" : "float",
    "f"      : "float",
    "e"      : "float",
    "pct"    : "float",
    "z"      : "integer",
    "ib"     : "integer",
    "pk"     : "integer",
    # Datas
    "date"   : "date",
    "ddmmyy" : "date",
    "mmddyy" : "date",
    "yymmdd" : "date",
    "yymmddn": "date",
    "julian" : "date",
    # Datetimes
    "datetime": "datetime",
    "dt"      : "datetime",
    "tod"     : "datetime",
    # Strings
    "$"       : "string",
    "char"    : "string",
}

# Formatos SAS que indicam booleano por convenção bancária (0/1)
_BOOLEAN_HINTS = {"yn", "yesno", "truefalse", "simnao"}


def _map_sas_type(sas_format: str, sas_type: str) -> str:
    """
    Converte formato SAS e tipo interno para tipo do manifesto.

    sas_type: "numeric" | "character"
    sas_format: ex "DATE9.", "BEST12.", "$CHAR20.", ""
    """
    if sas_type == "character":
        return "string"

    # Normaliza o formato: remove dígitos e ponto, lowercase
    import re
    fmt_clean = re.sub(r"[\d\.]", "", sas_format.lower()).strip("$")

    # Verifica boolean por convenção
    if fmt_clean in _BOOLEAN_HINTS:
        return "boolean"

    # Busca no mapa de formatos
    for key, mapped_type in _SAS_FORMAT_MAP.items():
        if fmt_clean.startswith(key):
            return mapped_type

    # Fallback: numérico sem formato reconhecido → float
    return "float"


class SAS7BDATExtractor(ExtractorBase):

    def supported_formats(self) -> list:
        return [".sas7bdat"]

    def extract(self, file_path: Path, table_name: str) -> dict:
        """
        Extrai metadados do SAS7BDAT e retorna dict de manifesto em DRAFT.

        Usa metadataonly=True para não carregar os dados em memória —
        ideal para arquivos grandes.
        """
        try:
            import pyreadstat
        except ImportError:
            raise ImportError(
                "pyreadstat não instalado.\n"
                "Execute: pip install pyreadstat"
            )

        print(f"[EXTRACT] Lendo metadados de {file_path.name} (metadataonly)...")

        # Lê apenas metadados — sem carregar dados em memória
        _, meta = pyreadstat.read_sas7bdat(
            str(file_path),
            metadataonly=True,
            encoding="latin-1",   # encoding padrão em arquivos SAS brasileiros
        )

        columns = self._build_columns(meta)
        reg_tags = self._detect_table_regulatory_tags(columns)

        manifest = {
            "table"          : table_name,
            "description"    : meta.file_label or f"# TODO: descrever {table_name}",
            "owner"          : "# TODO: squad responsável",
            "version"        : "1.0.0",
            "manifest_status": "DRAFT",
            "validated_by"   : None,
            "validated_at"   : None,

            "source": {
                "system"          : "# TODO: nome do sistema de origem",
                "format"          : "sas7bdat",
                "encoding"        : "latin-1",
                "os"              : "# TODO: unix | windows | mainframe",
                "update_frequency": "# TODO: daily | weekly | monthly | event_driven",
                "contact"         : "# TODO: email do time de origem",
            },

            "regulatory": {
                "tags"               : reg_tags if reg_tags else ["# TODO: revisar tags"],
                "data_classification": "confidential" if any(
                    "LGPD_SENSITIVE" in c.get("regulatory_flags", []) for c in columns
                ) else "internal",
                "retention_years"    : None,
            },

            "steward": {
                "name" : "# TODO: nome do Data Steward",
                "email": "# TODO: email do Data Steward",
            },

            "business_context": (
                f"# TODO: descrever o propósito de negócio de {table_name}.\n"
                f"# Origem: arquivo SAS7BDAT com {meta.number_rows} linhas "
                f"e {meta.number_columns} colunas."
            ),

            "tolerance": {
                "max_null_pct"    : 20,
                "allow_duplicates": False,
            },

            "schema"       : columns,
            "dependencies" : [],
            "sample_queries": [],
        }

        print(
            f"[EXTRACT] {table_name}: {meta.number_columns} colunas | "
            f"{meta.number_rows} linhas | "
            f"LGPD sensitivo: {any('LGPD_SENSITIVE' in c.get('regulatory_flags',[]) for c in columns)}"
        )

        return manifest

    def _build_columns(self, meta) -> list:
        """Constrói a lista de colunas a partir dos metadados do pyreadstat."""
        columns = []

        for i, raw_name in enumerate(meta.column_names):
            label  = meta.column_labels[i] if meta.column_labels else ""
            fmt    = meta.original_variable_types[i] if meta.original_variable_types else ""
            sas_type = "character" if raw_name in (meta.character_storage_widths or {}) else "numeric"

            # Tenta extrair o tipo do column_measure se disponível
            if hasattr(meta, "column_measure") and meta.column_measure:
                measure = meta.column_measure.get(raw_name, "")
                if measure == "nominal" or sas_type == "character":
                    col_type = "string"
                else:
                    col_type = _map_sas_type(str(fmt), sas_type)
            else:
                col_type = _map_sas_type(str(fmt), sas_type)

            norm_name = self._normalize_column_name(raw_name)
            reg_flags = self._detect_regulatory_flags(norm_name, str(label))

            col = {
                "name"            : norm_name,
                "type"            : col_type,
                "nullable"        : True,
                "primary_key"     : False,
                "description"     : str(label) if label else f"# TODO: descrever {norm_name}",
                "sas_label"       : str(label) if label else None,
                "regulatory_flags": reg_flags,
                "business_rules"  : [],
            }

            # Heurística: primeira coluna com padrão de ID → primary_key candidato
            if i == 0 and any(p in norm_name for p in ["cd_", "id_", "nr_", "cod"]):
                col["primary_key"] = True
                col["nullable"]    = False

            columns.append(col)

        return columns


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Extrai manifesto YAML de um arquivo SAS7BDAT."
    )
    parser.add_argument("--file",   required=True, help="Caminho do arquivo .sas7bdat")
    parser.add_argument("--table",  required=True, help="Nome da tabela (ex: tb_clientes)")
    parser.add_argument("--output", required=True, help="Caminho do YAML de saída")
    parser.add_argument(
        "--enrich", action="store_true",
        help="Chama o Ollama para enriquecer business_context e sample_queries (requer ollama serve)"
    )
    parser.add_argument(
        "--overwrite", action="store_true",
        help="Sobrescreve o YAML de saída se já existir (nunca sobrescreve VALIDATED)"
    )
    args = parser.parse_args()

    file_path   = Path(args.file)
    output_path = Path(args.output)

    if not file_path.exists():
        print(f"[ERROR] Arquivo não encontrado: {file_path}")
        sys.exit(1)

    if file_path.suffix.lower() != ".sas7bdat":
        print(f"[ERROR] Este extrator só suporta .sas7bdat. Recebido: {file_path.suffix}")
        sys.exit(1)

    extractor = SAS7BDATExtractor()
    manifest  = extractor.extract(file_path, args.table)

    if args.enrich:
        manifest = _enrich_with_slm(manifest, args.table)

    writer = ManifestWriter()
    writer.write(manifest, output_path, overwrite=args.overwrite)


def _enrich_with_slm(manifest: dict, table_name: str) -> dict:
    """Chama a SLM para enriquecer business_context e sample_queries."""
    try:
        import requests
        from config import OLLAMA_HOST, OLLAMA_MODEL

        r = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=3)
        if r.status_code != 200:
            print("[WARN] Ollama indisponivel - enriquecimento ignorado")
            return manifest
    except Exception:
        print("[WARN] Ollama indisponivel - enriquecimento ignorado")
        return manifest

    import json
    import requests
    from config import OLLAMA_HOST, OLLAMA_MODEL

    col_summary = [
        {"name": c["name"], "type": c["type"], "sas_label": c.get("sas_label"), "flags": c.get("regulatory_flags")}
        for c in manifest["schema"]
    ]

    prompt = f"""Você é um Data Steward sênior de um banco brasileiro.
Analise o schema da tabela `{table_name}` e gere:

1. Um `business_context` descrevendo o propósito da tabela (2-4 frases)
2. Duas `sample_queries` SQL úteis para analistas

Schema das colunas:
{json.dumps(col_summary, ensure_ascii=False, indent=2)}

Responda APENAS em JSON, sem markdown, no formato:
{{
  "business_context": "...",
  "sample_queries": [
    {{"description": "...", "sql": "..."}},
    {{"description": "...", "sql": "..."}}
  ]
}}"""

    print("[SLM] Enriquecendo manifesto via Ollama...")
    try:
        resp = requests.post(
            f"{OLLAMA_HOST}/api/chat",
            json={
                "model"  : OLLAMA_MODEL,
                "stream" : False,
                "options": {"temperature": 0.1, "num_predict": 600},
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=300,
        )
        resp.raise_for_status()
        raw = resp.json()["message"]["content"]

        # Remove markdown fences se presentes
        import re
        raw = re.sub(r"```(?:json)?", "", raw).strip()
        enriched = json.loads(raw)

        manifest["business_context"] = enriched.get("business_context", manifest["business_context"])
        manifest["sample_queries"]   = enriched.get("sample_queries", [])
        print("[SLM] Enriquecimento concluído")

    except Exception as e:
        print(f"[WARN] Falha no enriquecimento SLM: {e} - manifesto mantido sem enriquecimento")

    return manifest


if __name__ == "__main__":
    main()
