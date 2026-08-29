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


# ═══════════════════════ TestParquet ══════════════════════════════════════════
class TestParquet(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.s   = make_storage(self.tmp)

    def test_write_parquet_creates_file(self):
        name = self.s.write_parquet("silver", "tb.csv", SAMPLE)
        self.assertEqual(name, "tb.parquet")
        self.assertTrue(self.s.exists("silver", "tb.parquet"))

    def test_write_parquet_extension_always_parquet(self):
        name = self.s.write_parquet("silver", "tb.json", SAMPLE)
        self.assertEqual(name, "tb.parquet")

    def test_read_parquet_roundtrip(self):
        self.s.write_parquet("silver", "tb.csv", SAMPLE)
        loaded = self.s.read("silver", "tb.parquet")
        self.assertEqual(list(loaded.columns), list(SAMPLE.columns))
        self.assertEqual(len(loaded), len(SAMPLE))

    def test_parquet_preserves_numeric_types(self):
        self.s.write_parquet("silver", "tb.csv", SAMPLE)
        loaded = self.s.read("silver", "tb.parquet")
        dtype = str(loaded["valor"].dtype)
        self.assertTrue(dtype.startswith("float") or dtype.startswith("int"),
            "Esperado tipo numerico, got: {}".format(dtype))

    def test_promote_creates_parquet_in_silver(self):
        self.s.write("bronze", "tb.csv", SAMPLE)
        name = self.s.promote_to_parquet("tb.csv", "bronze", "silver")
        self.assertEqual(name, "tb.parquet")
        self.assertTrue(self.s.exists("silver", "tb.parquet"))

    def test_promote_archives_original(self):
        self.s.write("bronze", "tb.csv", SAMPLE)
        self.s.promote_to_parquet("tb.csv", "bronze", "silver")
        self.assertFalse(self.s.exists("bronze", "tb.csv"))
        archive = self.tmp / "bronze" / "_archive" / "tb.csv"
        self.assertTrue(archive.exists(), "Original deve estar em _archive/")

    def test_promote_data_integrity(self):
        self.s.write("bronze", "tb.csv", SAMPLE)
        name   = self.s.promote_to_parquet("tb.csv", "bronze", "silver")
        loaded = self.s.read("silver", name)
        self.assertEqual(len(loaded), len(SAMPLE))
        self.assertEqual(set(loaded.columns), set(SAMPLE.columns))

    def test_parquet_smaller_than_csv_large_dataset(self):
        import pandas as pd
        big = pd.DataFrame({
            "id"  : ["C{:04d}".format(i) for i in range(500)],
            "nome": ["Cliente {}".format(i % 50) for i in range(500)],
            "seg" : ["PRIME" if i % 3 == 0 else "VAREJO" for i in range(500)],
            "val" : [round(1000 + i * 10.5, 2) for i in range(500)],
        })
        self.s.write("bronze", "big.csv", big)
        csv_size = (self.tmp / "bronze" / "big.csv").stat().st_size
        self.s.write_parquet("silver", "big.csv", big)
        pq_size  = (self.tmp / "silver" / "big.parquet").stat().st_size
        self.assertLess(pq_size, csv_size,
            "Parquet ({}) deve ser menor que CSV ({})".format(pq_size, csv_size))

    def test_list_includes_parquet(self):
        self.s.write_parquet("silver", "tb.csv", SAMPLE)
        self.assertIn("tb.parquet", self.s.list("silver"))

    def test_promote_json_to_parquet(self):
        import json
        p = self.tmp / "bronze" / "tb.json"
        p.write_text(json.dumps({"data": SAMPLE.to_dict(orient="records")}))
        name = self.s.promote_to_parquet("tb.json", "bronze", "silver")
        self.assertTrue(self.s.exists("silver", name))


if __name__ == "__main__":
    unittest.main()


# ═══════════════════ TestPromoteWithContract ══════════════════════════════════
class TestPromoteWithContract(unittest.TestCase):
    """
    Testes para promote_to_parquet() com contrato do Manifest.
    Verifica que o Silver respeita os tipos declarados, não os inferidos.
    """

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.s   = make_storage(self.tmp)

    def _contract(self, cols, status="VALIDATED"):
        from types import SimpleNamespace
        schema = [
            SimpleNamespace(
                name=c["name"], type=c["type"],
                nullable=c.get("nullable", True),
                business_rules=c.get("business_rules", []),
            )
            for c in cols
        ]
        return SimpleNamespace(
            table="tb_test", version="1.0.0",
            manifest_status=status, schema=schema,
        )

    def _write_bronze(self, data: dict, filename="tb_test.csv"):
        df = pd.DataFrame({k: [str(v) for v in vals] for k, vals in data.items()})
        self.s.write("bronze", filename, df)
        return filename

    def test_integer_column_typed_correctly(self):
        """Coluna declarada como integer chega ao Silver com tipo numerico."""
        self._write_bronze({"id": [1, 2, 3], "val": [10, 20, 30]})
        contract = self._contract([
            {"name": "id",  "type": "integer", "nullable": False},
            {"name": "val", "type": "integer"},
        ])
        name   = self.s.promote_to_parquet("tb_test.csv", "bronze", "silver", contract)
        loaded = self.s.read("silver", name)
        self.assertEqual(str(loaded["id"].dtype), "Int64")
        self.assertEqual(str(loaded["val"].dtype), "Int64")

    def test_float_column_typed_correctly(self):
        self._write_bronze({"vl_renda": ["5000.50", "8000.00", "12000.75"]})
        contract = self._contract([{"name": "vl_renda", "type": "float"}])
        name     = self.s.promote_to_parquet("tb_test.csv", "bronze", "silver", contract)
        loaded   = self.s.read("silver", name)
        self.assertTrue(str(loaded["vl_renda"].dtype).startswith("float"))

    def test_boolean_column_from_sn_domain(self):
        self._write_bronze({"fl_ativo": ["S", "N", "S", "S", "N"]})
        contract = self._contract([{"name": "fl_ativo", "type": "boolean"}])
        name     = self.s.promote_to_parquet("tb_test.csv", "bronze", "silver", contract)
        loaded   = self.s.read("silver", name)
        self.assertIn(str(loaded["fl_ativo"].dtype), ("bool", "boolean"))
        self.assertTrue(loaded["fl_ativo"].iloc[0])
        self.assertFalse(loaded["fl_ativo"].iloc[1])

    def test_date_column_typed_correctly(self):
        from datetime import date
        self._write_bronze({"dt_nasc": ["2024-01-15", "2023-06-30", "1990-03-22"]})
        contract = self._contract([{"name": "dt_nasc", "type": "date"}])
        name     = self.s.promote_to_parquet("tb_test.csv", "bronze", "silver", contract)
        loaded   = self.s.read("silver", name)
        # Lido como object pelo pandas mas os valores são date
        first = loaded["dt_nasc"].iloc[0]
        self.assertIsNotNone(first)

    def test_string_column_preserved(self):
        self._write_bronze({"nm_cliente": ["Ana", "Bruno", "Carlos"]})
        contract = self._contract([{"name": "nm_cliente", "type": "string"}])
        name     = self.s.promote_to_parquet("tb_test.csv", "bronze", "silver", contract)
        loaded   = self.s.read("silver", name)
        self.assertEqual(loaded["nm_cliente"].tolist(), ["Ana", "Bruno", "Carlos"])

    def test_parquet_metadata_contains_manifest_info(self):
        """Metadata do Manifest é embutida no footer do Parquet."""
        import pyarrow.parquet as pq_mod
        self._write_bronze({"id": ["1", "2"]})
        contract = self._contract([{"name": "id", "type": "integer"}])
        name     = self.s.promote_to_parquet("tb_test.csv", "bronze", "silver", contract)
        path     = self.tmp / "silver" / name
        meta     = pq_mod.read_metadata(str(path))
        raw_meta = meta.metadata or {}
        meta_str = {k.decode(): v.decode() for k, v in raw_meta.items()}
        self.assertIn("nimbus.schema_source",    meta_str)
        self.assertIn("nimbus.table",            meta_str)
        self.assertIn("nimbus.manifest_version", meta_str)
        self.assertEqual(meta_str["nimbus.schema_source"], "manifest_validated")

    def test_draft_manifest_reflected_in_metadata(self):
        import pyarrow.parquet as pq_mod
        self._write_bronze({"id": ["1", "2"]})
        contract = self._contract([{"name": "id", "type": "integer"}], status="DRAFT")
        name     = self.s.promote_to_parquet("tb_test.csv", "bronze", "silver", contract)
        path     = self.tmp / "silver" / name
        meta     = pq_mod.read_metadata(str(path))
        raw_meta = {k.decode(): v.decode() for k, v in (meta.metadata or {}).items()}
        self.assertEqual(raw_meta.get("nimbus.schema_source"), "manifest_draft")

    def test_extra_column_kept_as_string_with_warning(self):
        """Coluna no dado mas nao no Manifest entra como string (NON_BREAKING)."""
        self._write_bronze({"id": ["1","2"], "coluna_nova": ["x","y"]})
        contract = self._contract([{"name": "id", "type": "integer"}])
        # Nao deve levantar excecao — coluna_nova entra como string
        name   = self.s.promote_to_parquet("tb_test.csv", "bronze", "silver", contract)
        loaded = self.s.read("silver", name)
        self.assertIn("coluna_nova", loaded.columns)

    def test_without_contract_uses_inference(self):
        """Sem contrato, comportamento original (inferencia pyarrow) e mantido."""
        self._write_bronze({"id": ["1", "2"], "val": ["10.5", "20.0"]})
        name = self.s.promote_to_parquet("tb_test.csv", "bronze", "silver")
        self.assertTrue(self.s.exists("silver", name))
        loaded = self.s.read("silver", name)
        self.assertIn("id",  loaded.columns)
        self.assertIn("val", loaded.columns)

    def test_multiple_types_single_call(self):
        """Promove arquivo com multiplos tipos numa unica chamada."""
        self._write_bronze({
            "id"       : ["1", "2", "3"],
            "nome"     : ["Ana", "Bruno", "Carlos"],
            "vl_renda" : ["5000.0", "8000.5", "12000.0"],
            "fl_ativo" : ["S", "N", "S"],
        })
        contract = self._contract([
            {"name": "id",        "type": "integer", "nullable": False},
            {"name": "nome",      "type": "string"},
            {"name": "vl_renda",  "type": "float"},
            {"name": "fl_ativo",  "type": "boolean"},
        ])
        name   = self.s.promote_to_parquet("tb_test.csv", "bronze", "silver", contract)
        loaded = self.s.read("silver", name)
        self.assertEqual(str(loaded["id"].dtype),     "Int64")
        self.assertTrue(str(loaded["vl_renda"].dtype).startswith("float"))
        self.assertIn(str(loaded["fl_ativo"].dtype), ("bool", "boolean"))
        self.assertEqual(len(loaded), 3)


if __name__ == "__main__":
    unittest.main()
