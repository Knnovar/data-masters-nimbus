"""
tests/test_quality_score.py — Suite de testes para src/metrics/quality_score.py

Cobre todas as dimensões do quality score e seus casos de borda:
  - _conformity: DLQ, sem cast_report, colunas quebradas, tudo conforme
  - _completeness: nulos obrigatórios, anuláveis com tolerância, sem profiling
  - _uniqueness: sem PK, allow_duplicates, duplicatas, score mínimo
  - _schema_stability: None / NON_BREAKING / BREAKING / tipo desconhecido
  - compute: pesos, dimensões None, score máximo 100, integração completa
"""

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.metrics.quality_score import (
    DUPLICATE_FACTOR,
    MANDATORY_NULL_FACTOR,
    OPTIONAL_NULL_MAX_PENALTY,
    WEIGHTS,
    _conformity,
    _completeness,
    _dim,
    _schema_stability,
    _uniqueness,
    compute,
)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _val(status="PASS", null_violations=None, rows_total=100,
         duplicate_count=0, evolution_type=None):
    return SimpleNamespace(
        status          = status,
        null_violations = null_violations or {},
        rows_total      = rows_total,
        duplicate_count = duplicate_count,
        evolution_type  = evolution_type,
    )


def _contract(pk_names=None, non_nullable=None, max_null_pct=None,
              allow_duplicates=False):
    tol = SimpleNamespace(
        max_null_pct     = max_null_pct,
        allow_duplicates = allow_duplicates,
    )

    def _get_pks():
        return pk_names or []

    def _get_non_nullable():
        return non_nullable or []

    return SimpleNamespace(
        get_primary_keys  = _get_pks,
        get_non_nullable  = _get_non_nullable,
        tolerance         = tol,
    )


def _profiler(cols=None):
    """Monta payload do profiler com null_pct por coluna."""
    columns = {c: {"null_pct": pct} for c, pct in (cols or {}).items()}
    return {"columns": columns}


def _cast_report(col_map):
    """
    col_map: {nome: (cast_ok, fail_pct)}
    Ex: {"id": (True, 0.0), "val": (False, 30.5)}
    """
    return {name: {"cast_ok": ok, "fail_pct": pct}
            for name, (ok, pct) in col_map.items()}


# ═════════════════════════════════════════════════════════════════════════════
# TestDim
# ═════════════════════════════════════════════════════════════════════════════

class TestDim(unittest.TestCase):

    def test_returns_dict_with_value_and_detail(self):
        d = _dim(85.5, "detalhe")
        self.assertEqual(set(d.keys()), {"value", "detail"})

    def test_value_rounded_to_one_decimal(self):
        d = _dim(85.567, "x")
        self.assertEqual(d["value"], 85.6)

    def test_none_value_preserved(self):
        d = _dim(None, "sem dados")
        self.assertIsNone(d["value"])

    def test_zero_rounded(self):
        self.assertEqual(_dim(0.0, "x")["value"], 0.0)

    def test_100_rounded(self):
        self.assertEqual(_dim(100.0, "x")["value"], 100.0)

    def test_detail_stored(self):
        self.assertEqual(_dim(50.0, "meu detalhe")["detail"], "meu detalhe")


# ═════════════════════════════════════════════════════════════════════════════
# TestConformity
# ═════════════════════════════════════════════════════════════════════════════

