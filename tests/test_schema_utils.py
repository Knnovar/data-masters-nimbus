"""
tests/test_schema_utils.py — Testes para src/storage/schema_utils.py

Cobre todos os casos de borda mapeados no planejamento:
  - Mapeamento de tipos Manifest -> PyArrow
  - Cast de integer, float, boolean, date, datetime, string
  - Threshold de falha de cast (CAST_FAIL_THRESHOLD)
  - Colunas extras (NON_BREAKING) e colunas ausentes (MISSING)
  - Metadata embutida no Parquet
  - Formatos de data com fallback
  - Domínios de boolean reconhecidos
"""

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from typing import List, Optional

import pandas as pd
import pyarrow as pa

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.storage.schema_utils import (
    CAST_FAIL_THRESHOLD,
    apply_manifest_schema,
    build_parquet_metadata,
    manifest_to_arrow_schema,
)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers para montar contratos de teste sem depender de DataContract real
# ─────────────────────────────────────────────────────────────────────────────

def _col(name, type_, nullable=True, business_rules=None):
    return SimpleNamespace(
        name           = name,
        type           = type_,
        nullable       = nullable,
        business_rules = business_rules or [],
    )


def _contract(cols, status="VALIDATED", version="1.0.0", table="tb_test"):
    return SimpleNamespace(
        table           = table,
        version         = version,
        manifest_status = status,
        schema          = cols,
    )


# ─────────────────────────────────────────────────────────────────────────────
# TestManifestToArrowSchema
# ─────────────────────────────────────────────────────────────────────────────

class TestManifestToArrowSchema(unittest.TestCase):

    def test_string_maps_to_pa_string(self):
        c = _contract([_col("nome", "string")])
        s = manifest_to_arrow_schema(c)
        self.assertEqual(s.field("nome").type, pa.string())

    def test_integer_maps_to_int64(self):
        c = _contract([_col("id", "integer")])
        s = manifest_to_arrow_schema(c)
        self.assertEqual(s.field("id").type, pa.int64())

    def test_float_maps_to_float64(self):
        c = _contract([_col("val", "float")])
        s = manifest_to_arrow_schema(c)
        self.assertEqual(s.field("val").type, pa.float64())

    def test_boolean_maps_to_bool(self):
        c = _contract([_col("fl", "boolean")])
        s = manifest_to_arrow_schema(c)
        self.assertEqual(s.field("fl").type, pa.bool_())

    def test_date_maps_to_date32(self):
        c = _contract([_col("dt", "date")])
        s = manifest_to_arrow_schema(c)
        self.assertEqual(s.field("dt").type, pa.date32())

    def test_datetime_maps_to_timestamp(self):
        c = _contract([_col("ts", "datetime")])
        s = manifest_to_arrow_schema(c)
        self.assertEqual(s.field("ts").type, pa.timestamp("us"))

    def test_unknown_type_defaults_to_string(self):
        c = _contract([_col("x", "xml")])
        s = manifest_to_arrow_schema(c)
        self.assertEqual(s.field("x").type, pa.string())

    def test_nullable_false_reflected_in_schema(self):
        c = _contract([_col("id", "integer", nullable=False)])
        s = manifest_to_arrow_schema(c)
        self.assertFalse(s.field("id").nullable)

    def test_extra_columns_added_as_string(self):
        c = _contract([_col("id", "integer")])
        s = manifest_to_arrow_schema(c, extra_columns=["coluna_nova"])
        self.assertIn("coluna_nova", s.names)
        self.assertEqual(s.field("coluna_nova").type, pa.string())

    def test_column_order_matches_manifest(self):
        cols = [_col("b", "float"), _col("a", "string"), _col("c", "integer")]
        c    = _contract(cols)
        s    = manifest_to_arrow_schema(c)
        self.assertEqual(s.names, ["b", "a", "c"])

    def test_aliases_int_maps_to_int64(self):
        for alias in ("int", "long"):
            c = _contract([_col("x", alias)])
            s = manifest_to_arrow_schema(c)
            self.assertEqual(s.field("x").type, pa.int64(),
                             "Alias '{}' deve mapear para int64".format(alias))

    def test_aliases_float_maps_to_float64(self):
        for alias in ("double", "decimal", "numeric"):
            c = _contract([_col("x", alias)])
            s = manifest_to_arrow_schema(c)
            self.assertEqual(s.field("x").type, pa.float64(),
                             "Alias '{}' deve mapear para float64".format(alias))


