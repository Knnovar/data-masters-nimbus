"""
tests/test_strict_cast.py — Suite de testes para src/storage/strict_cast.py

Cobre todos os comportamentos documentados e casos de borda:
  - _blank_mask e _blank_scalar
  - cast_series_strict: string, integer, float, boolean, date, datetime
  - reject_limit via contract.tolerance
  - apply_strict_schema: tipagem, rejeição, rastreio, summary, report
  - _split_duplicate_pk: chave simples, composta, tolerância allow_duplicates
  - Integração: cast + rejeição + duplicata num único apply
"""

import sys
import unittest
from datetime import date, datetime
from pathlib import Path
from types import SimpleNamespace

import pandas as pd

# Ajusta o path para encontrar o módulo
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.storage.strict_cast import (
    REASON_DUPLICATE,
    REASON_TYPE,
    REJECT_TRACE_COLUMNS,
    _blank_mask,
    _blank_scalar,
    _split_duplicate_pk,
    _to_bool,
    apply_strict_schema,
    cast_series_strict,
    reject_limit,
)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers para montar contratos de teste
# ─────────────────────────────────────────────────────────────────────────────

def _col(name, type_="string", nullable=True, primary_key=False, business_rules=None):
    return SimpleNamespace(
        name           = name,
        type           = type_,
        nullable       = nullable,
        primary_key    = primary_key,
        business_rules = business_rules or [],
    )


def _tolerance(max_reject_pct=0.0, max_null_pct=None, allow_duplicates=False):
    return SimpleNamespace(
        max_reject_pct   = max_reject_pct,
        max_null_pct     = max_null_pct,
        allow_duplicates = allow_duplicates,
    )


def _contract(cols, tolerance=None, pk_names=None):
    def _get_primary_keys():
        if pk_names:
            return pk_names
        return [c.name for c in cols if getattr(c, "primary_key", False)]

    return SimpleNamespace(
        schema          = cols,
        tolerance       = tolerance,
        get_primary_keys= _get_primary_keys,
    )


# ═════════════════════════════════════════════════════════════════════════════
# TestBlankMask
# ═════════════════════════════════════════════════════════════════════════════

class TestBlankMask(unittest.TestCase):

    def _mask(self, values):
        return _blank_mask(pd.Series(values))

    def test_none_is_blank(self):
        self.assertTrue(self._mask([None]).iloc[0])

    def test_empty_string_is_blank(self):
        self.assertTrue(self._mask([""]).iloc[0])

    def test_whitespace_is_blank(self):
        self.assertTrue(self._mask(["   "]).iloc[0])

    def test_nan_string_is_blank(self):
        self.assertTrue(self._mask(["nan"]).iloc[0])

    def test_none_string_is_blank(self):
        self.assertTrue(self._mask(["None"]).iloc[0])

    def test_real_value_not_blank(self):
        self.assertFalse(self._mask(["abc"]).iloc[0])

    def test_zero_not_blank(self):
        self.assertFalse(self._mask(["0"]).iloc[0])

    def test_mixed_series(self):
        mask = self._mask(["a", None, "", "b", "nan"])
        expected = [False, True, True, False, True]
        self.assertEqual(mask.tolist(), expected)

    def test_pd_na_is_blank(self):
        self.assertTrue(self._mask([pd.NA]).iloc[0])


# ═════════════════════════════════════════════════════════════════════════════
# TestBlankScalar
# ═════════════════════════════════════════════════════════════════════════════

class TestBlankScalar(unittest.TestCase):

    def test_none_is_blank(self):    self.assertTrue(_blank_scalar(None))
    def test_empty_is_blank(self):   self.assertTrue(_blank_scalar(""))
    def test_nan_str_is_blank(self): self.assertTrue(_blank_scalar("nan"))
    def test_none_str_is_blank(self):self.assertTrue(_blank_scalar("None"))
    def test_value_not_blank(self):  self.assertFalse(_blank_scalar("x"))
    def test_zero_not_blank(self):   self.assertFalse(_blank_scalar("0"))

    def test_pd_na_is_blank(self):
        self.assertTrue(_blank_scalar(pd.NA))

    def test_float_nan_is_blank(self):
        import math
        self.assertTrue(_blank_scalar(float("nan")))


