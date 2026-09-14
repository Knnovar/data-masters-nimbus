"""
src/manifest/manifest_version.py — Versionamento semantico do Manifest por diff de schema.

O campo `version` do Manifest era escrito a mao: nada no pipeline o incrementava,
entao uma coluna podia ser removida do contrato sem que a versao mudasse. Um
contrato cuja versao nao acompanha a mudanca nao e contrato — e documentacao.

Este modulo compara o Manifest atual com o **baseline** (a ultima versao publicada)
e deriva o incremento, com a semantica de contrato de dados, nao de biblioteca:

    MAJOR  coluna removida, tipo alterado, nullable true->false, PK alterada,
           formato/delimitador/encoding da origem alterado, tolerancia restringida
           -> quebra consumidor existente

    MINOR  coluna nova, nullable false->true, tolerancia afrouxada
           -> retrocompativel: quem ja consome continua funcionando

    PATCH  descricao, business_rules, steward, sample_queries, business_context
           -> nao muda o dado nem o schema

De onde vem o baseline, nessa ordem:
  1. `--baseline <arquivo>`, quando informado explicitamente;
  2. `git show HEAD:<caminho>` — o contrato como esta commitado;
  3. lock em `data/contracts/.lock/<tabela>.yaml` — snapshot do ultimo bump
     aplicado, usado quando nao ha git (container, tarball, workspace sem repo).

O lock e escrito a cada `--apply`, de modo que os dois caminhos convergem.

Uso:
    python -m src.manifest.manifest_version --file data/contracts/tb_clientes.yaml
    python -m src.manifest.manifest_version --file <novo> --baseline <antigo>
    python -m src.manifest.manifest_version --file <novo> --apply --author "Joao Silva"
    python tasks.py manifest-version --file data/contracts/tb_clientes.yaml
"""

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import yaml

MAJOR = "MAJOR"
MINOR = "MINOR"
PATCH = "PATCH"
NONE = "NONE"

_ORDEM = {NONE: 0, PATCH: 1, MINOR: 2, MAJOR: 3}

LOCK_DIR = ".lock"

# Campos de coluna que descrevem o dado (mudanca = PATCH), nao o contrato.
_CAMPOS_DESCRITIVOS = ("description", "sas_label", "business_rules", "regulatory_flags")

# Campos de raiz cuja mudanca e apenas documental.
_RAIZ_DESCRITIVA = ("description", "business_context", "owner", "steward", "sample_queries")


class Mudanca:
    """Uma diferenca entre o baseline e o Manifest atual."""

    def __init__(self, nivel: str, campo: str, detalhe: str):
        self.nivel = nivel
        self.campo = campo
        self.detalhe = detalhe

    def __repr__(self):
        return "Mudanca({}, {}, {})".format(self.nivel, self.campo, self.detalhe)

    def to_dict(self) -> dict:
        return {"nivel": self.nivel, "campo": self.campo, "detalhe": self.detalhe}


