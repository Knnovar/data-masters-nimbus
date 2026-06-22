"""
tests/test_storage.py - Testes para src/storage/storage.py
"""

import sys
import unittest
import tempfile
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.storage.storage import LocalStorage


def make_storage(base: Path) -> LocalStorage:
    layer_map = {l: base / l for l in
                 ["bronze","silver","gold","quarantine","contracts","metrics","reports"]}
    return LocalStorage(layer_map)


SAMPLE = pd.DataFrame({
    "id"   : ["A1", "A2", "A3"],
    "nome" : ["Ana", "Bruno", "Carla"],
    "valor": [10.0, 20.0, 30.0],
})


class TestReadWrite(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.s   = make_storage(self.tmp)

    def test_write_creates_file(self):
        self.s.write("bronze", "tb.csv", SAMPLE)
        self.assertTrue(self.s.exists("bronze", "tb.csv"))

    def test_write_read_roundtrip(self):
        self.s.write("bronze", "tb.csv", SAMPLE)
        loaded = self.s.read("bronze", "tb.csv")
        self.assertEqual(list(loaded.columns), list(SAMPLE.columns))
        self.assertEqual(len(loaded), len(SAMPLE))

    def test_write_overwrites(self):
        self.s.write("bronze", "tb.csv", SAMPLE)
        new = pd.DataFrame({"id": ["X1"], "nome": ["Xpto"], "valor": [99.0]})
        self.s.write("bronze", "tb.csv", new)
        loaded = self.s.read("bronze", "tb.csv")
        self.assertEqual(len(loaded), 1)

    def test_write_text(self):
        self.s.write_text("contracts", "tb.yaml", "table: tb_teste\n")
        self.assertTrue(self.s.exists("contracts", "tb.yaml"))

    def test_read_path_returns_path(self):
        self.s.write("bronze", "tb.csv", SAMPLE)
        path = self.s.read_path("bronze", "tb.csv")
        self.assertIsInstance(path, Path)
        self.assertTrue(path.exists())

    def test_unknown_layer_raises(self):
        with self.assertRaises(ValueError, msg="Camada desconhecida"):
            self.s.write("inexistente", "tb.csv", SAMPLE)


class TestListExists(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.s   = make_storage(self.tmp)

    def test_list_csv_files(self):
        self.s.write("bronze", "tb_a.csv", SAMPLE)
        self.s.write("bronze", "tb_b.csv", SAMPLE)
        files = self.s.list("bronze")
        self.assertIn("tb_a.csv", files)
        self.assertIn("tb_b.csv", files)

    def test_list_empty(self):
        self.assertEqual(self.s.list("silver"), [])

    def test_exists_true(self):
        self.s.write("bronze", "tb.csv", SAMPLE)
        self.assertTrue(self.s.exists("bronze", "tb.csv"))

    def test_exists_false(self):
        self.assertFalse(self.s.exists("bronze", "nao_existe.csv"))


class TestMove(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.s   = make_storage(self.tmp)

    def test_move_bronze_to_silver(self):
        self.s.write("bronze", "tb.csv", SAMPLE)
        self.s.move("tb.csv", "bronze", "silver")
        self.assertTrue(self.s.exists("silver", "tb.csv"))
        self.assertFalse(self.s.exists("bronze", "tb.csv"))

    def test_move_to_quarantine(self):
        self.s.write("bronze", "tb_bad.csv", SAMPLE)
        self.s.move("tb_bad.csv", "bronze", "quarantine")
        self.assertTrue(self.s.exists("quarantine", "tb_bad.csv"))
        self.assertFalse(self.s.exists("bronze", "tb_bad.csv"))

    def test_move_overwrites_destination(self):
        """Move deve sobrescrever arquivo existente no destino (Windows compat)."""
        self.s.write("bronze", "tb.csv", SAMPLE)
        old = pd.DataFrame({"id": ["OLD"]})
        self.s.write("silver", "tb.csv", old)
        self.s.move("tb.csv", "bronze", "silver")
        loaded = self.s.read("silver", "tb.csv")
        self.assertEqual(len(loaded), len(SAMPLE))


class TestValidatorIntegration(unittest.TestCase):
    """Testa o validator com o storage real."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.s   = make_storage(self.tmp)

    def test_validate_pass_scenario(self):
        import yaml
        from src.validation.validator import validate

        contract = {
            "table": "tb_t", "description": "T", "owner": "sq",
            "version": "1.0.0",
            "tolerance": {"max_null_pct": 20, "allow_duplicates": False},
            "schema": [
                {"name": "id",    "type": "string", "nullable": False, "primary_key": True},
                {"name": "valor", "type": "float",  "nullable": True},
            ],
        }
        df = pd.DataFrame({"id": ["A1","A2"], "valor": ["10.0","20.0"]})
        self.s.write("bronze", "tb_t.csv", df)
        self.s.write_text("contracts", "tb_t.yaml",
                          yaml.dump(contract, allow_unicode=True))

        result = validate(self.s, "tb_t.csv", "tb_t.yaml", "baseline")
        self.assertEqual(result.status, "PASS")
        self.assertEqual(result.rows_total, 2)

    def test_validate_dlq_missing_column(self):
        import yaml
        from src.validation.validator import validate

        contract = {
            "table": "tb_t", "description": "T", "owner": "sq",
            "version": "1.0.0",
            "tolerance": {"max_null_pct": 20, "allow_duplicates": False},
            "schema": [
                {"name": "id",     "type": "string", "nullable": False, "primary_key": True},
                {"name": "obrig",  "type": "string", "nullable": False},
            ],
        }
        df = pd.DataFrame({"id": ["A1"]})  # "obrig" ausente
        self.s.write("bronze", "tb_dlq.csv", df)
        self.s.write_text("contracts", "tb_dlq.yaml",
                          yaml.dump(contract, allow_unicode=True))

        result = validate(self.s, "tb_dlq.csv", "tb_dlq.yaml", "breaking")
        self.assertEqual(result.status, "DLQ")
        self.assertEqual(result.evolution_type, "BREAKING")


if __name__ == "__main__":
    unittest.main()