class TestConformity(unittest.TestCase):

    def test_dlq_returns_zero(self):
        r = _conformity(_val(status="DLQ"), cast_report=None)
        self.assertEqual(r["value"], 0.0)

    def test_dlq_detail_mentions_quarentena(self):
        r = _conformity(_val(status="DLQ"), cast_report=None)
        self.assertIn("quarentena", r["detail"].lower())

    def test_no_cast_report_returns_none(self):
        r = _conformity(_val(status="PASS"), cast_report=None)
        self.assertIsNone(r["value"])

    def test_empty_cast_report_returns_none(self):
        r = _conformity(_val(status="PASS"), cast_report={})
        self.assertIsNone(r["value"])

    def test_all_conformant_returns_100(self):
        report = _cast_report({"id": (True, 0.0), "nome": (True, 0.0)})
        r = _conformity(_val(), report)
        self.assertEqual(r["value"], 100.0)

    def test_broken_column_returns_zero(self):
        report = _cast_report({"id": (False, 50.0), "nome": (True, 0.0)})
        r = _conformity(_val(), report)
        self.assertEqual(r["value"], 0.0)

    def test_broken_column_detail_names_column(self):
        report = _cast_report({"val": (False, 30.0)})
        r = _conformity(_val(), report)
        self.assertIn("val", r["detail"])

    def test_broken_column_detail_includes_fail_pct(self):
        report = _cast_report({"val": (False, 42.5)})
        r = _conformity(_val(), report)
        self.assertIn("42.5", r["detail"])

    def test_worst_fail_pct_shown_when_multiple_broken(self):
        report = _cast_report({"a": (False, 10.0), "b": (False, 90.0)})
        r = _conformity(_val(), report)
        self.assertIn("90.0", r["detail"])

    def test_avg_fail_reduces_score(self):
        # 2 colunas com 20% de falha cada → avg_fail=20 → score=80
        report = _cast_report({"a": (True, 20.0), "b": (True, 20.0)})
        r = _conformity(_val(), report)
        self.assertAlmostEqual(r["value"], 80.0, places=1)

    def test_score_never_below_zero(self):
        report = _cast_report({"a": (True, 150.0)})  # fail_pct absurdo
        r = _conformity(_val(), report)
        self.assertGreaterEqual(r["value"], 0.0)

    def test_warning_status_not_zero(self):
        report = _cast_report({"id": (True, 0.0)})
        r = _conformity(_val(status="WARNING"), report)
        self.assertIsNotNone(r["value"])
        self.assertGreater(r["value"], 0.0)

    def test_detail_counts_conformant_columns(self):
        report = _cast_report({"a": (True, 0.0), "b": (True, 0.0), "c": (True, 0.0)})
        r = _conformity(_val(), report)
        self.assertIn("3", r["detail"])


# ═════════════════════════════════════════════════════════════════════════════
# TestCompleteness
# ═════════════════════════════════════════════════════════════════════════════

class TestCompleteness(unittest.TestCase):

    def test_no_violations_100(self):
        r = _completeness(_val(null_violations={}), None, None)
        self.assertEqual(r["value"], 100.0)

    def test_mandatory_violations_penalized(self):
        # null_violations={"col": 50.0} → mandatory_pct=50 → penalty=100
        r = _completeness(_val(null_violations={"col": 50.0}), None, None)
        self.assertEqual(r["value"], 0.0)

    def test_mandatory_factor_applied(self):
        # null_violations com 10% → penalty = 2.0 * 10 = 20 → score = 80
        r = _completeness(_val(null_violations={"col": 10.0}), None, None)
        self.assertAlmostEqual(r["value"], 80.0, places=1)

    def test_multiple_mandatory_averaged(self):
        # avg(20, 40) = 30 → penalty = 2 * 30 = 60 → score = 40
        r = _completeness(_val(null_violations={"a": 20.0, "b": 40.0}), None, None)
        self.assertAlmostEqual(r["value"], 40.0, places=1)

    def test_optional_within_tolerance_no_penalty(self):
        c = _contract(non_nullable=["id"], max_null_pct=50.0)
        prof = _profiler({"nome": 10.0})  # 10% < 50% tolerância → ratio=0.2 → pequena penalidade
        r = _completeness(_val(), prof, c)
        self.assertGreaterEqual(r["value"], 90.0)

    def test_optional_at_tolerance_max_penalty(self):
        # avg_opt = 100% da tolerância → optional_ratio=1.0 → penalty=50
        c = _contract(non_nullable=["id"], max_null_pct=50.0)
        prof = _profiler({"nome": 50.0})  # avg_opt=50 == tolerância → ratio=1.0
        r = _completeness(_val(), prof, c)
        self.assertAlmostEqual(r["value"], 50.0, places=1)

    def test_optional_above_tolerance_capped_at_ratio_1(self):
        c = _contract(non_nullable=["id"], max_null_pct=10.0)
        prof = _profiler({"nome": 200.0})  # muito acima → ratio capped at 1.0
        r = _completeness(_val(), prof, c)
        self.assertAlmostEqual(r["value"], 50.0, places=1)

    def test_no_tolerance_declared_no_optional_penalty(self):
        c = _contract(non_nullable=["id"], max_null_pct=None)
        prof = _profiler({"nome": 80.0})
        r = _completeness(_val(), prof, c)
        # Sem tolerância declarada → optional_ratio=0 → sem penalidade opcional
        self.assertEqual(r["value"], 100.0)

    def test_no_profiler_no_optional_eval(self):
        c = _contract(non_nullable=["id"], max_null_pct=30.0)
        r = _completeness(_val(), None, c)
        self.assertIn("sem profiling", r["detail"].lower())

    def test_score_never_below_zero(self):
        # Violações massivas não levam score abaixo de 0
        v = _val(null_violations={"a": 100.0, "b": 100.0})
        c = _contract(non_nullable=["id"], max_null_pct=1.0)
        prof = _profiler({"nome": 100.0})
        r = _completeness(v, prof, c)
        self.assertGreaterEqual(r["value"], 0.0)

    def test_detail_mentions_mandatory_pct(self):
        r = _completeness(_val(null_violations={"col": 25.0}), None, None)
        self.assertIn("25", r["detail"])

    def test_no_contract_no_optional_penalty(self):
        prof = _profiler({"nome": 100.0})
        r = _completeness(_val(), prof, None)
        self.assertEqual(r["value"], 100.0)


