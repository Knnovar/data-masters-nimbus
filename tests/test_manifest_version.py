"""
tests/test_manifest_version.py — Versionamento semantico do Manifest por diff de schema.

O que estes testes garantem:
  - quebra de contrato (coluna removida, tipo alterado, NOT NULL novo) vira MAJOR;
  - mudanca retrocompativel (coluna nova nullable, tolerancia afrouxada) vira MINOR;
  - mudanca so de documentacao vira PATCH;
  - o maior nivel domina quando ha varias mudancas juntas;
  - --apply grava versao, historico e lock;
  - o baseline cai para o lock quando nao ha git;
  - o validator bloqueia promocao de contrato com versao desatualizada.
"""

import sys
import tempfile
import unittest
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.manifest.manifest_validator import ManifestValidator
from src.manifest.manifest_version import (
    MAJOR,
    MINOR,
    NONE,
    PATCH,
    ManifestVersioner,
    aplicar_bump,
    baseline_do_lock,
    caminho_lock,
    gravar_lock,
    resolver_baseline,
)


def manifest_base(**overrides) -> dict:
    base = {
        "table": "tb_clientes",
        "description": "Cadastro de clientes",
        "owner": "Dados PF",
        "version": "1.2.3",
        "manifest_status": "VALIDATED",
        "business_context": "Base cadastral",
        "steward": {"name": "Joao Silva", "email": "joao@banco.com"},
        "regulatory": {"tags": ["LGPD"], "data_classification": "confidential"},
        "source": {"format": "csv", "delimiter": ";", "encoding": "utf-8", "system": "CRM"},
        "tolerance": {"max_null_pct": 20.0, "allow_duplicates": False},
        "schema": [
            {"name": "cd_cliente", "type": "string", "nullable": False,
             "primary_key": True, "description": "Codigo"},
            {"name": "vl_renda_mensal", "type": "double", "nullable": True,
             "description": "Renda"},
        ],
    }
    base.update(overrides)
    return base


class TestNivelDeMudanca(unittest.TestCase):

    def setUp(self):
        self.v = ManifestVersioner()
        self.antes = manifest_base()

    def _nivel(self, depois):
        return self.v.nivel(self.v.diff(self.antes, depois))

    def test_sem_mudanca_e_none(self):
        self.assertEqual(self._nivel(manifest_base()), NONE)

    def test_coluna_removida_e_major(self):
        depois = manifest_base()
        depois["schema"] = depois["schema"][:1]
        self.assertEqual(self._nivel(depois), MAJOR)

    def test_tipo_alterado_e_major(self):
        depois = manifest_base()
        depois["schema"][1]["type"] = "string"
        self.assertEqual(self._nivel(depois), MAJOR)

    def test_nullable_apertado_e_major(self):
        depois = manifest_base()
        depois["schema"][1]["nullable"] = False
        self.assertEqual(self._nivel(depois), MAJOR)

    def test_nullable_afrouxado_e_minor(self):
        depois = manifest_base()
        depois["schema"][0]["nullable"] = True
        self.assertEqual(self._nivel(depois), MINOR)

    def test_primary_key_alterada_e_major(self):
        depois = manifest_base()
        depois["schema"][1]["primary_key"] = True
        self.assertEqual(self._nivel(depois), MAJOR)

    def test_coluna_nova_nullable_e_minor(self):
        depois = manifest_base()
        depois["schema"].append({"name": "nm_cliente", "type": "string", "nullable": True})
        self.assertEqual(self._nivel(depois), MINOR)

    def test_coluna_nova_not_null_e_major(self):
        depois = manifest_base()
        depois["schema"].append({"name": "nm_cliente", "type": "string", "nullable": False})
        self.assertEqual(self._nivel(depois), MAJOR)

    def test_ordem_das_colunas_e_major(self):
        depois = manifest_base()
        depois["schema"] = list(reversed(depois["schema"]))
        self.assertEqual(self._nivel(depois), MAJOR)

    def test_formato_da_origem_e_major(self):
        depois = manifest_base()
        depois["source"]["delimiter"] = ","
        self.assertEqual(self._nivel(depois), MAJOR)

    def test_tolerancia_restringida_e_major(self):
        depois = manifest_base()
        depois["tolerance"]["max_null_pct"] = 5.0
        self.assertEqual(self._nivel(depois), MAJOR)

    def test_tolerancia_afrouxada_e_minor(self):
        depois = manifest_base()
        depois["tolerance"]["max_null_pct"] = 50.0
        self.assertEqual(self._nivel(depois), MINOR)

    def test_tolerancia_removida_e_major(self):
        depois = manifest_base()
        depois["tolerance"]["max_reject_pct"] = None
        self.antes["tolerance"]["max_reject_pct"] = 1.0
        self.assertEqual(self._nivel(depois), MAJOR)

    def test_tolerancia_declarada_pela_primeira_vez_e_minor(self):
        depois = manifest_base()
        depois["tolerance"]["max_reject_pct"] = 1.0
        self.assertEqual(self._nivel(depois), MINOR)

    def test_descricao_e_patch(self):
        depois = manifest_base(description="Cadastro de clientes pessoa fisica")
        self.assertEqual(self._nivel(depois), PATCH)

    def test_business_rules_da_coluna_e_patch(self):
        depois = manifest_base()
        depois["schema"][0]["business_rules"] = ["unico"]
        self.assertEqual(self._nivel(depois), PATCH)

    def test_maior_nivel_domina(self):
        depois = manifest_base(description="outra")
        depois["schema"].append({"name": "nm_cliente", "type": "string", "nullable": True})
        depois["schema"][1]["type"] = "string"
        self.assertEqual(self._nivel(depois), MAJOR)


