"""
tests/test_prefect_flow.py - Testes para prefect_flow.py

Nao dependem de servidor Prefect: o flow e as tasks sao executados pela funcao
pura (`.fn`), que e exatamente o caminho usado por `--no-prefect` no Control-M.
O que se fixa aqui e o contrato operacional - bloqueio de gate virando falha da
run (GateBlocked, com o resultado preservado) e paridade de exit code com o
runner direto.
"""

import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))
import prefect_flow as pf
from prefect_flow import (GateBlocked, _exit_code, _metric_exit_code,
                          _publication_exit_code, pipeline_flow)


def unwrap(obj):
    """Funcao pura da task/flow - o mesmo que `--no-prefect` faz na CLI."""
    return getattr(obj, "fn", obj)


def metric(table="tb_clientes", status="PASS", gate_status="PASS", score=95.0):
    return {"table": table, "scenario": "baseline", "validation_status": status,
            "gate_status": gate_status, "quality_score": score}


def publication(table="tb_clientes", status="OK", layer="silver", error=None):
    return {"table": table, "status": status, "layer": layer, "error": error}


class TestExitCodeDeStatus(unittest.TestCase):

    def test_mapeamento_declarado(self):
        self.assertEqual(_exit_code("PASS"), 0)
        self.assertEqual(_exit_code("SKIPPED"), 0)
        self.assertEqual(_exit_code("WARNING"), 0)
        self.assertEqual(_exit_code("DLQ"), 2)
        self.assertEqual(_exit_code("ERROR"), 2)

    def test_status_desconhecido_e_tratado_como_falha(self):
        self.assertEqual(_exit_code("QUALQUER_OUTRO"), 2)

    def test_gate_bloqueado_vale_dois_mesmo_com_validacao_em_pass(self):
        self.assertEqual(_metric_exit_code(metric(gate_status="BLOCKED")), 2)

    def test_sem_bloqueio_vale_o_codigo_da_validacao(self):
        self.assertEqual(_metric_exit_code(metric()), 0)
        self.assertEqual(_metric_exit_code(metric(status="DLQ")), 2)


class TestPublicationExitCode(unittest.TestCase):

    def _codigo(self, publications):
        with patch("run_pipeline.silver_guard",
                   return_value=type("G", (), {"warnings": []})()):
            with redirect_stdout(io.StringIO()):
                return _publication_exit_code(publications, "run_1")

    def test_publicacao_ok_e_zero(self):
        self.assertEqual(self._codigo([publication()]), 0)

    def test_sem_publicacao_e_zero(self):
        self.assertEqual(self._codigo([]), 0)

    def test_skipped_por_falta_de_credencial_nao_e_falha(self):
        self.assertEqual(self._codigo([publication(status="SKIPPED",
                                                   error="sem credencial")]), 0)

    def test_disabled_nao_e_falha(self):
        self.assertEqual(self._codigo([publication(status="DISABLED")]), 0)

    def test_erro_de_upload_vale_dois(self):
        self.assertEqual(self._codigo([publication(status="ERROR",
                                                   error="timeout")]), 2)

    def test_bloqueio_de_gate_vale_dois(self):
        self.assertEqual(self._codigo([publication(status="BLOCKED",
                                                   error="gate")]), 2)


class TestGateBlocked(unittest.TestCase):

    def test_excecao_preserva_o_resultado_da_run(self):
        result = {"run_id": "run_1", "exit_code": 2}
        erro = GateBlocked(result)
        self.assertIs(erro.result, result)

    def test_mensagem_cita_run_id_e_exit_code(self):
        texto = str(GateBlocked({"run_id": "run_1", "exit_code": 2}))
        self.assertIn("run_1", texto)
        self.assertIn("exit_code=2", texto)


