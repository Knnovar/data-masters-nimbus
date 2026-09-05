"""tests/test_schema_utils.py — Testes para src/storage/schema_utils.py"""
import sys, unittest
from pathlib import Path
from types import SimpleNamespace
import pandas as pd
import pyarrow as pa

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.storage.schema_utils import (
    CAST_FAIL_THRESHOLD, apply_manifest_schema,
    build_parquet_metadata, manifest_to_arrow_schema,
)

def _col(name, type_, nullable=True, business_rules=None):
    return SimpleNamespace(name=name, type=type_, nullable=nullable, business_rules=business_rules or [])

def _contract(cols, status="VALIDATED", version="1.0.0", table="tb_test"):
    return SimpleNamespace(table=table, version=version, manifest_status=status, schema=cols)

class TestManifestToArrowSchema(unittest.TestCase):
    def test_string(self): self.assertEqual(manifest_to_arrow_schema(_contract([_col("n","string")])).field("n").type, pa.string())
    def test_integer(self): self.assertEqual(manifest_to_arrow_schema(_contract([_col("n","integer")])).field("n").type, pa.int64())
    def test_float(self): self.assertEqual(manifest_to_arrow_schema(_contract([_col("n","float")])).field("n").type, pa.float64())
    def test_boolean(self): self.assertEqual(manifest_to_arrow_schema(_contract([_col("n","boolean")])).field("n").type, pa.bool_())
    def test_date(self): self.assertEqual(manifest_to_arrow_schema(_contract([_col("n","date")])).field("n").type, pa.date32())
    def test_datetime(self): self.assertEqual(manifest_to_arrow_schema(_contract([_col("n","datetime")])).field("n").type, pa.timestamp("us"))
    def test_unknown_defaults_string(self): self.assertEqual(manifest_to_arrow_schema(_contract([_col("n","xml")])).field("n").type, pa.string())
    def test_nullable_false(self): self.assertFalse(manifest_to_arrow_schema(_contract([_col("n","integer",nullable=False)])).field("n").nullable)
    def test_extra_columns_as_string(self):
        s = manifest_to_arrow_schema(_contract([_col("id","integer")]), extra_columns=["nova"])
        self.assertIn("nova", s.names)
        self.assertEqual(s.field("nova").type, pa.string())
    def test_column_order(self):
        cols = [_col("b","float"),_col("a","string"),_col("c","integer")]
        self.assertEqual(manifest_to_arrow_schema(_contract(cols)).names, ["b","a","c"])
    def test_aliases_int(self):
        for alias in ("int","long"):
            self.assertEqual(manifest_to_arrow_schema(_contract([_col("n",alias)])).field("n").type, pa.int64())
    def test_aliases_float(self):
        for alias in ("double","decimal","numeric"):
            self.assertEqual(manifest_to_arrow_schema(_contract([_col("n",alias)])).field("n").type, pa.float64())

class TestCastInteger(unittest.TestCase):
    def _apply(self, values):
        df = pd.DataFrame({"id": values})
        return apply_manifest_schema(df, _contract([_col("id","integer")]))
    def test_clean_integers(self):
        df, _ = self._apply(["1","2","3"])
        self.assertEqual(str(df["id"].dtype), "Int64")
    def test_null_preserved(self):
        df, _ = self._apply(["1",None,"3"])
        self.assertTrue(pd.isna(df["id"].iloc[1]))
    def test_high_fail_rate_keeps_string(self):
        df, warns = self._apply(["1","abc","def","xyz"])
        self.assertIn(str(df["id"].dtype), ("object","str"))
        self.assertTrue(any("CAST_FAIL" in w for w in warns))
    def test_low_fail_rate_casts(self):
        values = [str(i) for i in range(99)] + ["abc"]
        df, _ = self._apply(values)
        self.assertEqual(str(df["id"].dtype), "Int64")

class TestCastFloat(unittest.TestCase):
    def _apply(self, values):
        df = pd.DataFrame({"v": values})
        return apply_manifest_schema(df, _contract([_col("v","float")]))
    def test_clean_floats(self):
        df, _ = self._apply(["1.5","2.3","10.0"])
        self.assertTrue(str(df["v"].dtype).startswith("float"))
    def test_high_fail_keeps_string(self):
        df, warns = self._apply(["1.0","abc","def","ghi"])
        self.assertIn(str(df["v"].dtype), ("object","str"))
        self.assertTrue(any("CAST_FAIL" in w for w in warns))

class TestCastBoolean(unittest.TestCase):
    def _apply(self, values):
        df = pd.DataFrame({"fl": values})
        return apply_manifest_schema(df, _contract([_col("fl","boolean")]))
    def test_sn(self):
        df, warns = self._apply(["S","N","S"])
        self.assertEqual(df["fl"].tolist(), [True,False,True])
        self.assertEqual(len(warns), 0)
    def test_01(self):
        df, _ = self._apply(["1","0","1"])
        self.assertEqual(df["fl"].tolist(), [True,False,True])
    def test_true_false(self):
        df, _ = self._apply(["True","False","true"])
        self.assertEqual(df["fl"].tolist(), [True,False,True])
    def test_null_preserved(self):
        df, _ = self._apply(["S",None,"N"])
        self.assertTrue(pd.isna(df["fl"].iloc[1]))
    def test_out_of_domain_low_rate_becomes_null(self):
        values = ["S","N"]*49 + ["X"]
        df = pd.DataFrame({"fl": values})
        result, _ = apply_manifest_schema(df, _contract([_col("fl","boolean")]))
        self.assertTrue(pd.isna(result["fl"].iloc[-1]))
    def test_high_fail_keeps_string(self):
        df, warns = self._apply(["X","Y","Z","W"])
        self.assertIn(str(df["fl"].dtype), ("object","str"))
        self.assertTrue(any("CAST_FAIL" in w for w in warns))

