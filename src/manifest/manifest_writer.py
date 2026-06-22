"""
src/manifest/manifest_writer.py — Serialização e escrita de manifestos YAML.

Responsabilidades:
  - Serializar o dict de manifesto para YAML legível
  - Nunca sobrescrever um manifesto VALIDATED sem flag explícita
  - Criar arquivo _draft.yaml quando o destino já é VALIDATED
  - Validar que o dict tem os campos mínimos obrigatórios antes de gravar
"""

from pathlib import Path
from datetime import datetime
import yaml


class ManifestWriter:

    REQUIRED_FIELDS = {"table", "version", "schema"}

    def write(self, manifest: dict, output_path: Path, overwrite: bool = False) -> Path:
        """
        Grava o manifesto em YAML.

        Regras de proteção:
          - Se output_path existe com manifest_status=VALIDATED → cria _draft.yaml
          - Se output_path existe com manifest_status=DRAFT e overwrite=False → aborta
          - Se overwrite=True e status != VALIDATED → sobrescreve
        """
        self._validate_minimum(manifest)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Verifica se o destino já existe
        if output_path.exists():
            existing_status = self._read_status(output_path)

            if existing_status == "VALIDATED":
                # Nunca sobrescreve VALIDATED — cria draft paralelo
                draft_path = output_path.with_stem(output_path.stem + "_draft")
                print(
                    f"[WRITER] AVISO: {output_path.name} já existe com status VALIDATED.\n"
                    f"         Salvando rascunho em: {draft_path.name}"
                )
                return self._dump(manifest, draft_path)

            if not overwrite:
                print(
                    f"[WRITER] AVISO: {output_path.name} já existe (DRAFT).\n"
                    f"         Use --overwrite para substituir."
                )
                return output_path

        return self._dump(manifest, output_path)

    def _dump(self, manifest: dict, path: Path) -> Path:
        """Serializa o manifesto para YAML com formatação legível."""

        # Adiciona timestamp de geração
        manifest = {**manifest, "_generated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")}

        with open(path, "w", encoding="utf-8") as f:
            # Cabeçalho informativo
            f.write(
                f"# Manifesto: {manifest.get('table', 'desconhecido')}\n"
                f"# Status: {manifest.get('manifest_status', 'DRAFT')}\n"
                f"# Gerado em: {manifest['_generated_at']}\n"
                f"# Campos marcados com '# TODO' requerem preenchimento manual.\n\n"
            )
            yaml.dump(
                manifest,
                f,
                allow_unicode   = True,
                sort_keys       = False,
                default_flow_style = False,
                width           = 120,
            )

        print(f"[WRITER] Manifesto gravado: {path}")
        return path

    def _validate_minimum(self, manifest: dict) -> None:
        missing = self.REQUIRED_FIELDS - set(manifest.keys())
        if missing:
            raise ValueError(f"Manifesto invalido - campos obrigatorios ausentes: {missing}")

        if not manifest.get("schema"):
            raise ValueError("Manifesto invalido - schema nao pode ser vazio.")

    def _read_status(self, path: Path) -> str:
        """Lê apenas o manifest_status de um YAML existente."""
        try:
            with open(path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            return data.get("manifest_status", "DRAFT")
        except Exception:
            return "DRAFT"