class TestCalculoDaVersao(unittest.TestCase):

    def setUp(self):
        self.v = ManifestVersioner()

    def test_major_zera_minor_e_patch(self):
        self.assertEqual(self.v.proxima("1.2.3", MAJOR), "2.0.0")

    def test_minor_zera_patch(self):
        self.assertEqual(self.v.proxima("1.2.3", MINOR), "1.3.0")

    def test_patch_incrementa(self):
        self.assertEqual(self.v.proxima("1.2.3", PATCH), "1.2.4")

    def test_none_preserva(self):
        self.assertEqual(self.v.proxima("1.2.3", NONE), "1.2.3")

    def test_versao_invalida_levanta(self):
        with self.assertRaises(ValueError):
            self.v.proxima("1.2", MAJOR)

    def test_avaliar_marca_divergencia(self):
        antes = manifest_base()
        depois = manifest_base()
        depois["schema"][1]["type"] = "string"
        aval = self.v.avaliar(antes, depois)
        self.assertEqual(aval["versao_esperada"], "2.0.0")
        self.assertFalse(aval["conforme"])

    def test_avaliar_marca_conforme(self):
        antes = manifest_base()
        depois = manifest_base(version="2.0.0")
        depois["schema"][1]["type"] = "string"
        self.assertTrue(self.v.avaliar(antes, depois)["conforme"])