# ─────────────────────────────────────────────────────────────────────────────
# TestCastInteger
# ─────────────────────────────────────────────────────────────────────────────

class TestCastInteger(unittest.TestCase):

    def _apply(self, values, nullable=True):
        df = pd.DataFrame({"id": values})
        c  = _contract([_col("id", "integer", nullable=nullable)])
        return apply_manifest_schema(df, c)

    def test_clean_integers_cast_correctly(self):
        df, warns = self._apply(["1", "2", "3"])
        self.assertEqual(str(df["id"].dtype), "Int64")
        self.assertEqual(df["id"].tolist(), [1, 2, 3])

    def test_null_values_preserved(self):
        df, warns = self._apply(["1", None, "3"])
        self.assertTrue(pd.isna(df["id"].iloc[1]))

    def test_empty_string_becomes_null(self):
        df, warns = self._apply(["1", "", "3"])
        self.assertTrue(pd.isna(df["id"].iloc[1]))

    def test_high_fail_rate_keeps_string(self):
        # 50% de falha > CAST_FAIL_THRESHOLD
        df, warns = self._apply(["1", "abc", "3", "xyz"])
        self.assertIn(str(df["id"].dtype), ("object", "str"),
                         "Alta falha de cast deve manter como string")
        self.assertTrue(any("CAST_FAIL" in w for w in warns))

    def test_low_fail_rate_casts_with_warning(self):
        # 1 em 100 falha < CAST_FAIL_THRESHOLD
        values = ["{}".format(i) for i in range(99)] + ["abc"]
        df, warns = self._apply(values)
        self.assertEqual(str(df["id"].dtype), "Int64")


# ─────────────────────────────────────────────────────────────────────────────
# TestCastFloat
# ─────────────────────────────────────────────────────────────────────────────

class TestCastFloat(unittest.TestCase):

    def _apply(self, values):
        df = pd.DataFrame({"val": values})
        c  = _contract([_col("val", "float")])
        return apply_manifest_schema(df, c)

    def test_clean_floats(self):
        df, _ = self._apply(["1.5", "2.3", "10.0"])
        self.assertTrue(str(df["val"].dtype).startswith("float"))

    def test_null_preserved(self):
        df, _ = self._apply(["1.5", None, "3.0"])
        self.assertTrue(pd.isna(df["val"].iloc[1]))

    def test_high_fail_rate_keeps_string(self):
        df, warns = self._apply(["1.0", "abc", "def", "ghi"])
        self.assertIn(str(df["val"].dtype), ("object", "str"))
        self.assertTrue(any("CAST_FAIL" in w for w in warns))


# ─────────────────────────────────────────────────────────────────────────────
# TestCastBoolean
# ─────────────────────────────────────────────────────────────────────────────

class TestCastBoolean(unittest.TestCase):

    def _apply(self, values):
        df = pd.DataFrame({"fl": values})
        c  = _contract([_col("fl", "boolean")])
        return apply_manifest_schema(df, c)

    def test_sn_domain(self):
        df, warns = self._apply(["S", "N", "S"])
        self.assertEqual(df["fl"].tolist(), [True, False, True])
        self.assertEqual(len(warns), 0)

    def test_zero_one_domain(self):
        df, _ = self._apply(["1", "0", "1"])
        self.assertEqual(df["fl"].tolist(), [True, False, True])

    def test_true_false_domain(self):
        df, _ = self._apply(["True", "False", "true"])
        self.assertEqual(df["fl"].tolist(), [True, False, True])

    def test_yes_no_domain(self):
        df, _ = self._apply(["yes", "no", "YES"])
        self.assertEqual(df["fl"].tolist(), [True, False, True])

    def test_null_preserved(self):
        df, _ = self._apply(["S", None, "N"])
        self.assertTrue(pd.isna(df["fl"].iloc[1]))

    def test_out_of_domain_becomes_null(self):
        # 1 valor fora do dominio em 100 fica abaixo do threshold (1% < 5%)
        # O cast ocorre e o valor fora do dominio vira None/pd.NA
        values = ["S", "N"] * 49 + ["X"]   # 99 validos + 1 invalido
        df = pd.DataFrame({"fl": values})
        c  = _contract([_col("fl", "boolean")])
        result, warns = apply_manifest_schema(df, c)
        self.assertTrue(pd.isna(result["fl"].iloc[-1]),
            "Valor fora do dominio boolean deve virar null quando fail_rate < threshold")

    def test_high_fail_rate_keeps_string(self):
        # Todos os valores fora do domínio
        df, warns = self._apply(["X", "Y", "Z", "W"])
        self.assertIn(str(df["fl"].dtype), ("object", "str"))
        self.assertTrue(any("CAST_FAIL" in w for w in warns))


