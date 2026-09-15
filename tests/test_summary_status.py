"""
tests/test_summary_status.py - Coluna Status do resumo e do relatorio.

Validacao estrutural e gate sao decisoes distintas, e o resumo mostrava apenas
a primeira: uma tabela barrada por rejeicao acima da tolerancia aparecia como
PASS na coluna Status e o bloqueio ficava visivel somente na coluna Publicacao.
Estes testes fixam a precedencia do gate na exibicao, sem alterar o campo
validation_status persistido nas metricas e no ledger.
"""

import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))
from run_pipeline import print_summary
from src.metrics.metrics_collector import generate_report, summary_status
from src.storage.storage import LocalStorage

_LAYERS = ["bronze", "silver", "gold", "quarantine", "contracts", "metrics", "reports"]


def _metrics(**over) -> dict:
    base = {
        "run_id"           : "run_teste",
        "table"            : "tb_clientes",
        "scenario"         : "type_drift",
        "validation_status": "PASS",
        "gate_status"      : "PASS",
        "gate_reason"      : "CONFORMANT",
        "quality_score"    : 56.6,
        "rows_total"       : 500,
        "duplicate_count"  : 0,
        "avg_null_pct"     : 0.0,
        "profiling_ms"     : 10,
        "slm_status"       : "SKIPPED",
        "slm_inference_ms" : 0,
        "quality_dimensions": {},
        "issues"           : [],
        "warnings"         : [],
        "null_violations"  : 0,
        "rows_rejected"    : 0,
    }
    base.update(over)
    return base


class TestSummaryStatus(unittest.TestCase):

    def test_gate_bloqueado_tem_precedencia_sobre_validacao(self):
        icon, status = summary_status(_metrics(
            gate_status="BLOCKED", gate_reason="REJECT_ABOVE_TOLERANCE"))
        self.assertEqual(status, "BLOCKED")
        self.assertEqual(icon, "[BLOCK]")

    def test_bloqueio_por_governanca_tambem_aparece(self):
        _, status = summary_status(_metrics(
            gate_status="BLOCKED", gate_reason="MANIFEST_NOT_VALIDATED"))
        self.assertEqual(status, "BLOCKED")

    def test_bloqueio_por_contrato_ilegivel_tambem_aparece(self):
        _, status = summary_status(_metrics(
            gate_status="BLOCKED", gate_reason="CONTRACT_UNREADABLE"))
        self.assertEqual(status, "BLOCKED")

    def test_dlq_continua_dlq(self):
        icon, status = summary_status(_metrics(
            validation_status="DLQ", gate_status="BLOCKED",
            gate_reason="VALIDATION_DLQ"))
        self.assertEqual(status, "DLQ")
        self.assertEqual(icon, "[DLQ]")

    def test_erro_continua_erro(self):
        _, status = summary_status(_metrics(
            validation_status="ERROR", gate_status="BLOCKED"))
        self.assertEqual(status, "ERROR")

    def test_pass_with_rejects_preserva_o_status_da_validacao(self):
        icon, status = summary_status(_metrics(
            validation_status="WARNING", gate_status="PASS_WITH_REJECTS"))
        self.assertEqual(status, "WARNING")
        self.assertEqual(icon, "[WARN]")

    def test_pass_liberado_permanece_pass(self):
        icon, status = summary_status(_metrics())
        self.assertEqual(status, "PASS")
        self.assertEqual(icon, "[PASS]")

    def test_status_desconhecido_nao_quebra(self):
        icon, status = summary_status({"validation_status": "OUTRO"})
        self.assertEqual(status, "OUTRO")
        self.assertEqual(icon, "[?]")

    def test_registro_sem_validation_status_nao_quebra(self):
        icon, _ = summary_status({})
        self.assertEqual(icon, "[?]")


class TestResumoImpresso(unittest.TestCase):

    def _resumo(self, metrics: dict) -> str:
        buf = io.StringIO()
        with redirect_stdout(buf):
            print_summary([metrics])
        return buf.getvalue()

    def test_tabela_barrada_nao_aparece_como_pass(self):
        saida = self._resumo(_metrics(
            gate_status="BLOCKED", gate_reason="REJECT_ABOVE_TOLERANCE"))
        self.assertIn("[BLOCK] BLOCKED", saida)
        self.assertIn("[QUALIDADE]", saida)
        self.assertNotIn("PASS", saida)

    def test_tabela_liberada_mantem_o_resumo_anterior(self):
        saida = self._resumo(_metrics())
        self.assertIn("[PASS] PASS", saida)
        self.assertIn("[LIBERADA]", saida)


class TestRelatorioMarkdown(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.storage = LocalStorage({l: base / l for l in _LAYERS})

    def tearDown(self):
        self.tmp.cleanup()

    def _relatorio(self, metrics: list[dict]) -> str:
        with patch("src.metrics.metrics_collector.get_storage",
                   return_value=self.storage):
            with redirect_stdout(io.StringIO()):
                nome = generate_report(metrics)
        with open(self.storage.read_path("reports", nome), encoding="utf-8") as f:
            return f.read()

    def test_relatorio_usa_o_mesmo_criterio_do_resumo(self):
        md = self._relatorio([_metrics(
            gate_status="BLOCKED", gate_reason="REJECT_ABOVE_TOLERANCE")])
        self.assertIn("| [BLOCK] BLOCKED ", md)

    def test_relatorio_de_carga_liberada_permanece_pass(self):
        md = self._relatorio([_metrics()])
        self.assertIn("| [PASS] PASS ", md)

    def test_contagem_de_dlq_e_warning_usa_validation_status(self):
        md = self._relatorio([
            _metrics(validation_status="WARNING", gate_status="BLOCKED",
                     gate_reason="REJECT_ABOVE_TOLERANCE"),
        ])
        self.assertIn("**Com WARNING:** 1", md)
        self.assertIn("**Com DLQ:** 0", md)


if __name__ == "__main__":
    unittest.main(verbosity=2)
