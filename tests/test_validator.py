"""
tests/test_validator.py - Testes para src/validation/validator.py
"""

import sys
import unittest
import tempfile
import yaml
import pandas as pd
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.validation.validator import validate, ValidationResult
from src.storage.storage import LocalStorage


def make_storage(base: Path) -> LocalStorage:
    layer_map = {l: base / l for l in
                 ["bronze","silver","gold","quarantine","contracts","metrics","reports"]}
    return LocalStorage(layer_map)


BASE_CONTRACT = {
    "table": "tb_t", "description": "Teste", "owner": "sq",
    "version": "1.0.0",
    "tolerance": {"max_null_pct": 20, "allow_duplicates": False},
    "schema": [
        {"name": "id",    "type": "string", "nullable": False, "primary_key": True},
        {"name": "nome",  "type": "string", "nullable": False},
        {"name": "valor", "type": "float",  "nullable": True},
    ],
}


class TestPass(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.s   = make_storage(self.tmp)
        self.s.write_text("contracts", "tb_t.yaml",
                          yaml.dump(BASE_CONTRACT, allow_unicode=True))

    def test_valid_data_returns_pass(self):
        df = pd.DataFrame({"id": ["A1","A2"], "nome": ["Ana","Bruno"], "valor": ["10.0","20.0"]})
        self.s.write("bronze", "tb_t.csv", df)
        r = validate(self.s, "tb_t.csv", "tb_t.yaml", "baseline")
        self.assertEqual(r.status, "PASS")
        self.assertEqual(r.rows_total, 2)
        self.assertEqual(r.duplicate_count, 0)

    def test_pass_has_draft_warning(self):
        df = pd.DataFrame({"id": ["A1"], "nome": ["Ana"], "valor": ["10.0"]})
        self.s.write("bronze", "tb_t.csv", df)
        r = validate(self.s, "tb_t.csv", "tb_t.yaml", "baseline")
        draft_warns = [w for w in r.warnings if "DRAFT" in w]
        self.assertEqual(len(draft_warns), 1)


class TestWarning(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.s   = make_storage(self.tmp)
        self.s.write_text("contracts", "tb_t.yaml",
                          yaml.dump(BASE_CONTRACT, allow_unicode=True))

    def test_duplicates_cause_warning(self):
        df = pd.DataFrame({"id": ["A1","A1","A2"],
                           "nome": ["Ana","Ana","Bruno"],
                           "valor": ["10.0","10.0","20.0"]})
        self.s.write("bronze", "tb_t.csv", df)
        r = validate(self.s, "tb_t.csv", "tb_t.yaml", "baseline")
        self.assertEqual(r.status, "WARNING")
        self.assertEqual(r.duplicate_count, 1)

    def test_null_required_column_causes_warning(self):
        df = pd.DataFrame({"id": ["A1","A2",None],
                           "nome": ["Ana","Bruno","Carla"],
                           "valor": ["10.0",None,"30.0"]})
        self.s.write("bronze", "tb_t.csv", df)
        r = validate(self.s, "tb_t.csv", "tb_t.yaml", "baseline")
        self.assertEqual(r.status, "WARNING")
        self.assertIn("id", r.null_violations)

    def test_extra_column_is_non_breaking(self):
        df = pd.DataFrame({"id": ["A1"], "nome": ["Ana"], "valor": ["10.0"],
                           "nova_col": ["x"]})
        self.s.write("bronze", "tb_t.csv", df)
        r = validate(self.s, "tb_t.csv", "tb_t.yaml", "non_breaking")
        self.assertEqual(r.status, "WARNING")
        self.assertEqual(r.evolution_type, "NON_BREAKING")


class TestDLQ(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.s   = make_storage(self.tmp)
        self.s.write_text("contracts", "tb_t.yaml",
                          yaml.dump(BASE_CONTRACT, allow_unicode=True))

    def test_missing_required_column_causes_dlq(self):
        df = pd.DataFrame({"id": ["A1"], "valor": ["10.0"]})  # nome ausente
        self.s.write("bronze", "tb_t.csv", df)
        r = validate(self.s, "tb_t.csv", "tb_t.yaml", "breaking")
        self.assertEqual(r.status, "DLQ")
        self.assertEqual(r.evolution_type, "BREAKING")
        self.assertGreater(len(r.issues), 0)

    def test_missing_pk_causes_dlq(self):
        df = pd.DataFrame({"nome": ["Ana"], "valor": ["10.0"]})  # id ausente
        self.s.write("bronze", "tb_t.csv", df)
        r = validate(self.s, "tb_t.csv", "tb_t.yaml", "breaking")
        self.assertEqual(r.status, "DLQ")

    def test_dlq_file_written_to_quarantine(self):
        df = pd.DataFrame({"nome": ["Ana"]})
        self.s.write("bronze", "tb_t.csv", df)
        validate(self.s, "tb_t.csv", "tb_t.yaml", "breaking")
        self.assertTrue(self.s.exists("quarantine", "tb_t.csv"))

    def test_invalid_contract_causes_dlq(self):
        self.s.write_text("contracts", "bad.yaml", "table: tb_t\n")
        df = pd.DataFrame({"id": ["A1"]})
        self.s.write("bronze", "tb_t.csv", df)
        r = validate(self.s, "tb_t.csv", "bad.yaml", "baseline")
        self.assertEqual(r.status, "DLQ")


class TestValidationResult(unittest.TestCase):

    def test_defaults(self):
        r = ValidationResult(table="tb_t", status="PASS")
        self.assertEqual(r.scenario, "baseline")
        self.assertIsNone(r.evolution_type)
        self.assertEqual(r.issues, [])
        self.assertEqual(r.warnings, [])
        self.assertEqual(r.rows_total, 0)

    def test_to_dict(self):
        r = ValidationResult(table="tb_t", status="PASS", rows_total=100)
        d = r.to_dict()
        self.assertEqual(d["table"], "tb_t")
        self.assertEqual(d["rows_total"], 100)


if __name__ == "__main__":
    unittest.main()