class TestFlowSemPrefect(unittest.TestCase):
    """Executa o flow pela funcao pura, com todas as tasks substituidas."""

    def setUp(self):
        self.metricas = [metric()]
        self.publicacoes = [publication()]

        produced = [{"table": "tb_clientes", "filename": "tb_clientes.csv"}]
        patches = {
            "task_generate_data":   lambda *a, **k: produced,
            "task_validate":        lambda item, run_id: dict(item),
            "task_profile":         lambda item: dict(item),
            "task_enrich_slm":      lambda item: dict(item,
                                        publications=self.publicacoes),
            "task_collect_metrics": lambda item, run_id: self.metricas[0],
            "task_report":          lambda all_metrics, run_id: "pipeline_report.md",
        }
        for nome, subst in patches.items():
            p = patch.object(pf, nome, subst)
            p.start()
            self.addCleanup(p.stop)

    def _rodar(self, **kwargs):
        with redirect_stdout(io.StringIO()):
            return unwrap(pipeline_flow)(run_id="run_1", **kwargs)

    def test_run_liberada_devolve_exit_zero(self):
        result = self._rodar()
        self.assertEqual(result["exit_code"], 0)
        self.assertEqual(result["run_id"], "run_1")
        self.assertEqual(result["report_path"], "pipeline_report.md")

    def test_dat_ref_e_derivada_do_run_id_quando_ausente(self):
        with redirect_stdout(io.StringIO()):
            result = unwrap(pipeline_flow)(run_id="run_20240115_101112_abc")
        self.assertEqual(result["exit_code"], 0)

    def test_gate_bloqueado_levanta_gateblocked(self):
        """Sem excecao, a run aparece 'Completed' no Prefect mesmo bloqueada."""
        self.metricas[0] = metric(gate_status="BLOCKED")
        with self.assertRaises(GateBlocked) as ctx:
            self._rodar()
        self.assertEqual(ctx.exception.result["exit_code"], 2)

    def test_quarentena_levanta_gateblocked(self):
        self.metricas[0] = metric(status="DLQ")
        with self.assertRaises(GateBlocked):
            self._rodar()

    def test_falha_de_publicacao_levanta_gateblocked(self):
        self.publicacoes[0] = publication(status="ERROR", error="timeout")
        with self.assertRaises(GateBlocked) as ctx:
            self._rodar()
        self.assertEqual(ctx.exception.result["exit_code"], 2)

    def test_resultado_do_bloqueio_carrega_metricas_e_publicacoes(self):
        self.metricas[0] = metric(gate_status="BLOCKED")
        with self.assertRaises(GateBlocked) as ctx:
            self._rodar()
        result = ctx.exception.result
        self.assertEqual(result["metrics"], self.metricas)
        self.assertEqual(result["publications"], self.publicacoes)


class TestNoPrefect(unittest.TestCase):
    """A CLI oferece --no-prefect para o Control-M; a troca depende de `.fn`."""

    def test_flag_existe_no_parser(self):
        fonte = Path(pf.__file__).read_text(encoding="utf-8")
        self.assertIn('"--no-prefect"', fonte)

    def test_flow_e_tasks_expoem_a_funcao_pura(self):
        if not pf._HAS_PREFECT:
            self.skipTest("Prefect nao instalado: decoradores ja sao no-op")
        alvos = ["pipeline_flow", "task_extract_manifest", "task_generate_data",
                 "task_validate", "task_profile", "task_enrich_slm",
                 "task_collect_metrics", "task_report"]
        for nome in alvos:
            with self.subTest(alvo=nome):
                self.assertTrue(callable(unwrap(getattr(pf, nome))))

    def test_sem_prefect_os_decoradores_sao_transparentes(self):
        if pf._HAS_PREFECT:
            self.skipTest("Prefect instalado: os decoradores reais subiriam servidor")
        def alvo(x):
            return x * 2
        self.assertEqual(pf.task(alvo)(3), 6)
        self.assertEqual(pf.flow(name="x")(alvo)(3), 6)


class TestParidadeComRunnerDireto(unittest.TestCase):

    def test_mesma_metrica_mesmo_codigo_nos_dois_runners(self):
        from run_pipeline import pipeline_exit_code
        casos = [metric(), metric(status="DLQ"), metric(gate_status="BLOCKED"),
                 metric(status="WARNING", gate_status="PASS_WITH_REJECTS")]
        for m in casos:
            with self.subTest(metric=m):
                self.assertEqual(pipeline_exit_code([m], []), _metric_exit_code(m))


if __name__ == "__main__":
    unittest.main()