class TestCastDate(unittest.TestCase):
    def _apply(self, values, fmt=None):
        rules = ["Formato detectado: {}".format(fmt)] if fmt else []
        df = pd.DataFrame({"dt": values})
        return apply_manifest_schema(df, _contract([_col("dt","date",business_rules=rules)]))
    def test_br_format(self):
        from datetime import date
        df, warns = self._apply(["01/01/2024","15/06/2023"], fmt="%d/%m/%Y")
        self.assertEqual(df["dt"].iloc[0], date(2024,1,1))
        self.assertEqual(len(warns), 0)
    def test_iso_fallback(self):
        from datetime import date
        df, _ = self._apply(["2024-01-15","2023-06-30"])
        self.assertEqual(df["dt"].iloc[0], date(2024,1,15))
    def test_wrong_format_fallback_warning(self):
        df, warns = self._apply(["01/01/2024","15/06/2023"], fmt="%Y-%m-%d")
        self.assertTrue(any("DATE_FORMAT_FALLBACK" in w for w in warns))
    def test_unrecognized_keeps_string(self):
        df, warns = self._apply(["NAO_E_DATA_99","TAMBEM_NAO"])
        self.assertIn(str(df["dt"].dtype), ("object","str"))
        self.assertTrue(any("CAST_FAIL" in w for w in warns))
    def test_null_preserved(self):
        df, _ = self._apply(["2024-01-01", None])
        self.assertTrue(pd.isna(df["dt"].iloc[1]))

class TestCastDatetime(unittest.TestCase):
    def test_iso_datetime(self):
        df = pd.DataFrame({"ts": ["2024-01-15 10:30:00","2023-06-30 00:00:00"]})
        result, _ = apply_manifest_schema(df, _contract([_col("ts","datetime")]))
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(result["ts"]))

class TestApplyManifestSchema(unittest.TestCase):
    def test_extra_column_warning(self):
        df = pd.DataFrame({"id":["1"],"nova":["x"]})
        _, warns = apply_manifest_schema(df, _contract([_col("id","integer")]))
        self.assertTrue(any("EXTRA_COLUMN" in w and "nova" in w for w in warns))
    def test_missing_required_warning(self):
        df = pd.DataFrame({"outro":["x"]})
        _, warns = apply_manifest_schema(df, _contract([_col("id","integer",nullable=False)]))
        self.assertTrue(any("MISSING_REQUIRED" in w for w in warns))
    def test_missing_nullable_no_warning(self):
        df = pd.DataFrame({"outro":["x"]})
        _, warns = apply_manifest_schema(df, _contract([_col("id","integer",nullable=True)]))
        self.assertFalse(any("MISSING_REQUIRED" in w for w in warns))
    def test_original_not_mutated(self):
        df = pd.DataFrame({"id":["1","2"]})
        orig_dtype = df["id"].dtype
        apply_manifest_schema(df, _contract([_col("id","integer")]))
        self.assertEqual(df["id"].dtype, orig_dtype)
    def test_mixed_types(self):
        df = pd.DataFrame({"id":["1","2"],"nome":["Ana","Bruno"],"val":["100.5","200.0"],"fl":["S","N"]})
        result, warns = apply_manifest_schema(df, _contract([
            _col("id","integer"),_col("nome","string"),_col("val","float"),_col("fl","boolean")]))
        self.assertEqual(str(result["id"].dtype), "Int64")
        self.assertTrue(str(result["val"].dtype).startswith("float"))
        self.assertEqual(len(warns), 0)
    def test_unknown_type_warning(self):
        df = pd.DataFrame({"x":["a","b"]})
        result, warns = apply_manifest_schema(df, _contract([_col("x","xml")]))
        self.assertTrue(any("UNKNOWN_TYPE" in w for w in warns))

class TestBuildParquetMetadata(unittest.TestCase):
    def _str(self, c, warns=None):
        return {k.decode():v.decode() for k,v in build_parquet_metadata(c, warns or {}).items()}
    def test_validated(self):
        m = self._str(_contract([], status="VALIDATED", table="tb_c", version="2.0.0"))
        self.assertEqual(m["nimbus.schema_source"], "manifest_validated")
        self.assertEqual(m["nimbus.table"], "tb_c")
    def test_draft(self):
        m = self._str(_contract([], status="DRAFT"))
        self.assertEqual(m["nimbus.schema_source"], "manifest_draft")
    def test_warnings_count(self):
        m = self._str(_contract([]), warns=["W1","W2","W3"])
        self.assertEqual(m["nimbus.warnings_count"], "3")
    def test_all_bytes(self):
        for k,v in build_parquet_metadata(_contract([]), []).items():
            self.assertIsInstance(k, bytes); self.assertIsInstance(v, bytes)
    def test_generated_at_present(self):
        self.assertIn("nimbus.generated_at", self._str(_contract([])))
    def test_warnings_truncated_at_10(self):
        import json
        m = self._str(_contract([]), warns=["W{}".format(i) for i in range(20)])
        self.assertLessEqual(len(json.loads(m["nimbus.warnings"])), 10)

if __name__ == "__main__":
    unittest.main()