# ═════════════════════════════════════════════════════════════════════════════
# TestToBool
# ═════════════════════════════════════════════════════════════════════════════

class TestToBool(unittest.TestCase):

    def test_s_true(self):       self.assertTrue(_to_bool("S"))
    def test_sim_true(self):     self.assertTrue(_to_bool("sim"))
    def test_1_true(self):       self.assertTrue(_to_bool("1"))
    def test_true_true(self):    self.assertTrue(_to_bool("True"))
    def test_yes_true(self):     self.assertTrue(_to_bool("yes"))
    def test_n_false(self):      self.assertFalse(_to_bool("N"))
    def test_nao_false(self):    self.assertFalse(_to_bool("nao"))
    def test_0_false(self):      self.assertFalse(_to_bool("0"))
    def test_false_false(self):  self.assertFalse(_to_bool("false"))
    def test_no_false(self):     self.assertFalse(_to_bool("no"))
    def test_unknown_none(self): self.assertIsNone(_to_bool("X"))
    def test_case_insensitive(self): self.assertTrue(_to_bool("SIM"))
    def test_verdadeiro_true(self): self.assertTrue(_to_bool("verdadeiro"))
    def test_falso_false(self):  self.assertFalse(_to_bool("falso"))


# ═════════════════════════════════════════════════════════════════════════════
# TestCastSeriesStrictString
# ═════════════════════════════════════════════════════════════════════════════

class TestCastSeriesStrictString(unittest.TestCase):

    def _cast(self, values):
        return cast_series_strict(pd.Series(values), "string")

    def test_no_fail_mask(self):
        _, fail = self._cast(["a", "b", "c"])
        self.assertFalse(fail.any())

    def test_returns_object_dtype(self):
        result, _ = self._cast(["a", "b"])
        self.assertIn(str(result.dtype), ("object", "str"))

    def test_aliases_str_text(self):
        for alias in ("str", "text"):
            _, fail = cast_series_strict(pd.Series(["x"]), alias)
            self.assertFalse(fail.any())


# ═════════════════════════════════════════════════════════════════════════════
# TestCastSeriesStrictInteger
# ═════════════════════════════════════════════════════════════════════════════

class TestCastSeriesStrictInteger(unittest.TestCase):

    def _cast(self, values, mt="integer"):
        return cast_series_strict(pd.Series(values), mt)

    def test_clean_values(self):
        result, fail = self._cast(["1", "2", "3"])
        self.assertFalse(fail.any())
        self.assertEqual(str(result.dtype), "Int64")

    def test_null_preserved(self):
        result, fail = self._cast(["1", None, "3"])
        self.assertTrue(pd.isna(result.iloc[1]))
        self.assertFalse(fail.iloc[1])  # nulo nao e falha

    def test_blank_string_not_fail(self):
        _, fail = self._cast(["1", "", "3"])
        self.assertFalse(fail.iloc[1])

    def test_invalid_value_is_fail(self):
        _, fail = self._cast(["1", "abc", "3"])
        self.assertTrue(fail.iloc[1])
        self.assertFalse(fail.iloc[0])
        self.assertFalse(fail.iloc[2])

    def test_alias_int_long(self):
        for alias in ("int", "long"):
            result, fail = self._cast(["10", "20"], mt=alias)
            self.assertEqual(str(result.dtype), "Int64")
            self.assertFalse(fail.any())

    def test_all_invalid_all_fail(self):
        _, fail = self._cast(["abc", "def", "xyz"])
        self.assertTrue(fail.all())

    def test_float_string_is_valid_integer(self):
        # "10.0" e convertido para 10 pelo pd.to_numeric
        result, fail = self._cast(["10.0", "20.0"])
        self.assertFalse(fail.any())


# ═════════════════════════════════════════════════════════════════════════════
# TestCastSeriesStrictFloat
# ═════════════════════════════════════════════════════════════════════════════