# ─────────────────────────────────────────────────────────────────────────────
# TestCastDate
# ─────────────────────────────────────────────────────────────────────────────

class TestCastDate(unittest.TestCase):

    def _apply(self, values, fmt=None):
        rules = ["Formato detectado: {}".format(fmt)] if fmt else []
        df    = pd.DataFrame({"dt": values})
        c     = _contract([_col("dt", "date", business_rules=rules)])
        return apply_manifest_schema(df, c)

    def test_br_format_with_declared_format(self):
        df, warns = self._apply(["01/01/2024", "15/06/2023"], fmt="%d/%m/%Y")
        from datetime import date
        self.assertEqual(df["dt"].iloc[0], date(2024, 1, 1))
        self.assertEqual(len(warns), 0)

    def test_iso_format_fallback(self):
        df, warns = self._apply(["2024-01-15", "2023-06-30"])
        from datetime import date
        self.assertEqual(df["dt"].iloc[0], date(2024, 1, 15))

    def test_wrong_declared_format_falls_back_with_warning(self):
        # Declara %Y-%m-%d mas dado está em %d/%m/%Y
        df, warns = self._apply(["01/01/2024", "15/06/2023"], fmt="%Y-%m-%d")
        self.assertTrue(any("DATE_FORMAT_FALLBACK" in w for w in warns))
        from datetime import date
        self.assertEqual(df["dt"].iloc[0], date(2024, 1, 1))

    def test_unrecognized_format_keeps_string(self):
        # Valores que nenhum parser de data consegue interpretar
        df, warns = self._apply(["NAO_E_DATA_99", "TAMBEM_NAO_E_DATA"])
        self.assertIn(str(df["dt"].dtype), ("object", "str"))
        self.assertTrue(any("CAST_FAIL" in w for w in warns))

    def test_null_preserved(self):
        df, _ = self._apply(["2024-01-01", None])
        self.assertTrue(pd.isna(df["dt"].iloc[1]))


# ─────────────────────────────────────────────────────────────────────────────
# TestCastDatetime
# ─────────────────────────────────────────────────────────────────────────────

class TestCastDatetime(unittest.TestCase):

    def test_iso_datetime_cast(self):
        df = pd.DataFrame({"ts": ["2024-01-15 10:30:00", "2023-06-30 00:00:00"]})
        c  = _contract([_col("ts", "datetime")])
        result, warns = apply_manifest_schema(df, c)
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(result["ts"]))


# ─────────────────────────────────────────────────────────────────────────────
# TestApplyManifestSchema — comportamentos de borda
# ─────────────────────────────────────────────────────────────────────────────

