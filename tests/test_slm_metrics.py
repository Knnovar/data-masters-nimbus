"""
tests/test_slm_metrics.py - Testes para src/metrics/metrics_collector.py

Cobre o achatamento das metricas da SLM (o que permite comparar modelos entre
runs) e a persistencia de metricas e relatorio: os tres artefatos tem que sair
pelo storage configurado, nunca por caminho de filesystem fixo - e o que faz o
backend MinIO/S3 receber tambem a governanca, e nao so o dado.
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))
import src.metrics.metrics_collector as mc
from src.metrics.metrics_collector import (_slm_metrics, collect,
                                           generate_report, save_summary)
from src.storage.storage import LocalStorage

_LAYERS = ["bronze", "silver", "gold", "quarantine", "contracts", "metrics", "reports"]


def val_result(table="tb_clientes", status="PASS", scenario="baseline"):
    return SimpleNamespace(
        table=table, scenario=scenario, status=status,
        rows_total=100, rows_valid=100, duplicate_count=0,
        null_violations={}, evolution_type=None, issues=[], warnings=[],
    )


def slm_result(status="SUCCESS"):
    return {
        "status": status,
        "model": "phi4",
        "num_predict": 512,
        "inference_ms": 1234,
        "perf": {"total_ms": 1300, "load_ms": 200, "prompt_tokens": 800,
                 "prompt_eval_ms": 300, "output_tokens": 120, "eval_ms": 800,
                 "tokens_per_s": 15.0, "truncated": False},
        "output": {"chars": 900, "words": 140, "column_coverage_pct": 100,
                   "columns_missing": [], "has_pontos_atencao": True,
                   "has_draft_tag": True},
    }


class TestAchatamentoDaSLM(unittest.TestCase):

    def test_campos_de_perf_e_output_ficam_planos(self):
        flat = _slm_metrics(slm_result())
        self.assertEqual(flat["slm_model"], "phi4")
        self.assertEqual(flat["slm_total_ms"], 1300)
        self.assertEqual(flat["slm_tokens_per_s"], 15.0)
        self.assertEqual(flat["slm_output_words"], 140)

    def test_nenhum_valor_aninhado(self):
        for chave, valor in _slm_metrics(slm_result()).items():
            with self.subTest(campo=chave):
                self.assertNotIsInstance(valor, dict)

    def test_resultado_sem_perf_nem_output_nao_quebra(self):
        flat = _slm_metrics({"status": "SKIPPED"})
        self.assertIsNone(flat["slm_model"])
        self.assertIsNone(flat["slm_total_ms"])
        self.assertIsNone(flat["slm_output_chars"])

    def test_draft_tag_e_preservada(self):
        """A marcacao de DRAFT do metadado gerado por IA precisa chegar a metrica."""
        self.assertTrue(_slm_metrics(slm_result())["slm_has_draft_tag"])


class PersistenciaBase(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.storage = LocalStorage({l: self.tmp / l for l in _LAYERS})
        patcher = patch.object(mc, "get_storage", lambda: self.storage)
        patcher.start()
        self.addCleanup(patcher.stop)

    def metric_files(self):
        return sorted(p.name for p in (self.tmp / "metrics").glob("*.json"))


class TestCollect(PersistenciaBase):

    def test_grava_um_json_por_tabela_e_formato(self):
        collect("run_1", val_result(), {"columns": {}}, slm_result(), fmt="csv")
        collect("run_1", val_result(), {"columns": {}}, slm_result(), fmt="json")
        self.assertEqual(self.metric_files(),
                         ["run_1_tb_clientes_csv.json", "run_1_tb_clientes_json.json"])

    def test_json_gravado_e_igual_ao_registro_devolvido(self):
        record = collect("run_1", val_result(), {"columns": {}}, slm_result(),
                         fmt="csv", dat_ref="2024-04-01")
        salvo = json.loads((self.tmp / "metrics" / "run_1_tb_clientes_csv.json")
                           .read_text(encoding="utf-8"))
        self.assertEqual(salvo, record)

    def test_registro_carrega_linhagem_e_formato(self):
        record = collect("run_1", val_result(), {"columns": {}}, slm_result(),
                         fmt="fixed", dat_ref="2024-04-01")
        self.assertEqual(record["run_id"], "run_1")
        self.assertEqual(record["dat_ref"], "2024-04-01")
        self.assertEqual(record["format"], "fixed")

    def test_score_e_dimensoes_entram_no_registro(self):
        record = collect("run_1", val_result(), {"columns": {}}, slm_result(),
                         fmt="csv")
        self.assertIn("quality_score", record)
        self.assertIn("quality_dimensions", record)
        for dim in ("conformity", "completeness", "uniqueness", "schema_stability"):
            self.assertIn("score_" + dim, record)

    def test_gate_ausente_e_pass(self):
        record = collect("run_1", val_result(), {"columns": {}}, slm_result())
        self.assertEqual(record["gate_status"], "PASS")
        self.assertEqual(record["rows_rejected"], 0)

    def test_gate_bloqueado_e_registrado_com_motivo(self):
        gate = {"status": "BLOCKED", "reason": "reject_pct acima da tolerancia",
                "detail": "vl_limite: 12%"}
        reject = {"rows_rejected": 12, "reject_pct": 12.0, "limit_pct": 5.0,
                  "by_column": {"vl_limite": 12}}
        record = collect("run_1", val_result(), {"columns": {}}, slm_result(),
                         reject_report=reject, gate=gate)
        self.assertEqual(record["gate_status"], "BLOCKED")
        self.assertEqual(record["rows_rejected"], 12)
        self.assertEqual(record["rejects_by_column"], {"vl_limite": 12})

    def test_media_de_nulos_vem_do_profiling(self):
        payload = {"columns": {"a": {"null_pct": 10.0}, "b": {"null_pct": 0.0}},
                   "profiling_ms": 42}
        record = collect("run_1", val_result(), payload, slm_result())
        self.assertEqual(record["avg_null_pct"], 5.0)
        self.assertEqual(record["profiling_ms"], 42)

    def test_slm_pulada_nao_impede_a_metrica(self):
        record = collect("run_1", val_result(), {"columns": {}},
                         {"status": "SKIPPED"})
        self.assertEqual(record["slm_status"], "SKIPPED")
        self.assertEqual(record["slm_inference_ms"], 0)


class TestSaveSummary(PersistenciaBase):

    def test_consolidado_e_gravado_com_o_run_id_no_nome(self):
        m = collect("run_1", val_result(), {"columns": {}}, slm_result())
        nome = save_summary("run_1", [m])
        self.assertEqual(nome, "run_1_summary.json")
        self.assertTrue((self.tmp / "metrics" / nome).exists())

    def test_consolidado_contem_todas_as_tabelas(self):
        metricas = [
            collect("run_1", val_result(table="tb_clientes"), {"columns": {}}, slm_result()),
            collect("run_1", val_result(table="tb_transacoes"), {"columns": {}}, slm_result()),
        ]
        save_summary("run_1", metricas)
        salvo = json.loads((self.tmp / "metrics" / "run_1_summary.json")
                           .read_text(encoding="utf-8"))
        self.assertEqual([r["table"] for r in salvo],
                         ["tb_clientes", "tb_transacoes"])


class TestGenerateReport(PersistenciaBase):

    def _report(self, metricas):
        nome = generate_report(metricas)
        return nome, (self.tmp / "reports" / nome).read_text(encoding="utf-8")

    def test_devolve_o_nome_do_objeto_e_nao_um_path(self):
        m = collect("run_1", val_result(), {"columns": {}}, slm_result())
        nome, _ = self._report([m])
        self.assertIsInstance(nome, str)
        self.assertEqual(nome, "pipeline_report.md")

    def test_relatorio_lista_a_tabela_e_o_score(self):
        m = collect("run_1", val_result(), {"columns": {}}, slm_result())
        _, texto = self._report([m])
        self.assertIn("tb_clientes", texto)
        self.assertIn(str(m["quality_score"]), texto)

    def test_relatorio_traz_as_dimensoes_com_os_pesos_reais(self):
        m = collect("run_1", val_result(), {"columns": {}}, slm_result())
        _, texto = self._report([m])
        for cabecalho in ("Conformidade (40%)", "Completude (25%)",
                          "Unicidade (20%)", "Estabilidade (15%)"):
            self.assertIn(cabecalho, texto)

    def test_secao_de_gate_aparece_quando_ha_bloqueio(self):
        m = collect("run_1", val_result(), {"columns": {}}, slm_result(),
                    gate={"status": "BLOCKED", "reason": "tolerancia",
                          "detail": "vl: 12%"},
                    reject_report={"rows_rejected": 12, "reject_pct": 12.0,
                                   "limit_pct": 5.0, "by_column": {"vl": 12}})
        _, texto = self._report([m])
        self.assertIn("Gate de Tipagem", texto)
        self.assertIn("BLOCKED", texto)

    def test_sem_bloqueio_nao_ha_secao_de_gate(self):
        m = collect("run_1", val_result(), {"columns": {}}, slm_result())
        _, texto = self._report([m])
        self.assertNotIn("Gate de Tipagem", texto)

    def test_desempenho_da_slm_aparece_quando_houve_inferencia(self):
        m = collect("run_1", val_result(), {"columns": {}}, slm_result())
        _, texto = self._report([m])
        self.assertIn("Desempenho da SLM", texto)
        self.assertIn("phi4", texto)

    def test_sem_inferencia_o_relatorio_diz_que_nao_houve(self):
        m = collect("run_1", val_result(), {"columns": {}}, {"status": "SKIPPED"})
        _, texto = self._report([m])
        self.assertIn("Nenhuma inferencia bem-sucedida", texto)

    def test_aviso_de_draft_da_ia_esta_sempre_no_rodape(self):
        m = collect("run_1", val_result(), {"columns": {}}, slm_result())
        _, texto = self._report([m])
        self.assertIn("AI_METADATA_STATUS: DRAFT", texto)

    def test_dlq_e_contado_no_resumo(self):
        m = collect("run_1", val_result(status="DLQ"), {"columns": {}}, slm_result())
        _, texto = self._report([m])
        self.assertIn("[DLQ]", texto)
        self.assertIn("**Com DLQ:** 1", texto)

    def test_run_sem_metrica_nao_quebra_o_relatorio(self):
        _, texto = self._report([])
        self.assertIn("N/A", texto)


if __name__ == "__main__":
    unittest.main()
