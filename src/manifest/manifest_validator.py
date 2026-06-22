"""
src/manifest/manifest_validator.py — Promoção HITL de manifesto DRAFT → VALIDATED.

Responsabilidades:
  - Verificar que todos os campos TODO foram preenchidos
  - Registrar quem validou e quando
  - Atualizar o manifest_status para VALIDATED
  - Bloquear promoção se campos obrigatórios ainda têm placeholder

Uso via CLI:
    python -m src.manifest.manifest_validator \\
        --file data/contracts/tb_clientes.yaml \\
        --steward "Joao Silva" \\
        --check-only        # apenas lista pendências, não promove
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


# Placeholder padrão gerado pelo extrator — indica campo não preenchido
_TODO_MARKER = "# TODO"

# Campos que DEVEM estar preenchidos para promover a VALIDATED
_REQUIRED_FOR_VALIDATION = [
    "description",
    "owner",
    "business_context",
]

# Campos de coluna que DEVEM estar preenchidos
_REQUIRED_COL_FIELDS = ["description"]


class ManifestValidator:

    def check(self, manifest_path: Path) -> dict:
        """
        Verifica pendências no manifesto sem alterar o arquivo.

        Retorna:
            {
                "ready": bool,
                "pending": [{"field": ..., "issue": ...}],
                "warnings": [...],
            }
        """
        manifest = self._load(manifest_path)
        pending  = []
        warnings = []

        # Verifica campos raiz
        for field in _REQUIRED_FOR_VALIDATION:
            val = manifest.get(field, "")
            if not val or _TODO_MARKER in str(val):
                pending.append({"field": field, "issue": "Não preenchido ou contém TODO"})

        # Verifica source
        source = manifest.get("source") or {}
        for key in ["system", "os", "update_frequency", "contact"]:
            if _TODO_MARKER in str(source.get(key, "")):
                pending.append({"field": f"source.{key}", "issue": "Contém TODO"})

        # Verifica steward
        steward = manifest.get("steward") or {}
        for key in ["name", "email"]:
            if not steward.get(key) or _TODO_MARKER in str(steward.get(key, "")):
                pending.append({"field": f"steward.{key}", "issue": "Não preenchido"})

        # Verifica regulatory tags
        reg = manifest.get("regulatory") or {}
        tags = reg.get("tags", [])
        if not tags or any(_TODO_MARKER in str(t) for t in tags):
            pending.append({"field": "regulatory.tags", "issue": "Tags regulatórias não revisadas"})

        # Verifica colunas
        for col in manifest.get("schema", []):
            col_name = col.get("name", "?")
            for cf in _REQUIRED_COL_FIELDS:
                val = col.get(cf, "")
                if not val or _TODO_MARKER in str(val):
                    pending.append({
                        "field": f"schema[{col_name}].{cf}",
                        "issue": "Não preenchido ou contém TODO"
                    })
            # Warning (não bloqueia): colunas sem business_rules
            if not col.get("business_rules"):
                warnings.append(f"schema[{col_name}].business_rules está vazio")

        # Warning: sem sample_queries
        if not manifest.get("sample_queries"):
            warnings.append("sample_queries esta vazio - recomendado para o Devin")

        return {
            "ready"   : len(pending) == 0,
            "pending" : pending,
            "warnings": warnings,
        }

    def promote(self, manifest_path: Path, steward_name: str) -> bool:
        """
        Promove o manifesto de DRAFT para VALIDATED após verificar pendências.

        Retorna True se promovido, False se há pendências bloqueantes.
        """
        result = self.check(manifest_path)

        if not result["ready"]:
            print(f"\n[VALIDATOR] Promocao bloqueada - {len(result['pending'])} pendencia(s):")
            for p in result["pending"]:
                print(f"   [PENDENTE] {p['field']}: {p['issue']}")
            print("\nPreencha os campos acima antes de promover.")
            return False

        # Exibe warnings sem bloquear
        if result["warnings"]:
            print(f"\n[VALIDATOR] {len(result['warnings'])} aviso(s) (não bloqueante):")
            for w in result["warnings"]:
                print(f"   [AVISO] {w}")

        # Promove
        manifest = self._load(manifest_path)
        manifest["manifest_status"] = "VALIDATED"
        manifest["validated_by"]    = steward_name
        manifest["validated_at"]    = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

        # Reescreve o arquivo preservando o cabeçalho
        with open(manifest_path, "w", encoding="utf-8") as f:
            f.write(
                f"# Manifesto: {manifest.get('table', '')}\n"
                f"# Status: VALIDATED\n"
                f"# Validado por: {steward_name} em {manifest['validated_at']}\n\n"
            )
            yaml.dump(manifest, f, allow_unicode=True, sort_keys=False,
                      default_flow_style=False, width=120)

        print(f"\n[VALIDATOR] Manifesto promovido para VALIDATED por '{steward_name}'")
        print(f"            Arquivo: {manifest_path}")
        return True

    def _load(self, path: Path) -> dict:
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Valida e promove um manifesto YAML de DRAFT para VALIDATED."
    )
    parser.add_argument("--file",       required=True, help="Caminho do manifesto YAML")
    parser.add_argument("--steward",    default=None,  help="Nome do Data Steward responsável")
    parser.add_argument("--check-only", action="store_true",
                        help="Apenas lista pendências sem promover")
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        print(f"[ERROR] Arquivo não encontrado: {path}")
        sys.exit(1)

    validator = ManifestValidator()
    result    = validator.check(path)

    print(f"\n[VALIDATOR] Verificando: {path.name}")
    print(f"            Status: {'PRONTO PARA VALIDAR' if result['ready'] else 'COM PENDÊNCIAS'}")

    if result["pending"]:
        print(f"\n  Pendências ({len(result['pending'])}):")
        for p in result["pending"]:
            print(f"    [PENDENTE] {p['field']}: {p['issue']}")

    if result["warnings"]:
        print(f"\n  Avisos ({len(result['warnings'])}):")
        for w in result["warnings"]:
            print(f"    [AVISO] {w}")

    if args.check_only:
        sys.exit(0 if result["ready"] else 1)

    if not args.steward:
        print("\n[ERROR] Informe --steward 'Nome do Steward' para promover.")
        sys.exit(1)

    ok = validator.promote(path, args.steward)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