class TestApplyManifestSchema(unittest.TestCase):

    def test_extra_column_generates_warning(self):
        """Coluna no dado mas não no Manifest -> WARNING EXTRA_COLUMN."""
        df = pd.DataFrame({"id": ["1"], "coluna_nova": ["x"]})
        c  = _contract([_col("id", "integer")])
        _, warns = apply_manifest_schema(df, c)
        self.assertTrue(any("EXTRA_COLUMN" in w and "coluna_nova" in w
                            for w in warns))

    def test_missing_required_column_generates_warning(self):
        """Coluna not-nullable no Manifest mas ausente no dado -> WARNING MISSING."""
        df = pd.DataFrame({"outro": ["x"]})
        c  = _contract([_col("id", "integer", nullable=False)])
        _, warns = apply_manifest_schema(df, c)
        self.assertTrue(any("MISSING_REQUIRED" in w for w in warns))

    def test_missing_nullable_column_no_warning(self):
        """Coluna nullable ausente no dado não gera warning."""
        df = pd.DataFrame({"outro": ["x"]})
        c  = _contract([_col("id", "integer", nullable=True)])
        _, warns = apply_manifest_schema(df, c)
        self.assertFalse(any("MISSING_REQUIRED" in w for w in warns))

    def test_original_df_not_mutated(self):
        """apply_manifest_schema não altera o DataFrame original."""
        df = pd.DataFrame({"id": ["1", "2"]})
        c  = _contract([_col("id", "integer")])
        original_dtype = df["id"].dtype
        apply_manifest_schema(df, c)
        self.assertEqual(df["id"].dtype, original_dtype)

    def test_multiple_columns_mixed_types(self):
        """Múltiplas colunas com tipos diferentes todas convertidas corretamente."""
        df = pd.DataFrame({
            "id"  : ["1", "2"],
            "nome": ["Ana", "Bruno"],
            "val" : ["100.5", "200.0"],
            "fl"  : ["S", "N"],
        })
        c = _contract([
            _col("id",   "integer"),
            _col("nome", "string"),
            _col("val",  "float"),
            _col("fl",   "boolean"),
        ])
        result, warns = apply_manifest_schema(df, c)
        self.assertEqual(str(result["id"].dtype),   "Int64")
        self.assertIn(str(result["nome"].dtype), ("object", "str"))
        self.assertTrue(str(result["val"].dtype).startswith("float"))
        self.assertEqual(str(result["fl"].dtype),   "boolean")
        self.assertEqual(len(warns), 0)

    def test_unknown_type_keeps_string_with_warning(self):
        df = pd.DataFrame({"x": ["a", "b"]})
        c  = _contract([_col("x", "xml")])
        result, warns = apply_manifest_schema(df, c)
        self.assertIn(str(result["x"].dtype), ("object", "str"))
        self.assertTrue(any("UNKNOWN_TYPE" in w for w in warns))


# ─────────────────────────────────────────────────────────────────────────────
# TestBuildParquetMetadata
# ─────────────────────────────────────────────────────────────────────────────

class TestBuildParquetMetadata(unittest.TestCase):

    def _meta_str(self, contract, warnings=None):
        raw = build_parquet_metadata(contract, warnings or [])
        return {k.decode(): v.decode() for k, v in raw.items()}

    def test_validated_manifest_reflected(self):
        c    = _contract([], status="VALIDATED", table="tb_clientes", version="2.0.0")
        meta = self._meta_str(c)
        self.assertEqual(meta["nimbus.schema_source"],    "manifest_validated")
        self.assertEqual(meta["nimbus.table"],            "tb_clientes")
        self.assertEqual(meta["nimbus.manifest_version"], "2.0.0")

    def test_draft_manifest_reflected(self):
        c    = _contract([], status="DRAFT")
        meta = self._meta_str(c)
        self.assertEqual(meta["nimbus.schema_source"], "manifest_draft")

    def test_warnings_count_stored(self):
        c    = _contract([])
        meta = self._meta_str(c, warnings=["W1", "W2", "W3"])
        self.assertEqual(meta["nimbus.warnings_count"], "3")

    def test_warnings_list_stored_as_json(self):
        import json
        c    = _contract([])
        meta = self._meta_str(c, warnings=["W1", "W2"])
        self.assertIn("nimbus.warnings", meta)
        parsed = json.loads(meta["nimbus.warnings"])
        self.assertIn("W1", parsed)

    def test_all_keys_are_bytes(self):
        c   = _contract([])
        raw = build_parquet_metadata(c, [])
        for k, v in raw.items():
            self.assertIsInstance(k, bytes)
            self.assertIsInstance(v, bytes)

    def test_generated_at_is_present(self):
        c    = _contract([])
        meta = self._meta_str(c)
        self.assertIn("nimbus.generated_at", meta)

    def test_more_than_10_warnings_truncated(self):
        import json
        c       = _contract([])
        many_ws = ["W{}".format(i) for i in range(20)]
        meta    = self._meta_str(c, warnings=many_ws)
        parsed  = json.loads(meta["nimbus.warnings"])
        self.assertLessEqual(len(parsed), 10)


if __name__ == "__main__":
    unittest.main()