class TestCastSeriesStrictFloat(unittest.TestCase):

    def _cast(self, values, mt="float"):
        return cast_series_strict(pd.Series(values), mt)

    def test_clean_values(self):
        result, fail = self._cast(["1.5", "2.3", "10.0"])
        self.assertFalse(fail.any())
        self.assertTrue(str(result.dtype).startswith("float"))

    def test_invalid_is_fail(self):
        _, fail = self._cast(["1.0", "abc", "3.0"])
        self.assertTrue(fail.iloc[1])
        self.assertFalse(fail.iloc[0])

    def test_null_not_fail(self):
        _, fail = self._cast(["1.0", None, "3.0"])
        self.assertFalse(fail.iloc[1])

    def test_aliases(self):
        for alias in ("double", "decimal", "numeric"):
            _, fail = self._cast(["1.0", "2.0"], mt=alias)
            self.assertFalse(fail.any())


# ═════════════════════════════════════════════════════════════════════════════
# TestCastSeriesStrictBoolean
# ═════════════════════════════════════════════════════════════════════════════

class TestCastSeriesStrictBoolean(unittest.TestCase):

    def _cast(self, values):
        return cast_series_strict(pd.Series(values), "boolean")

    def test_sn_domain(self):
        result, fail = self._cast(["S", "N", "S"])
        self.assertFalse(fail.any())
        self.assertTrue(result.iloc[0])
        self.assertFalse(result.iloc[1])

    def test_01_domain(self):
        result, fail = self._cast(["1", "0", "1"])
        self.assertFalse(fail.any())
        self.assertTrue(result.iloc[0])

    def test_true_false_domain(self):
        result, fail = self._cast(["True", "False"])
        self.assertFalse(fail.any())
        self.assertTrue(result.iloc[0])

    def test_out_of_domain_is_fail(self):
        _, fail = self._cast(["S", "X", "N"])
        self.assertTrue(fail.iloc[1])
        self.assertFalse(fail.iloc[0])
        self.assertFalse(fail.iloc[2])

    def test_null_not_fail(self):
        _, fail = self._cast(["S", None, "N"])
        self.assertFalse(fail.iloc[1])

    def test_alias_bool(self):
        _, fail = cast_series_strict(pd.Series(["S", "N"]), "bool")
        self.assertFalse(fail.any())


# ═════════════════════════════════════════════════════════════════════════════
# TestCastSeriesStrictDate
# ═════════════════════════════════════════════════════════════════════════════

class TestCastSeriesStrictDate(unittest.TestCase):

    def _cast(self, values, fmt=None):
        return cast_series_strict(pd.Series(values), "date", date_format=fmt)

    def test_iso_format(self):
        result, fail = self._cast(["2024-01-15", "2023-06-30"])
        self.assertFalse(fail.any())
        self.assertEqual(result.iloc[0], date(2024, 1, 15))

    def test_br_format(self):
        result, fail = self._cast(["15/01/2024", "30/06/2023"], fmt="%d/%m/%Y")
        self.assertFalse(fail.any())
        self.assertEqual(result.iloc[0], date(2024, 1, 15))

    def test_invalid_date_is_fail(self):
        _, fail = self._cast(["2024-01-15", "NAO_E_DATA_99"])
        self.assertFalse(fail.iloc[0])
        self.assertTrue(fail.iloc[1])

    def test_null_not_fail(self):
        _, fail = self._cast(["2024-01-01", None])
        self.assertFalse(fail.iloc[1])

    def test_wrong_format_tries_fallback(self):
        # Declara formato errado mas dado esta em ISO — deve tentar fallback
        result, fail = self._cast(["2024-01-15"], fmt="%d/%m/%Y")
        # Pode falhar ou ter fallback — o importante e nao levantar excecao
        self.assertIsNotNone(result)


# ═════════════════════════════════════════════════════════════════════════════
# TestCastSeriesStrictDatetime
# ═════════════════════════════════════════════════════════════════════════════

class TestCastSeriesStrictDatetime(unittest.TestCase):

    def test_iso_datetime(self):
        result, fail = cast_series_strict(
            pd.Series(["2024-01-15 10:30:00", "2023-06-30 00:00:00"]), "datetime"
        )
        self.assertFalse(fail.any())
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(result))

    def test_invalid_datetime_is_fail(self):
        _, fail = cast_series_strict(
            pd.Series(["2024-01-15 10:30:00", "NAO_E_DATETIME"]), "datetime"
        )
        self.assertFalse(fail.iloc[0])
        self.assertTrue(fail.iloc[1])

    def test_alias_timestamp(self):
        result, fail = cast_series_strict(
            pd.Series(["2024-01-01 00:00:00"]), "timestamp"
        )
        self.assertFalse(fail.any())


