import sys, tempfile, unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))
from run_pipeline import pipeline_exit_code
from prefect_flow import _metric_exit_code

def _metric(status="PASS", gate_status="PASS", table="tb_clientes"):
    return {"table": table, "validation_status": status, "gate_status": gate_status}

def _pub(status="SKIPPED", table="tb_clientes"):
    return {"table":table, "status": status, "layer": "silver", "error": None}

class TestPipelineExitCode(unittest.TestCase):

    def test_tudo_liberado_e_zero(self):
        self.assertEqual(pipeline_exit_code([_metric()], [_pub("OK")]), 0)

    def test_skipped_sem_credencial_nao_e_falha(self):
        self.assertEqual(pipeline_exit_code([_metric()], [_pub("SKIPPED")]), 0)

    def test_dlq_vale_dois_mesmo_sem_publicacao(self):
        self.assertEqual(pipeline_exit_code([_metric(status="DLQ")], []), 2)

    def test_gate_bloqueado_vale_dois_com_validacao_em_pass(self):
        metrics = [_metric(gate_status="BLOCKED")]
        self.assertEqual(pipeline_exit_code(metrics,[_pub("SKIPPED")]), 2)

    def test_falha_de_publicacao_vale_dois(self):
        self.assertEqual(pipeline_exit_code([_metric()], [_pub("ERROR")]), 2)

    def test_warning_com_rejeicao_dentro_da_tolerancia_e_zero(self):
        metrics = [_metric(status="WARNING", gate_status="PASS_WITH_REJECTS")]
        self.assertEqual(pipeline_exit_code(metrics, [_pub("OK")]), 0)

    def test_uma_tabela_ruim_derruba_a_run(self):
        metrics = [_metric(), _metric(status="DLQ", table="tb_transacoes")]
        self.assertEqual(pipeline_exit_code(metrics, [_pub("OK")]), 2)

class TestParidadeEntreRunners(unittest.TestCase):
    """A mesma metrica tem que dar o mesmo codigo nos dois runners."""

    def test_mesma_metrica_mesmo_codigo(self):
        casos = [
            _metric(),
            _metric(status="DLQ"),
            _metric(gate_status="BLOCKED"),
            _metric(status="WARNING", gate_status="PASS_WITH_REJECTS"),
        ]

        for m in casos:
            with self.subTest(metric=m):
                self.assertEqual(pipeline_exit_code([m], []), _metric_exit_code(m))

if __name__ == "__main__":
    unittest.main()