class ManifestVersioner:
    """Compara dois Manifests e deriva a proxima versao semantica."""

    # ── diff ──────────────────────────────────────────────────────────────────

    def diff(self, baseline: dict, atual: dict) -> list:
        """Lista de Mudanca entre dois manifests, ja classificadas por nivel."""
        mudancas = []
        mudancas += self._diff_schema(baseline, atual)
        mudancas += self._diff_source(baseline, atual)
        mudancas += self._diff_tolerancia(baseline, atual)
        mudancas += self._diff_descritivo(baseline, atual)
        return mudancas

    def _colunas(self, manifest: dict) -> dict:
        return {c.get("name"): c for c in (manifest.get("schema") or []) if c.get("name")}

    def _diff_schema(self, baseline: dict, atual: dict) -> list:
        antes, depois = self._colunas(baseline), self._colunas(atual)
        mudancas = []

        for nome in antes:
            if nome not in depois:
                mudancas.append(Mudanca(MAJOR, "schema.{}".format(nome), "coluna removida"))

        for nome, col in depois.items():
            if nome not in antes:
                nivel = MINOR if col.get("nullable", True) else MAJOR
                extra = "" if nivel == MINOR else " NOT NULL (quebra carga existente)"
                mudancas.append(Mudanca(nivel, "schema.{}".format(nome),
                                        "coluna nova{}".format(extra)))
                continue

            anterior = antes[nome]

            tipo_antes = str(anterior.get("type", "")).strip().lower()
            tipo_depois = str(col.get("type", "")).strip().lower()
            if tipo_antes != tipo_depois:
                mudancas.append(Mudanca(MAJOR, "schema.{}.type".format(nome),
                                        "{} -> {}".format(tipo_antes, tipo_depois)))

            null_antes = bool(anterior.get("nullable", True))
            null_depois = bool(col.get("nullable", True))
            if null_antes != null_depois:
                nivel = MAJOR if null_antes and not null_depois else MINOR
                mudancas.append(Mudanca(nivel, "schema.{}.nullable".format(nome),
                                        "{} -> {}".format(null_antes, null_depois)))

            pk_antes = bool(anterior.get("primary_key", False))
            pk_depois = bool(col.get("primary_key", False))
            if pk_antes != pk_depois:
                mudancas.append(Mudanca(MAJOR, "schema.{}.primary_key".format(nome),
                                        "{} -> {}".format(pk_antes, pk_depois)))

            for campo in _CAMPOS_DESCRITIVOS:
                if anterior.get(campo) != col.get(campo):
                    mudancas.append(Mudanca(PATCH, "schema.{}.{}".format(nome, campo),
                                            "alterado"))

        # Ordem das colunas importa para formato posicional e para CSV sem cabecalho.
        if list(antes) != list(depois) and set(antes) == set(depois):
            mudancas.append(Mudanca(MAJOR, "schema", "ordem das colunas alterada"))

        return mudancas

    def _diff_source(self, baseline: dict, atual: dict) -> list:
        antes = baseline.get("source") or {}
        depois = atual.get("source") or {}
        mudancas = []
        for campo in ("format", "delimiter", "encoding"):
            if antes.get(campo) != depois.get(campo):
                mudancas.append(Mudanca(MAJOR, "source.{}".format(campo),
                                        "{} -> {}".format(antes.get(campo), depois.get(campo))))
        for campo in ("system", "os", "update_frequency", "contact"):
            if antes.get(campo) != depois.get(campo):
                mudancas.append(Mudanca(PATCH, "source.{}".format(campo), "alterado"))
        return mudancas

    def _diff_tolerancia(self, baseline: dict, atual: dict) -> list:
        antes = baseline.get("tolerance") or {}
        depois = atual.get("tolerance") or {}
        mudancas = []

        # Afrouxar tolerancia e retrocompativel; restringir reprova carga que antes passava.
        for campo in ("max_null_pct", "max_reject_pct"):
            a, d = antes.get(campo), depois.get(campo)
            if a == d:
                continue
            if a is None or d is None:
                # Remover um limite declarado devolve a tolerancia ao default, que
                # pode ser mais estrito que o acordado: trata-se como quebra.
                nivel = MAJOR if d is None else MINOR
                mudancas.append(Mudanca(nivel, "tolerance.{}".format(campo),
                                        "{} -> {}".format(a, d)))
            else:
                nivel = MAJOR if float(d) < float(a) else MINOR
                mudancas.append(Mudanca(nivel, "tolerance.{}".format(campo),
                                        "{} -> {}".format(a, d)))

        a, d = bool(antes.get("allow_duplicates", False)), bool(depois.get("allow_duplicates", False))
        if a != d:
            nivel = MAJOR if a and not d else MINOR
            mudancas.append(Mudanca(nivel, "tolerance.allow_duplicates", "{} -> {}".format(a, d)))

        return mudancas

    def _diff_descritivo(self, baseline: dict, atual: dict) -> list:
        mudancas = []
        for campo in _RAIZ_DESCRITIVA:
            if baseline.get(campo) != atual.get(campo):
                mudancas.append(Mudanca(PATCH, campo, "alterado"))
        reg_antes = baseline.get("regulatory") or {}
        reg_depois = atual.get("regulatory") or {}
        if reg_antes.get("data_classification") != reg_depois.get("data_classification"):
            mudancas.append(Mudanca(MINOR, "regulatory.data_classification",
                                    "{} -> {}".format(reg_antes.get("data_classification"),
                                                      reg_depois.get("data_classification"))))
        if reg_antes.get("tags") != reg_depois.get("tags"):
            mudancas.append(Mudanca(PATCH, "regulatory.tags", "alterado"))
        return mudancas

    # ── versao ────────────────────────────────────────────────────────────────

    def nivel(self, mudancas: list) -> str:
        """O maior nivel entre as mudancas — MAJOR domina MINOR, que domina PATCH."""
        return max((m.nivel for m in mudancas), key=lambda n: _ORDEM[n], default=NONE)

    def parse(self, versao: str) -> tuple:
        partes = str(versao or "").split(".")
        if len(partes) != 3 or not all(p.isdigit() for p in partes):
            raise ValueError("Versao invalida no Manifest: {!r}".format(versao))
        return tuple(int(p) for p in partes)

    def proxima(self, versao_atual: str, nivel: str) -> str:
        major, minor, patch = self.parse(versao_atual)
        if nivel == MAJOR:
            return "{}.0.0".format(major + 1)
        if nivel == MINOR:
            return "{}.{}.0".format(major, minor + 1)
        if nivel == PATCH:
            return "{}.{}.{}".format(major, minor, patch + 1)
        return versao_atual

    def avaliar(self, baseline: dict, atual: dict) -> dict:
        """Diff + nivel + versao esperada, sem tocar em arquivo."""
        mudancas = self.diff(baseline, atual)
        nivel = self.nivel(mudancas)
        versao_base = baseline.get("version") or atual.get("version") or "0.0.0"
        esperada = self.proxima(versao_base, nivel)
        declarada = atual.get("version")
        return {
            "mudancas": mudancas,
            "nivel": nivel,
            "versao_baseline": versao_base,
            "versao_esperada": esperada,
            "versao_declarada": declarada,
            "conforme": declarada == esperada,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Baseline: git -> lock
# ─────────────────────────────────────────────────────────────────────────────

def carregar_yaml(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def baseline_do_git(path: Path, ref: str = "HEAD") -> dict:
    """Manifest como esta commitado. Devolve {} se nao houver git ou arquivo no ref."""
    path = Path(path)
    try:
        raiz = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=str(path.parent), capture_output=True, text=True, timeout=10,
        )
        if raiz.returncode != 0:
            return {}
        relativo = path.resolve().relative_to(Path(raiz.stdout.strip()).resolve())
        proc = subprocess.run(
            ["git", "show", "{}:{}".format(ref, relativo.as_posix())],
            cwd=raiz.stdout.strip(), capture_output=True, text=True, timeout=10,
        )
        if proc.returncode != 0 or not proc.stdout.strip():
            return {}
        return yaml.safe_load(proc.stdout) or {}
    except (OSError, ValueError, yaml.YAMLError, subprocess.SubprocessError):
        return {}


def caminho_lock(path: Path) -> Path:
    path = Path(path)
    return path.parent / LOCK_DIR / path.name


def baseline_do_lock(path: Path) -> dict:
    lock = caminho_lock(path)
    return carregar_yaml(lock) if lock.exists() else {}


def gravar_lock(path: Path, manifest: dict) -> Path:
    """Snapshot do contrato publicado, para quem roda sem git."""
    lock = caminho_lock(path)
    lock.parent.mkdir(parents=True, exist_ok=True)
    with open(lock, "w", encoding="utf-8") as f:
        f.write("# Snapshot do ultimo bump aplicado — baseline do diff quando nao ha git.\n"
                "# Gerado por src/manifest/manifest_version.py. Nao editar a mao.\n\n")
        yaml.dump(manifest, f, allow_unicode=True, sort_keys=False,
                  default_flow_style=False, width=120)
    return lock


def resolver_baseline(path: Path, baseline_explicito=None) -> tuple:
    """Devolve (manifest_baseline, origem). Origem vazia = sem baseline."""
    if baseline_explicito:
        return carregar_yaml(Path(baseline_explicito)), "arquivo:{}".format(baseline_explicito)
    do_git = baseline_do_git(path)
    if do_git:
        return do_git, "git:HEAD"
    do_lock = baseline_do_lock(path)
    if do_lock:
        return do_lock, "lock:{}".format(caminho_lock(path).as_posix())
    return {}, ""


# ─────────────────────────────────────────────────────────────────────────────
# Aplicacao do bump
# ─────────────────────────────────────────────────────────────────────────────

def aplicar_bump(path: Path, avaliacao: dict, autor: str, origem_baseline: str) -> str:
    """Grava a nova versao e o historico no proprio Manifest, e atualiza o lock."""
    path = Path(path)
    manifest = carregar_yaml(path)
    nova = avaliacao["versao_esperada"]

    entrada = {
        "version": nova,
        "previous_version": avaliacao["versao_baseline"],
        "level": avaliacao["nivel"],
        "date": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "author": autor,
        "baseline_source": origem_baseline,
        "changes": [m.to_dict() for m in avaliacao["mudancas"]],
    }

    manifest["version"] = nova

    # Contrato que muda volta para revisao humana: manter VALIDATED seria dizer
    # que o Steward aprovou uma versao que ele nunca viu.
    if manifest.get("manifest_status") == "VALIDATED":
        manifest["manifest_status"] = "DRAFT"
        manifest["validated_by"] = None
        manifest["validated_at"] = None
        entrada["revalidacao_requerida"] = True

    historico = list(manifest.get("version_history") or [])
    historico.append(entrada)
    manifest["version_history"] = historico

    with open(path, "w", encoding="utf-8") as f:
        f.write("# Manifesto: {}\n"
                "# Status: {}\n"
                "# Versao: {} ({} sobre {})\n\n".format(
                    manifest.get("table", ""),
                    manifest.get("manifest_status", "DRAFT"),
                    nova, avaliacao["nivel"], avaliacao["versao_baseline"]))
        yaml.dump(manifest, f, allow_unicode=True, sort_keys=False,
                  default_flow_style=False, width=120)

    gravar_lock(path, manifest)
    return nova


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def _imprimir(avaliacao: dict, origem: str) -> None:
    print("\n[VERSION] Baseline : {}".format(origem or "nenhum (primeira versao)"))
    print("[VERSION] Versao    : {} (declarada) | {} (baseline)".format(
        avaliacao["versao_declarada"], avaliacao["versao_baseline"]))
    print("[VERSION] Nivel     : {}".format(avaliacao["nivel"]))
    print("[VERSION] Esperada  : {}".format(avaliacao["versao_esperada"]))

    if not avaliacao["mudancas"]:
        print("\n  Nenhuma diferenca em relacao ao baseline.")
        return

    print("\n  Mudancas ({}):".format(len(avaliacao["mudancas"])))
    for m in sorted(avaliacao["mudancas"], key=lambda x: -_ORDEM[x.nivel]):
        print("    [{:<5}] {}: {}".format(m.nivel, m.campo, m.detalhe))


def main():
    parser = argparse.ArgumentParser(
        description="Deriva a versao semantica do Manifest a partir do diff de schema."
    )
    parser.add_argument("--file", required=True, help="Manifest YAML atual")
    parser.add_argument("--baseline", default=None,
                        help="Manifest de comparacao (default: git HEAD, depois o lock)")
    parser.add_argument("--apply", action="store_true",
                        help="Grava a nova versao e o version_history no arquivo")
    parser.add_argument("--author", default=None, help="Quem esta promovendo a versao")
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        print("[ERROR] Arquivo nao encontrado: {}".format(path))
        return 1

    atual = carregar_yaml(path)
    baseline, origem = resolver_baseline(path, args.baseline)

    if not baseline:
        print("\n[VERSION] Sem baseline (arquivo novo ou nao commitado).")
        print("          Versao declarada: {}".format(atual.get("version")))
        if args.apply:
            gravar_lock(path, atual)
            print("          Lock inicial gravado em {}".format(caminho_lock(path)))
        return 0

    versioner = ManifestVersioner()
    avaliacao = versioner.avaliar(baseline, atual)
    _imprimir(avaliacao, origem)

    if not args.apply:
        if avaliacao["conforme"]:
            print("\n[VERSION] OK: versao declarada corresponde ao diff.")
            return 0
        print("\n[VERSION] DIVERGENTE: declarada {}, esperada {}.".format(
            avaliacao["versao_declarada"], avaliacao["versao_esperada"]))
        print("          Rode com --apply --author \"Nome\" para corrigir.")
        return 1

    if not args.author:
        print("\n[ERROR] Informe --author \"Nome\" para registrar o bump no historico.")
        return 1

    if avaliacao["nivel"] == NONE:
        print("\n[VERSION] Nada a versionar: schema e metadados identicos ao baseline.")
        gravar_lock(path, atual)
        return 0

    era_validado = atual.get("manifest_status") == "VALIDATED"
    nova = aplicar_bump(path, avaliacao, args.author, origem)
    print("\n[VERSION] Versao promovida para {} ({}) por '{}'.".format(
        nova, avaliacao["nivel"], args.author))
    print("          Historico registrado em version_history.")
    if era_validado:
        print("          Status revertido para DRAFT: contrato alterado exige "
              "nova validacao do Steward.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