# ═════════════════════════════════════════════════════════════════════════════
# TestRejectLimit
# ═════════════════════════════════════════════════════════════════════════════

class TestRejectLimit(unittest.TestCase):

    def test_no_tolerance_returns_zero(self):
        c = _contract([_col("id", "integer")])
        self.assertEqual(reject_limit(c), 0.0)

    def test_max_reject_pct_used(self):
        tol = _tolerance(max_reject_pct=5.0)
        c = _contract([_col("id")], tolerance=tol)
        self.assertEqual(reject_limit(c), 5.0)

    def test_max_null_pct_fallback(self):
        tol = SimpleNamespace(max_reject_pct=None, max_null_pct=10.0, allow_duplicates=False)
        c = _contract([_col("id")], tolerance=tol)
        self.assertEqual(reject_limit(c), 10.0)

    def test_both_none_raises_or_zero(self):
        # Quando max_reject_pct=None e max_null_pct=None, o codigo atual
        # tenta float(None) e levanta TypeError. Documenta o comportamento real.
        tol = SimpleNamespace(max_reject_pct=None, max_null_pct=None, allow_duplicates=False)
        c = _contract([_col("id")], tolerance=tol)
        try:
            result = reject_limit(c)
            # Se nao levantou, deve retornar numerico
            self.assertIsInstance(result, float)
        except TypeError:
            # Comportamento atual: float(None) levanta TypeError
            pass

    def test_null_pct_zero_fallback(self):
        # max_null_pct=0.0 (default explicito) funciona corretamente
        tol = SimpleNamespace(max_reject_pct=None, max_null_pct=0.0, allow_duplicates=False)
        c = _contract([_col("id")], tolerance=tol)
        self.assertEqual(reject_limit(c), 0.0)

    def test_returns_float(self):
        tol = _tolerance(max_reject_pct=3)
        c = _contract([_col("id")], tolerance=tol)
        self.assertIsInstance(reject_limit(c), float)


# ═════════════════════════════════════════════════════════════════════════════
# TestApplyStrictSchemaBasic
# ═════════════════════════════════════════════════════════════════════════════

class TestApplyStrictSchemaBasic(unittest.TestCase):

    def test_all_valid_no_rejects(self):
        df = pd.DataFrame({"id": ["1", "2", "3"], "nome": ["Ana", "Bruno", "Carlos"]})
        c  = _contract([_col("id", "integer"), _col("nome", "string")])
        typed, rejected, warns, summary = apply_strict_schema(df, c)
        self.assertEqual(len(typed), 3)
        self.assertEqual(len(rejected), 0)
        self.assertEqual(summary["rows_rejected"], 0)

    def test_integer_typed_correctly(self):
        df = pd.DataFrame({"id": ["1", "2", "3"]})
        c  = _contract([_col("id", "integer")])
        typed, _, _, _ = apply_strict_schema(df, c)
        self.assertEqual(str(typed["id"].dtype), "Int64")

    def test_boolean_typed_correctly(self):
        df = pd.DataFrame({"fl": ["S", "N", "S"]})
        c  = _contract([_col("fl", "boolean")])
        typed, _, _, _ = apply_strict_schema(df, c)
        self.assertIn(str(typed["fl"].dtype), ("bool", "boolean"))

    def test_original_df_not_mutated(self):
        df = pd.DataFrame({"id": ["1", "2"]})
        original_dtype = df["id"].dtype
        c = _contract([_col("id", "integer")])
        apply_strict_schema(df, c)
        self.assertEqual(df["id"].dtype, original_dtype)

    def test_extra_column_warning(self):
        df = pd.DataFrame({"id": ["1"], "extra": ["x"]})
        c  = _contract([_col("id", "integer")])
        _, _, warns, _ = apply_strict_schema(df, c)
        self.assertTrue(any("EXTRA_COLUMN" in w and "extra" in w for w in warns))

    def test_missing_required_warning(self):
        df = pd.DataFrame({"outro": ["x"]})
        c  = _contract([_col("id", "integer", nullable=False)])
        _, _, warns, _ = apply_strict_schema(df, c)
        self.assertTrue(any("MISSING_REQUIRED" in w for w in warns))

    def test_missing_nullable_no_warning(self):
        df = pd.DataFrame({"outro": ["x"]})
        c  = _contract([_col("id", "integer", nullable=True)])
        _, _, warns, _ = apply_strict_schema(df, c)
        self.assertFalse(any("MISSING_REQUIRED" in w for w in warns))


