"""
tests/test_manifest.py - Testes para src/manifest/
"""

import sys
import unittest
import tempfile
import yaml
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.manifest.extractor_base import ExtractorBase
from src.manifest.manifest_writer import ManifestWriter
from src.manifest.manifest_validator import ManifestValidator


DRAFT = {
    "table": "tb_teste", "description": "Tabela de teste.",
    "owner": "squad", "version": "1.0.0", "manifest_status": "DRAFT",
    "source": {"system": "SIS_X", "format": "csv", "encoding": "utf-8",
               "os": "unix", "update_frequency": "daily", "contact": "squad@b.com"},
    "regulatory": {"tags": ["LGPD"], "data_classification": "confidential"},
    "steward": {"name": "Joao Silva", "email": "joao@banco.com"},
    "business_context": "Contexto de negocio preenchido.",
    "tolerance": {"max_null_pct": 20, "allow_duplicates": False},
    "schema": [
        {"name": "id",  "type": "string", "nullable": False, "primary_key": True,
         "description": "Chave primaria.", "regulatory_flags": [], "business_rules": []},
        {"name": "cpf", "type": "string", "nullable": False,
         "description": "CPF do cliente.", "regulatory_flags": ["LGPD_SENSITIVE"], "business_rules": []},
    ],
    "sample_queries": [{"description": "Contagem", "sql": "SELECT COUNT(*) FROM tb_teste"}],
    "dependencies": [],
}

INCOMPLETE = {
    "table": "tb_incompleto", "description": "# TODO: preencher",
    "owner": "squad", "version": "1.0.0", "manifest_status": "DRAFT",
    "source": {"system": "# TODO: sistema", "format": "csv", "encoding": "utf-8",
               "os": "# TODO: os", "update_frequency": "daily", "contact": "# TODO: email"},
    "regulatory": {"tags": ["# TODO: revisar"], "data_classification": "internal"},
    "steward": {"name": "# TODO: nome", "email": "# TODO: email"},
    "business_context": "# TODO: descrever",
    "tolerance": {"max_null_pct": 20, "allow_duplicates": False},
    "schema": [
        {"name": "id", "type": "string", "nullable": False, "primary_key": True,
         "description": "# TODO: descrever", "regulatory_flags": [], "business_rules": []},
    ],
    "sample_queries": [],
}


class ConcreteExtractor(ExtractorBase):
    def extract(self, file_path, table_name): return {}
    def supported_formats(self): return [".test"]


class TestExtractorBaseHeuristic(unittest.TestCase):

    def setUp(self):
        self.ext = ConcreteExtractor()

    def test_cpf_detects_lgpd(self):
        self.assertIn("LGPD_SENSITIVE", self.ext._detect_regulatory_flags("nr_cpf_cnpj", "CPF"))

    def test_nome_detects_lgpd(self):
        self.assertIn("LGPD_SENSITIVE", self.ext._detect_regulatory_flags("nm_cliente", "NOME"))

    def test_renda_detects_scr(self):
        self.assertIn("SCR_CANDIDATE", self.ext._detect_regulatory_flags("vl_renda", "RENDA"))

    def test_senha_detects_restricted(self):
        self.assertIn("RESTRICTED", self.ext._detect_regulatory_flags("cd_senha", "SENHA"))

    def test_clean_column_no_flags(self):
        self.assertEqual(self.ext._detect_regulatory_flags("dt_cadastro", "DATA"), [])

    def test_table_tags_aggregation(self):
        cols = [{"regulatory_flags": ["LGPD_SENSITIVE"]}, {"regulatory_flags": ["SCR_CANDIDATE"]}]
        tags = self.ext._detect_table_regulatory_tags(cols)
        self.assertIn("LGPD", tags)
        self.assertIn("SCR", tags)
        self.assertIn("BACEN_4658", tags)

    def test_normalize_spaces(self):
        self.assertEqual(self.ext._normalize_column_name("CD CLIENTE"), "cd_cliente")

    def test_normalize_camel(self):
        self.assertEqual(self.ext._normalize_column_name("CdCliente"), "cd_cliente")

    def test_normalize_already_snake(self):
        self.assertEqual(self.ext._normalize_column_name("cd_cliente"), "cd_cliente")

    def test_normalize_special_chars(self):
        result = self.ext._normalize_column_name("CD-CLIENTE/BANCO")
        self.assertNotIn(" ", result)
        self.assertNotIn("/", result)
        self.assertNotIn("-", result)