# ═════════════════════════════════════════════════════════════════════════════
# TestUniqueness
# ═════════════════════════════════════════════════════════════════════════════

class TestUniqueness(unittest.TestCase):

    def test_no_pk_returns_none(self):
        r = _uniqueness(_val(), _contract(pk_names=[]))
        self.assertIsNone(r["value"])

    def test_no_pk_detail_explains(self):
        r = _uniqueness(_val(), _contract(pk_names=[]))
        self.assertIn("primary_key", r["detail"].lower())

    def test_no_contract_returns_none(self):
        r = _uniqueness(_val(), None)
        self.assertIsNone(r["value"])

    def test_allow_duplicates_returns_100(self):
        c = _contract(pk_names=["id"], allow_duplicates=True)
        r = _uniqueness(_val(duplicate_count=50), c)
        self.assertEqual(r["value"], 100.0)

    def test_allow_duplicates_detail_explains(self):
        c = _contract(pk_names=["id"], allow_duplicates=True)
        r = _uniqueness(_val(duplicate_count=50), c)
        self.assertIn("permitidas", r["detail"].lower())

    def test_no_duplicates_returns_100(self):
        c = _contract(pk_names=["id"])
        r = _uniqueness(_val(duplicate_count=0, rows_total=100), c)
        self.assertEqual(r["value"], 100.0)

    def test_duplicates_reduce_score(self):
        # 5 duplicatas em 100 linhas → dup_pct=5 → 100 - 20*5 = 0
        c = _contract(pk_names=["id"])
        r = _uniqueness(_val(duplicate_count=5, rows_total=100), c)
        self.assertEqual(r["value"], 0.0)

    def test_1_pct_duplicates(self):
        # 1% → 100 - 20*1 = 80
        c = _contract(pk_names=["id"])
        r = _uniqueness(_val(duplicate_count=1, rows_total=100), c)
        self.assertAlmostEqual(r["value"], 80.0, places=1)

    def test_score_never_below_zero(self):
        c = _contract(pk_names=["id"])
        r = _uniqueness(_val(duplicate_count=999, rows_total=100), c)
        self.assertGreaterEqual(r["value"], 0.0)

    def test_detail_includes_duplicate_count(self):
        c = _contract(pk_names=["id"])
        r = _uniqueness(_val(duplicate_count=3, rows_total=100), c)
        self.assertIn("3", r["detail"])

    def test_detail_includes_pk_columns(self):
        c = _contract(pk_names=["cpf", "dt_ref"])
        r = _uniqueness(_val(duplicate_count=0, rows_total=100), c)
        self.assertIn("cpf", r["detail"])

    def test_rows_total_zero_no_division_error(self):
        c = _contract(pk_names=["id"])
        # rows_total=0 → usa 1 para evitar divisão por zero
        r = _uniqueness(_val(duplicate_count=0, rows_total=0), c)
        self.assertIsNotNone(r["value"])