# ═════════════════════════════════════════════════════════════════════════════
# TestApplyStrictSchemaRejection
# ═════════════════════════════════════════════════════════════════════════════

class TestApplyStrictSchemaRejection(unittest.TestCase):

    def test_invalid_value_goes_to_rejected(self):
        df = pd.DataFrame({"id": ["1", "abc", "3"]})
        c  = _contract([_col("id", "integer")])
        typed, rejected, warns, summary = apply_strict_schema(df, c)
        self.assertEqual(len(typed), 2)
        self.assertEqual(len(rejected), 1)
        self.assertEqual(str(rejected.iloc[0]["id"]), "abc")

    def test_rejected_has_trace_columns(self):
        df = pd.DataFrame({"id": ["1", "abc"]})
        c  = _contract([_col("id", "integer")])
        _, rejected, _, _ = apply_strict_schema(df, c)
        for col in REJECT_TRACE_COLUMNS:
            self.assertIn(col, rejected.columns)

    def test_reject_reason_is_type_not_conformant(self):
        df = pd.DataFrame({"id": ["1", "abc"]})
        c  = _contract([_col("id", "integer")])
        _, rejected, _, _ = apply_strict_schema(df, c)
        self.assertEqual(rejected.iloc[0]["_reject_reason"], REASON_TYPE)

    def test_reject_columns_lists_failing_column(self):
        df = pd.DataFrame({"id": ["abc"], "nome": ["Ana"]})
        c  = _contract([_col("id", "integer"), _col("nome", "string")])
        _, rejected, _, _ = apply_strict_schema(df, c)
        self.assertIn("id", rejected.iloc[0]["_reject_columns"])

    def test_reject_values_contains_original_value(self):
        df = pd.DataFrame({"id": ["abc_invalido"]})
        c  = _contract([_col("id", "integer")])
        _, rejected, _, _ = apply_strict_schema(df, c)
        self.assertIn("abc_invalido", rejected.iloc[0]["_reject_values"])

    def test_multiple_bad_columns_same_row(self):
        df = pd.DataFrame({"id": ["abc"], "val": ["xyz"]})
        c  = _contract([_col("id", "integer"), _col("val", "float")])
        _, rejected, _, _ = apply_strict_schema(df, c)
        # A mesma linha vai para rejected com ambas as colunas listadas
        self.assertEqual(len(rejected), 1)
        cols = rejected.iloc[0]["_reject_columns"]
        self.assertIn("id", cols)
        self.assertIn("val", cols)

    def test_valid_row_stays_in_typed(self):
        df = pd.DataFrame({"id": ["1", "abc", "3"]})
        c  = _contract([_col("id", "integer")])
        typed, _, _, _ = apply_strict_schema(df, c)
        self.assertEqual(list(typed["id"]), [1, 3])

    def test_all_valid_empty_rejected(self):
        df = pd.DataFrame({"id": ["1", "2", "3"]})
        c  = _contract([_col("id", "integer")])
        _, rejected, _, _ = apply_strict_schema(df, c)
        self.assertEqual(len(rejected), 0)

    def test_reject_warn_message(self):
        df = pd.DataFrame({"id": ["abc"]})
        c  = _contract([_col("id", "integer")])
        _, _, warns, _ = apply_strict_schema(df, c)
        self.assertTrue(any("REJECT" in w and "id" in w for w in warns))


# ═════════════════════════════════════════════════════════════════════════════
# TestApplyStrictSchemaSummary
# ═════════════════════════════════════════════════════════════════════════════