class TestManifestWriter(unittest.TestCase):

    def setUp(self):
        self.writer  = ManifestWriter()
        self.tmp_dir = Path(tempfile.mkdtemp())

    def test_writes_yaml_file(self):
        path = self.writer.write(DRAFT.copy(), self.tmp_dir / "tb.yaml")
        self.assertTrue(path.exists())

    def test_written_file_is_valid_yaml(self):
        path = self.writer.write(DRAFT.copy(), self.tmp_dir / "tb.yaml")
        data = yaml.safe_load(open(path, encoding="utf-8"))
        self.assertEqual(data["table"], "tb_teste")

    def test_validated_creates_draft_parallel(self):
        validated = {**DRAFT, "manifest_status": "VALIDATED"}
        path = self.writer.write(validated, self.tmp_dir / "tb_v.yaml")
        # Tenta gravar novamente — deve criar _draft.yaml
        draft_path = self.writer.write(DRAFT.copy(), path)
        self.assertIn("draft", draft_path.name)
        self.assertTrue(path.exists())

    def test_overwrite_draft(self):
        path = self.writer.write(DRAFT.copy(), self.tmp_dir / "tb_d.yaml")
        self.writer.write({**DRAFT, "description": "Atualizado"}, path, overwrite=True)
        data = yaml.safe_load(open(path, encoding="utf-8"))
        self.assertEqual(data["description"], "Atualizado")

    def test_missing_required_fields_raises(self):
        with self.assertRaises(ValueError):
            self.writer.write({"table": "tb_x"}, self.tmp_dir / "bad.yaml")

    def test_empty_schema_raises(self):
        with self.assertRaises(ValueError):
            self.writer.write({**DRAFT, "schema": []}, self.tmp_dir / "bad2.yaml")


class TestManifestValidator(unittest.TestCase):

    def setUp(self):
        self.validator = ManifestValidator()
        self.tmp_dir   = Path(tempfile.mkdtemp())

    def _write(self, manifest, name="tb.yaml"):
        path = self.tmp_dir / name
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(manifest, f, allow_unicode=True)
        return path

    def test_complete_manifest_ready(self):
        result = self.validator.check(self._write(DRAFT))
        self.assertTrue(result["ready"])
        self.assertEqual(len(result["pending"]), 0)

    def test_incomplete_has_pending(self):
        result = self.validator.check(self._write(INCOMPLETE))
        self.assertFalse(result["ready"])
        self.assertGreater(len(result["pending"]), 0)

    def test_todo_in_description_blocks(self):
        result = self.validator.check(self._write(INCOMPLETE))
        fields = [p["field"] for p in result["pending"]]
        self.assertIn("description", fields)

    def test_promote_complete_manifest(self):
        path = self._write(DRAFT, "tb_promote.yaml")
        ok   = self.validator.promote(path, "Joao Silva")
        self.assertTrue(ok)
        data = yaml.safe_load(open(path, encoding="utf-8"))
        self.assertEqual(data["manifest_status"], "VALIDATED")
        self.assertEqual(data["validated_by"], "Joao Silva")
        self.assertIsNotNone(data["validated_at"])

    def test_promote_incomplete_fails(self):
        path = self._write(INCOMPLETE, "tb_incomplete.yaml")
        ok   = self.validator.promote(path, "Joao")
        self.assertFalse(ok)
        data = yaml.safe_load(open(path, encoding="utf-8"))
        self.assertEqual(data["manifest_status"], "DRAFT")

    def test_missing_sample_queries_is_warning_not_error(self):
        no_q   = {**DRAFT, "sample_queries": []}
        result = self.validator.check(self._write(no_q, "tb_nq.yaml"))
        pending_fields = [p["field"] for p in result["pending"]]
        self.assertNotIn("sample_queries", pending_fields)
        self.assertTrue(any("sample_queries" in w for w in result["warnings"]))


if __name__ == "__main__":
    unittest.main()
