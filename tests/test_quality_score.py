"""
tests/test_quality_score.py - Testes para src/metrics/quality_score.py

O score e o numero exibido no dashboard e nas metricas; estes testes fixam o
que cada dimensao mede, como a renormalizacao trata dimensao nao medida
(value=None) e quais cenarios tem que zerar a conformidade.
"""

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.metrics.quality_score import WEIGHTS, compute


def val_result(status="PASS", rows_total=100, duplicate_count=0,
               null_violations=None, evolution_type=None):
    return SimpleNamespace(
        status=status,
        rows_total=rows_total,
        rows_valid=rows_total,
        duplicate_count=duplicate_count,
        null_violations=null_violations or {},
        evolution_type=evolution_type,
    )


def contract(primary_keys=("id",), non_nullable=("id",), max_null_pct=None,
             allow_duplicates=False):
    return SimpleNamespace(
        get_primary_keys=lambda: list(primary_keys),
        get_non_nullable=lambda: list(non_nullable),
        tolerance=SimpleNamespace(max_null_pct=max_null_pct,
                                  allow_duplicates=allow_duplicates),
    )


def cast_report(**cols):
    """cast_report({'vl': (True, 0.0)}) -> formato esperado por compute()."""
    return {c: {"cast_ok": ok, "fail_pct": pct} for c, (ok, pct) in cols.items()}


class TestPesos(unittest.TestCase):

    def test_pesos_somam_um(self):
        self.assertAlmostEqual(sum(WEIGHTS.values()), 1.0)

    def test_pesos_declarados(self):
        self.assertEqual(WEIGHTS, {"conformity": 0.40, "completeness": 0.25,
                                   "uniqueness": 0.20, "schema_stability": 0.15})


class TestCasoPerfeito(unittest.TestCase):

    def test_tudo_conforme_da_cem(self):
        out = compute(val_result(), {"columns": {}}, contract(),
                      cast_report(id=(True, 0.0)))
        self.assertEqual(out["score"], 100.0)

    def test_todas_as_dimensoes_sao_reportadas(self):
        out = compute(val_result(), {"columns": {}}, contract(),
                      cast_report(id=(True, 0.0)))
        self.assertEqual(set(out["dimensions"]), set(WEIGHTS))
        for name, dim in out["dimensions"].items():
            self.assertEqual(dim["weight"], WEIGHTS[name])
            self.assertIn("detail", dim)


class TestConformidade(unittest.TestCase):

    def test_quarentena_zera_conformidade(self):
        out = compute(val_result(status="DLQ"), {"columns": {}}, contract(),
                      cast_report(id=(True, 0.0)))
        self.assertEqual(out["dimensions"]["conformity"]["value"], 0.0)

    def test_coluna_com_cast_reprovado_zera_conformidade(self):
        out = compute(val_result(), {"columns": {}}, contract(),
                      cast_report(vl=(False, 8.0), id=(True, 0.0)))
        self.assertEqual(out["dimensions"]["conformity"]["value"], 0.0)
        self.assertIn("vl", out["dimensions"]["conformity"]["detail"])

    def test_falha_parcial_de_cast_reduz_proporcionalmente(self):
        out = compute(val_result(), {"columns": {}}, contract(),
                      cast_report(a=(True, 2.0), b=(True, 0.0)))
        self.assertEqual(out["dimensions"]["conformity"]["value"], 99.0)

    def test_sem_cast_report_conformidade_nao_e_medida(self):
        out = compute(val_result(), {"columns": {}}, contract(), None)
        self.assertIsNone(out["dimensions"]["conformity"]["value"])

    def test_dimensao_nao_medida_e_renormalizada(self):
        """Sem conformidade, o score e a media das outras tres, nao 60% do total."""
        out = compute(val_result(), {"columns": {}}, contract(), None)
        self.assertEqual(out["score"], 100.0)