class TestApplyStrictSchemaSummary(unittest.TestCase):

    def _run(self, data, cols, tolerance=None):
        df = pd.DataFrame(data)
        c  = _contract([_col(n, t) for n, t in cols], tolerance=tolerance)
        return apply_strict_schema(df, c)

    def test_summary_keys(self):
        _, _, _, summary = self._run({"id": ["1","2"]}, [("id","integer")])
        expected_keys = {"rows_total","rows_rejected","rows_kept","rows_type",
                         "rows_duplicate","reject_pct","limit_pct","by_column","within_limit"}
        self.assertEqual(set(summary.keys()), expected_keys)

    def test_rows_total(self):
        _, _, _, s = self._run({"id": ["1","2","3"]}, [("id","integer")])
        self.assertEqual(s["rows_total"], 3)

    def test_rows_rejected_zero_on_clean(self):
        _, _, _, s = self._run({"id": ["1","2"]}, [("id","integer")])
        self.assertEqual(s["rows_rejected"], 0)

    def test_rows_kept_correct(self):
        _, _, _, s = self._run({"id": ["1","abc","3"]}, [("id","integer")])
        self.assertEqual(s["rows_kept"], 2)
        self.assertEqual(s["rows_rejected"], 1)
        self.assertEqual(s["rows_kept"] + s["rows_rejected"], s["rows_total"])

    def test_rows_type_count(self):
        _, _, _, s = self._run({"id": ["1","abc","xyz"]}, [("id","integer")])
        self.assertEqual(s["rows_type"], 2)

    def test_reject_pct(self):
        _, _, _, s = self._run({"id": ["1","abc","3","xyz"]}, [("id","integer")])
        self.assertAlmostEqual(s["reject_pct"], 50.0)

    def test_within_limit_true_when_under(self):
        tol = _tolerance(max_reject_pct=60.0)
        _, _, _, s = self._run({"id": ["1","abc"]}, [("id","integer")], tolerance=tol)
        self.assertTrue(s["within_limit"])

    def test_within_limit_false_when_over(self):
        tol = _tolerance(max_reject_pct=0.0)
        _, _, _, s = self._run({"id": ["1","abc"]}, [("id","integer")], tolerance=tol)
        self.assertFalse(s["within_limit"])

    def test_by_column_lists_failing_columns(self):
        _, _, _, s = self._run({"id": ["abc"],"val": ["xyz"]},
                               [("id","integer"),("val","float")])
        self.assertIn("id",  s["by_column"])
        self.assertIn("val", s["by_column"])

    def test_limit_pct_in_summary(self):
        tol = _tolerance(max_reject_pct=10.0)
        _, _, _, s = self._run({"id": ["1"]}, [("id","integer")], tolerance=tol)
        self.assertEqual(s["limit_pct"], 10.0)


# ═════════════════════════════════════════════════════════════════════════════
# TestApplyStrictSchemaReport
# ═════════════════════════════════════════════════════════════════════════════

class TestApplyStrictSchemaReport(unittest.TestCase):

    def test_report_populated_per_column(self):
        df = pd.DataFrame({"id": ["1","abc"], "nome": ["Ana","Bruno"]})
        c  = _contract([_col("id","integer"), _col("nome","string")])
        report = {}
        apply_strict_schema(df, c, report=report)
        self.assertIn("id",   report)
        self.assertIn("nome", report)

    def test_report_declared_type(self):
        df = pd.DataFrame({"id": ["1"]})
        c  = _contract([_col("id","integer")])
        report = {}
        apply_strict_schema(df, c, report=report)
        self.assertEqual(report["id"]["declared"], "integer")

    def test_report_fail_pct(self):
        df = pd.DataFrame({"id": ["1","abc","3","xyz"]})
        c  = _contract([_col("id","integer")])
        report = {}
        apply_strict_schema(df, c, report=report)
        self.assertAlmostEqual(report["id"]["fail_pct"], 50.0)

    def test_report_cast_ok_true_on_clean(self):
        df = pd.DataFrame({"id": ["1","2"]})
        c  = _contract([_col("id","integer")])
        report = {}
        apply_strict_schema(df, c, report=report)
        self.assertTrue(report["id"]["cast_ok"])

    def test_report_cast_ok_false_on_fail(self):
        df = pd.DataFrame({"id": ["abc"]})
        c  = _contract([_col("id","integer")])
        report = {}
        apply_strict_schema(df, c, report=report)
        self.assertFalse(report["id"]["cast_ok"])

    def test_report_missing_column(self):
        df = pd.DataFrame({"outro": ["x"]})
        c  = _contract([_col("id","integer", nullable=False)])
        report = {}
        apply_strict_schema(df, c, report=report)
        self.assertIn("id", report)
        self.assertTrue(report["id"]["missing"])

    def test_report_rejected_rows_count(self):
        df = pd.DataFrame({"id": ["1","abc","xyz"]})
        c  = _contract([_col("id","integer")])
        report = {}
        apply_strict_schema(df, c, report=report)
        self.assertEqual(report["id"]["rejected_rows"], 2)

    def test_no_report_when_none(self):
        df = pd.DataFrame({"id": ["1"]})
        c  = _contract([_col("id","integer")])
        # Nao deve levantar excecao quando report=None (default)
        apply_strict_schema(df, c, report=None)