class TestAplicacaoEmArquivo(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.path = self.dir / "tb_clientes.yaml"

    def tearDown(self):
        self.tmp.cleanup()

    def _grava(self, manifest, path=None):
        alvo = path or self.path
        alvo.write_text(yaml.dump(manifest, allow_unicode=True, sort_keys=False),
                        encoding="utf-8")
        return alvo

    def test_apply_grava_versao_historico_e_lock(self):
        antes = manifest_base()
        depois = manifest_base()
        depois["schema"][1]["type"] = "string"
        self._grava(depois)

        aval = ManifestVersioner().avaliar(antes, depois)
        nova = aplicar_bump(self.path, aval, "Maria Souza", "teste")

        gravado = yaml.safe_load(self.path.read_text(encoding="utf-8"))
        self.assertEqual(nova, "2.0.0")
        self.assertEqual(gravado["version"], "2.0.0")

        historico = gravado["version_history"]
        self.assertEqual(len(historico), 1)
        self.assertEqual(historico[0]["level"], MAJOR)
        self.assertEqual(historico[0]["previous_version"], "1.2.3")
        self.assertEqual(historico[0]["author"], "Maria Souza")
        self.assertTrue(historico[0]["changes"])

        self.assertTrue(caminho_lock(self.path).exists())
        self.assertEqual(baseline_do_lock(self.path)["version"], "2.0.0")

    def test_bump_reverte_validated_para_draft(self):
        antes = manifest_base()
        depois = manifest_base()
        depois["schema"][1]["type"] = "string"
        self._grava(depois)

        aval = ManifestVersioner().avaliar(antes, depois)
        aplicar_bump(self.path, aval, "Maria Souza", "teste")

        gravado = yaml.safe_load(self.path.read_text(encoding="utf-8"))
        self.assertEqual(gravado["manifest_status"], "DRAFT")
        self.assertIsNone(gravado["validated_by"])
        self.assertTrue(gravado["version_history"][0]["revalidacao_requerida"])

    def test_historico_acumula_sem_perder_entradas(self):
        self._grava(manifest_base())
        aval = ManifestVersioner().avaliar(manifest_base(), manifest_base(description="x"))
        aplicar_bump(self.path, aval, "Maria", "teste")
        aplicar_bump(self.path, aval, "Maria", "teste")
        gravado = yaml.safe_load(self.path.read_text(encoding="utf-8"))
        self.assertEqual(len(gravado["version_history"]), 2)

    def test_baseline_cai_para_o_lock_sem_git(self):
        # Diretorio temporario nao e repositorio git: sobra o lock.
        gravar_lock(self.path, manifest_base())
        self._grava(manifest_base(version="1.2.3"))
        baseline, origem = resolver_baseline(self.path)
        self.assertTrue(origem.startswith("lock:"))
        self.assertEqual(baseline["version"], "1.2.3")

    def test_baseline_explicito_tem_prioridade(self):
        outro = self._grava(manifest_base(version="9.9.9"), self.dir / "outro.yaml")
        self._grava(manifest_base())
        baseline, origem = resolver_baseline(self.path, str(outro))
        self.assertEqual(baseline["version"], "9.9.9")
        self.assertTrue(origem.startswith("arquivo:"))

    def test_sem_baseline_devolve_vazio(self):
        self._grava(manifest_base())
        baseline, origem = resolver_baseline(self.path)
        self.assertEqual(baseline, {})
        self.assertEqual(origem, "")


class TestBloqueioNoValidator(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.path = self.dir / "tb_clientes.yaml"
        self.validator = ManifestValidator()

    def tearDown(self):
        self.tmp.cleanup()

    def _grava(self, manifest):
        self.path.write_text(yaml.dump(manifest, allow_unicode=True, sort_keys=False),
                             encoding="utf-8")

    def _completo(self, **overrides):
        m = manifest_base(**overrides)
        for col in m["schema"]:
            col.setdefault("description", "descricao")
        m["sample_queries"] = [{"description": "amostra", "sql": "SELECT 1"}]
        return m

    def test_sem_baseline_nao_bloqueia(self):
        self._grava(self._completo())
        self.assertTrue(self.validator.check_version(self.path)["ok"])

    def test_schema_alterado_sem_bump_bloqueia(self):
        gravar_lock(self.path, self._completo())
        alterado = self._completo()
        alterado["schema"][1]["type"] = "string"
        self._grava(alterado)

        resultado = self.validator.check_version(self.path)
        self.assertFalse(resultado["ok"])
        self.assertIn("2.0.0", resultado["motivo"])
        self.assertFalse(self.validator.promote(self.path, "Joao Silva"))
        # O arquivo nao pode ter sido promovido pelo caminho bloqueado.
        self.assertEqual(
            yaml.safe_load(self.path.read_text(encoding="utf-8"))["version"], "1.2.3")

    def test_schema_alterado_com_bump_promove(self):
        gravar_lock(self.path, self._completo())
        alterado = self._completo(version="2.0.0")
        alterado["schema"][1]["type"] = "string"
        self._grava(alterado)

        self.assertTrue(self.validator.check_version(self.path)["ok"])
        self.assertTrue(self.validator.promote(self.path, "Joao Silva"))

    def test_skip_version_check_promove_mesmo_divergente(self):
        gravar_lock(self.path, self._completo())
        alterado = self._completo()
        alterado["schema"][1]["type"] = "string"
        self._grava(alterado)
        self.assertTrue(
            self.validator.promote(self.path, "Joao Silva", skip_version_check=True))


if __name__ == "__main__":
    unittest.main(verbosity=2)