class TestCompletude(unittest.TestCase):

    def test_nulo_em_obrigatoria_penaliza_em_dobro(self):
        out = compute(val_result(null_violations={"nm": 10.0}), {"columns": {}},
                      contract(), cast_report(id=(True, 0.0)))
        self.assertEqual(out["dimensions"]["completeness"]["value"], 80.0)

    def test_nulos_em_anulaveis_dentro_da_tolerancia(self):
        payload = {"columns": {"tel": {"null_pct": 5.0}}}
        out = compute(val_result(), payload,
                      contract(max_null_pct=10.0), cast_report(id=(True, 0.0)))
        self.assertEqual(out["dimensions"]["completeness"]["value"], 75.0)

    def test_anulavel_acima_da_tolerancia_satura_a_penalidade(self):
        payload = {"columns": {"tel": {"null_pct": 90.0}}}
        out = compute(val_result(), payload,
                      contract(max_null_pct=10.0), cast_report(id=(True, 0.0)))
        self.assertEqual(out["dimensions"]["completeness"]["value"], 50.0)

    def test_sem_profiling_anulaveis_nao_sao_avaliadas(self):
        out = compute(val_result(), None, contract(), cast_report(id=(True, 0.0)))
        self.assertIn("sem profiling", out["dimensions"]["completeness"]["detail"])

    def test_completude_nao_fica_negativa(self):
        out = compute(val_result(null_violations={"a": 100.0}), {"columns": {}},
                      contract(), cast_report(id=(True, 0.0)))
        self.assertEqual(out["dimensions"]["completeness"]["value"], 0.0)


class TestUnicidade(unittest.TestCase):

    def test_sem_pk_declarada_nao_e_medida(self):
        out = compute(val_result(), {"columns": {}}, contract(primary_keys=()),
                      cast_report(id=(True, 0.0)))
        self.assertIsNone(out["dimensions"]["uniqueness"]["value"])

    def test_duplicata_penaliza_vinte_vezes_o_percentual(self):
        out = compute(val_result(duplicate_count=1, rows_total=100),
                      {"columns": {}}, contract(), cast_report(id=(True, 0.0)))
        self.assertEqual(out["dimensions"]["uniqueness"]["value"], 80.0)

    def test_contrato_que_permite_duplicata_nao_penaliza(self):
        out = compute(val_result(duplicate_count=10, rows_total=100),
                      {"columns": {}}, contract(allow_duplicates=True),
                      cast_report(id=(True, 0.0)))
        self.assertEqual(out["dimensions"]["uniqueness"]["value"], 100.0)

    def test_unicidade_nao_fica_negativa(self):
        out = compute(val_result(duplicate_count=50, rows_total=100),
                      {"columns": {}}, contract(), cast_report(id=(True, 0.0)))
        self.assertEqual(out["dimensions"]["uniqueness"]["value"], 0.0)

    def test_sem_contrato_unicidade_nao_e_medida(self):
        out = compute(val_result(), {"columns": {}}, None,
                      cast_report(id=(True, 0.0)))
        self.assertIsNone(out["dimensions"]["uniqueness"]["value"])


class TestEstabilidadeDeSchema(unittest.TestCase):

    def test_sem_evolucao_vale_cem(self):
        out = compute(val_result(), {"columns": {}}, contract(),
                      cast_report(id=(True, 0.0)))
        self.assertEqual(out["dimensions"]["schema_stability"]["value"], 100.0)

    def test_non_breaking_vale_setenta(self):
        out = compute(val_result(evolution_type="NON_BREAKING"), {"columns": {}},
                      contract(), cast_report(id=(True, 0.0)))
        self.assertEqual(out["dimensions"]["schema_stability"]["value"], 70.0)

    def test_breaking_zera_a_estabilidade(self):
        out = compute(val_result(evolution_type="BREAKING"), {"columns": {}},
                      contract(), cast_report(id=(True, 0.0)))
        self.assertEqual(out["dimensions"]["schema_stability"]["value"], 0.0)

    def test_evolucao_desconhecida_fica_no_meio(self):
        out = compute(val_result(evolution_type="OUTRA"), {"columns": {}},
                      contract(), cast_report(id=(True, 0.0)))
        self.assertEqual(out["dimensions"]["schema_stability"]["value"], 50.0)


class TestComposicao(unittest.TestCase):

    def test_score_e_a_media_ponderada_das_dimensoes_medidas(self):
        out = compute(val_result(duplicate_count=1, rows_total=100,
                                 null_violations={"nm": 10.0},
                                 evolution_type="NON_BREAKING"),
                      {"columns": {}}, contract(),
                      cast_report(a=(True, 2.0), b=(True, 0.0)))
        dims = out["dimensions"]
        esperado = sum(dims[n]["value"] * WEIGHTS[n] for n in WEIGHTS)
        self.assertEqual(out["score"], round(esperado, 1))

    def test_breaking_com_quarentena_derruba_o_score(self):
        out = compute(val_result(status="DLQ", evolution_type="BREAKING"),
                      {"columns": {}}, contract(), cast_report(id=(True, 0.0)))
        self.assertLess(out["score"], 50.0)

    def test_score_nunca_passa_de_cem(self):
        out = compute(val_result(), {"columns": {}}, contract(),
                      cast_report(id=(True, 0.0)))
        self.assertLessEqual(out["score"], 100.0)


if __name__ == "__main__":
    unittest.main()