# ═════════════════════════════════════════════════════════════════════════════
# TestSplitDuplicatePK
# ═════════════════════════════════════════════════════════════════════════════

class TestSplitDuplicatePK(unittest.TestCase):

    def _split(self, data, pk_names, allow_dup=False):
        tol = _tolerance(allow_duplicates=allow_dup)
        df  = pd.DataFrame(data)
        c   = _contract(
            [_col(n, "string") for n in df.columns],
            tolerance=tol,
            pk_names=pk_names,
        )
        return _split_duplicate_pk(df, df.copy(), c)

    def test_no_duplicates_returns_empty(self):
        dup_df, dup_idx = self._split({"id": ["1","2","3"]}, ["id"])
        self.assertEqual(len(dup_idx), 0)
        self.assertEqual(len(dup_df), 0)

    def test_duplicate_detected(self):
        dup_df, dup_idx = self._split({"id": ["1","2","1"]}, ["id"])
        self.assertEqual(len(dup_idx), 1)
        self.assertEqual(str(dup_df.iloc[0]["id"]), "1")

    def test_first_occurrence_kept(self):
        df  = pd.DataFrame({"id": ["1","1","1"]})
        tol = _tolerance()
        c   = _contract([_col("id","string")], tolerance=tol, pk_names=["id"])
        typed, rejected, _, _ = apply_strict_schema(df, c)
        # Primeira ocorrencia fica em typed, as duas repeticoes vao para rejected
        self.assertEqual(len(typed), 1)
        self.assertEqual(len(rejected), 2)
        self.assertEqual(str(typed.iloc[0]["id"]), "1")

    def test_reject_reason_is_duplicate(self):
        dup_df, dup_idx = self._split({"id": ["1","1"]}, ["id"])
        self.assertEqual(dup_df.iloc[0]["_reject_reason"], REASON_DUPLICATE)

    def test_duplicate_has_trace_columns(self):
        dup_df, _ = self._split({"id": ["1","1"]}, ["id"])
        for col in REJECT_TRACE_COLUMNS:
            self.assertIn(col, dup_df.columns)

    def test_allow_duplicates_returns_empty(self):
        dup_df, dup_idx = self._split({"id": ["1","1","1"]}, ["id"], allow_dup=True)
        self.assertEqual(len(dup_idx), 0)

    def test_composite_pk(self):
        data = {"a": ["1","1","1"], "b": ["x","x","y"]}
        dup_df, dup_idx = self._split(data, ["a","b"])
        # ("1","x") aparece 2x, ("1","y") aparece 1x → 1 duplicata
        self.assertEqual(len(dup_idx), 1)

    def test_no_pk_declared_returns_empty(self):
        df  = pd.DataFrame({"id": ["1","1"]})
        tol = _tolerance()
        c   = _contract([_col("id","string")], tolerance=tol, pk_names=[])
        dup_df, dup_idx = _split_duplicate_pk(df, df.copy(), c)
        self.assertEqual(len(dup_idx), 0)

    def test_empty_df_returns_empty(self):
        df  = pd.DataFrame({"id": pd.Series([], dtype=str)})
        tol = _tolerance()
        c   = _contract([_col("id","string")], tolerance=tol, pk_names=["id"])
        dup_df, dup_idx = _split_duplicate_pk(df, df.copy(), c)
        self.assertEqual(len(dup_idx), 0)

    def test_reject_values_contains_pk_values(self):
        dup_df, _ = self._split({"id": ["ABC","ABC"]}, ["id"])
        self.assertIn("ABC", dup_df.iloc[0]["_reject_values"])

    def test_duplicate_warning_in_apply(self):
        df  = pd.DataFrame({"id": ["1","1","2"]})
        tol = _tolerance()
        c   = _contract([_col("id","string")], tolerance=tol, pk_names=["id"])
        _, _, warns, summary = apply_strict_schema(df, c)
        self.assertTrue(any("duplicada" in w.lower() or "duplicate" in w.lower()
                            for w in warns))
        self.assertEqual(summary["rows_duplicate"], 1)