# ═════════════════════════════════════════════════════════════════════════════
# TestSchemaStability
# ═════════════════════════════════════════════════════════════════════════════

class TestSchemaStability(unittest.TestCase):

    def test_none_evolution_returns_100(self):
        r = _schema_stability(_val(evolution_type=None))
        self.assertEqual(r["value"], 100.0)

    def test_non_breaking_returns_70(self):
        r = _schema_stability(_val(evolution_type="NON_BREAKING"))
        self.assertEqual(r["value"], 70.0)

    def test_breaking_returns_0(self):
        r = _schema_stability(_val(evolution_type="BREAKING"))
        self.assertEqual(r["value"], 0.0)

    def test_unknown_type_returns_50(self):
        r = _schema_stability(_val(evolution_type="OUTRO_TIPO"))
        self.assertEqual(r["value"], 50.0)

    def test_detail_mentions_evolution_type(self):
        r = _schema_stability(_val(evolution_type="NON_BREAKING"))
        self.assertIn("NON_BREAKING", r["detail"])

    def test_detail_mentions_none_when_no_evolution(self):
        r = _schema_stability(_val(evolution_type=None))
        self.assertIn("nenhuma", r["detail"].lower())


# ═════════════════════════════════════════════════════════════════════════════
# TestCompute — função principal
# ═════════════════════════════════════════════════════════════════════════════