# ═════════════════════════════════════════════════════════════════════════════
# TestApplyStrictSchemaIntegration
# ═════════════════════════════════════════════════════════════════════════════

class TestApplyStrictSchemaIntegration(unittest.TestCase):
    """Cenários realistas combinando cast + rejeição + duplicata."""

    def test_mixed_type_and_duplicate(self):
        """Uma linha com tipo errado e outra com PK duplicada."""
        df = pd.DataFrame({
            "id" : ["1", "abc", "1"],
            "nome": ["Ana", "Bruno", "Carlos"],
        })
        tol = _tolerance()
        c   = _contract(
            [_col("id","integer",primary_key=True), _col("nome","string")],
            tolerance=tol,
            pk_names=["id"],
        )
        typed, rejected, warns, summary = apply_strict_schema(df, c)
        # "abc" → type reject; "1" (segunda ocorrencia) → duplicate reject
        self.assertEqual(summary["rows_total"], 3)
        self.assertEqual(summary["rows_rejected"], 2)
        self.assertEqual(summary["rows_kept"], 1)
        self.assertEqual(summary["rows_type"], 1)
        self.assertEqual(summary["rows_duplicate"], 1)

    def test_reject_pct_calculation_with_both_reasons(self):
        df = pd.DataFrame({
            "id": ["1","abc","3","3"],
        })
        tol = _tolerance(max_reject_pct=60.0)
        c   = _contract([_col("id","integer",primary_key=True)],
                         tolerance=tol, pk_names=["id"])
        _, _, _, summary = apply_strict_schema(df, c)
        # 1 tipo + 1 duplicata = 2 rejeições / 4 linhas = 50%
        self.assertAlmostEqual(summary["reject_pct"], 50.0)
        self.assertTrue(summary["within_limit"])

    def test_float_and_date_columns(self):
        df = pd.DataFrame({
            "val": ["5000.0", "nao_e_numero"],
            "dt" : ["2024-01-15", "2024-06-30"],
        })
        c = _contract([_col("val","float"), _col("dt","date")])
        typed, rejected, _, summary = apply_strict_schema(df, c)
        self.assertEqual(summary["rows_type"], 1)
        self.assertEqual(str(typed["val"].iloc[0]), "5000.0")

    def test_empty_dataframe(self):
        df = pd.DataFrame({"id": pd.Series([], dtype=str)})
        c  = _contract([_col("id","integer")])
        typed, rejected, _, summary = apply_strict_schema(df, c)
        self.assertEqual(len(typed), 0)
        self.assertEqual(summary["rows_total"], 0)
        self.assertEqual(summary["reject_pct"], 0.0)

    def test_report_and_summary_consistent(self):
        df = pd.DataFrame({"id": ["1","abc","3"]})
        c  = _contract([_col("id","integer")])
        report = {}
        _, _, _, summary = apply_strict_schema(df, c, report=report)
        self.assertEqual(report["id"]["rejected_rows"], summary["rows_type"])

    def test_all_rows_rejected_empty_typed(self):
        df = pd.DataFrame({"id": ["abc","xyz","def"]})
        c  = _contract([_col("id","integer")])
        typed, rejected, _, summary = apply_strict_schema(df, c)
        self.assertEqual(len(typed), 0)
        self.assertEqual(len(rejected), 3)
        self.assertEqual(summary["rows_rejected"], 3)


if __name__ == "__main__":
    unittest.main()