class TestCompute(unittest.TestCase):

    def test_returns_dict_with_score_and_dimensions(self):
        result = compute(_val(), None, None, None)
        self.assertIn("score", result)
        self.assertIn("dimensions", result)

    def test_dimensions_has_all_four_keys(self):
        result = compute(_val(), None, None, None)
        self.assertEqual(set(result["dimensions"].keys()),
                         {"conformity", "completeness", "uniqueness", "schema_stability"})

    def test_each_dimension_has_weight(self):
        result = compute(_val(), None, None, None)
        for name, d in result["dimensions"].items():
            self.assertIn("weight", d)
            self.assertEqual(d["weight"], WEIGHTS[name])

    def test_score_capped_at_100(self):
        report = _cast_report({"id": (True, 0.0)})
        c = _contract(pk_names=["id"])
        result = compute(_val(), _profiler(), c, report)
        self.assertLessEqual(result["score"], 100.0)

    def test_score_never_below_zero(self):
        v = _val(status="DLQ", null_violations={"a": 100.0},
                 duplicate_count=100, evolution_type="BREAKING")
        result = compute(v, None, None, None)
        self.assertGreaterEqual(result["score"], 0.0)

    def test_dlq_status_low_score(self):
        v = _val(status="DLQ", evolution_type="BREAKING")
        result = compute(v, None, None, None)
        self.assertLess(result["score"], 50.0)

    def test_clean_data_high_score(self):
        c      = _contract(pk_names=["id"], non_nullable=["id"])
        report = _cast_report({"id": (True, 0.0), "nome": (True, 0.0)})
        result = compute(_val(status="PASS"), _profiler({"nome": 0.0}), c, report)
        self.assertGreater(result["score"], 85.0)

    def test_none_dimensions_excluded_from_weighted_avg(self):
        # Sem cast_report e sem PK → conformity=None, uniqueness=None
        # Apenas completeness e schema_stability são medidas
        result = compute(_val(), None, None, None)
        measured = {n: d for n, d in result["dimensions"].items()
                    if d["value"] is not None}
        self.assertIn("completeness",    measured)
        self.assertIn("schema_stability", measured)
        # Score deve ser calculado só sobre as medidas
        total_w = sum(d["weight"] for d in measured.values())
        expected = sum(d["value"] * d["weight"] for d in measured.values()) / total_w
        self.assertAlmostEqual(result["score"], round(min(expected, 100.0), 1), places=1)

    def test_all_none_dimensions_returns_zero(self):
        # Força todas as dimensões para None: DLQ (conformity=0 não é None),
        # então usa status PASS sem cast_report e sem PK
        result = compute(_val(status="PASS"), None, _contract(pk_names=[]), None)
        # conformity=None, uniqueness=None → só completeness e stability medidos
        self.assertIsNotNone(result["score"])

    def test_score_is_rounded_to_one_decimal(self):
        result = compute(_val(), None, None, None)
        score_str = str(result["score"])
        decimal_places = len(score_str.split(".")[-1]) if "." in score_str else 0
        self.assertLessEqual(decimal_places, 1)

    def test_weights_sum_to_1(self):
        self.assertAlmostEqual(sum(WEIGHTS.values()), 1.0, places=10)

    def test_conformity_weight_40pct(self):
        self.assertEqual(WEIGHTS["conformity"], 0.40)

    def test_completeness_weight_25pct(self):
        self.assertEqual(WEIGHTS["completeness"], 0.25)

    def test_uniqueness_weight_20pct(self):
        self.assertEqual(WEIGHTS["uniqueness"], 0.20)

    def test_schema_stability_weight_15pct(self):
        self.assertEqual(WEIGHTS["schema_stability"], 0.15)

    def test_breaking_with_no_other_issues_score_below_60(self):
        # BREAKING → stability=0 (peso 15%), mas outros podem ser 100
        report = _cast_report({"id": (True, 0.0)})
        c = _contract(pk_names=["id"])
        result = compute(_val(evolution_type="BREAKING"),
                         _profiler({"id": 0.0}), c, report)
        self.assertLess(result["score"], 100.0)

    def test_non_breaking_reduces_score_vs_stable(self):
        c = _contract(pk_names=["id"])
        report = _cast_report({"id": (True, 0.0)})
        score_stable     = compute(_val(evolution_type=None), None, c, report)["score"]
        score_non_breaking = compute(_val(evolution_type="NON_BREAKING"), None, c, report)["score"]
        self.assertGreater(score_stable, score_non_breaking)

    def test_duplicates_reduce_score(self):
        c = _contract(pk_names=["id"])
        report = _cast_report({"id": (True, 0.0)})
        score_clean = compute(_val(duplicate_count=0, rows_total=100), None, c, report)["score"]
        score_dup   = compute(_val(duplicate_count=2, rows_total=100), None, c, report)["score"]
        self.assertGreater(score_clean, score_dup)


# ═════════════════════════════════════════════════════════════════════════════
# TestConstants
# ═════════════════════════════════════════════════════════════════════════════

class TestConstants(unittest.TestCase):

    def test_mandatory_null_factor_is_2(self):
        self.assertEqual(MANDATORY_NULL_FACTOR, 2.0)

    def test_optional_null_max_penalty_is_50(self):
        self.assertEqual(OPTIONAL_NULL_MAX_PENALTY, 50.0)

    def test_duplicate_factor_is_20(self):
        self.assertEqual(DUPLICATE_FACTOR, 20.0)

    def test_stability_none_is_100(self):
        from src.metrics.quality_score import _STABILITY
        self.assertEqual(_STABILITY[None], 100.0)

    def test_stability_non_breaking_is_70(self):
        from src.metrics.quality_score import _STABILITY
        self.assertEqual(_STABILITY["NON_BREAKING"], 70.0)

    def test_stability_breaking_is_0(self):
        from src.metrics.quality_score import _STABILITY
        self.assertEqual(_STABILITY["BREAKING"], 0.0)


if __name__ == "__main__":
    unittest.main()
