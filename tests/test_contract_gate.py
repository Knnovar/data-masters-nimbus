"""
tests/test_contract_gate.py - Contrato ilegivel bloqueia a publicacao.

Sem contrato nao existe cast dirigido pelo Manifest, gate de governanca nem
mascara de PII na quarentena. Antes destes testes, a falha ao reconstruir o
contrato dentro do run_scenario apenas imprimia um aviso e a tabela seguia para
a Silver com `contract=None`, aparecendo como liberada no resumo. O bloqueio
CONTRACT_UNREADABLE fecha esse caminho.
"""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

import run_pipeline
from run_pipeline import gate_label, pipeline_exit_code
from src.storage.storage import LocalStorage
from src.validation.validator import ValidationResult

_LAYERS = ["bronze", "silver", "gold", "quarantine", "contracts", "metrics", "reports"]

_CONTRATO_QUEBRADO = "table: tb_clientes\nschema: [ {name: id,\n"


class TestContratoIlegivelBloqueia(unittest.TestCase):
    """run_scenario com contrato presente e nao reconstruivel."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.storage = LocalStorage({l: base / l for l in _LAYERS})
        self.storage.write("bronze", "tb_clientes.csv", pd.DataFrame({"id": [1, 2]}))
        self.storage.write_text("contracts", "tb_clientes.yaml", _CONTRATO_QUEBRADO)

        self.coletado = []
        self.patches = [
            mock.patch.object(run_pipeline, "get_storage", return_value=self.storage),
            mock.patch.object(run_pipeline, "generate_all", return_value=[{
                "table": "tb_clientes",
                "filename": "tb_clientes.csv",
                "contract_filename": "tb_clientes.yaml",
            }]),
            mock.patch.object(run_pipeline, "validate", return_value=ValidationResult(
                table="tb_clientes", status="PASS", rows_total=2, rows_valid=2)),
            mock.patch.object(run_pipeline, "profile"),
            mock.patch.object(run_pipeline, "enrich"),
            mock.patch.object(run_pipeline, "collect", side_effect=self._collect),
            mock.patch("src.connectors.bronze_uploader.publish_bronze",
                       return_value={"table": "tb_clientes", "layer": "bronze",
                                     "status": "DISABLED", "target": None, "error": None}),
        ]
        self.mocks = {p.attribute if hasattr(p, "attribute") else p.target: p.start()
                      for p in self.patches}

    def tearDown(self):
        for p in self.patches:
            p.stop()
        self.tmp.cleanup()

    def _collect(self, run_id, val_result, profiler_payload, slm_result, **kw):
        gate = kw.get("gate") or {}
        registro = {
            "table": val_result.table,
            "validation_status": val_result.status,
            "gate_status": gate.get("status"),
            "gate_reason": gate.get("reason"),
            "gate_detail": gate.get("detail"),
        }
        self.coletado.append(registro)
        return registro

    def _run(self):
        return run_pipeline.run_scenario("baseline", "run_20250801_000000",
                                         fmt="csv", dat_ref="2025-08-01")

    def test_gate_bloqueia_com_razao_de_contrato(self):
        metrics, _ = self._run()
        self.assertEqual(metrics[0]["gate_status"], "BLOCKED")
        self.assertEqual(metrics[0]["gate_reason"], "CONTRACT_UNREADABLE")
        self.assertIn("tb_clientes.yaml", metrics[0]["gate_detail"])

    def test_nada_e_promovido_para_a_silver(self):
        self._run()
        self.assertEqual(self.storage.list("silver"), [])

    def test_profiling_e_slm_nao_executam(self):
        self._run()
        self.mocks["profile"].assert_not_called()
        self.mocks["enrich"].assert_not_called()

    def test_publicacao_da_silver_registrada_como_bloqueada(self):
        _, publications = self._run()
        silver = [p for p in publications if p.get("layer") == "silver"]
        self.assertEqual(len(silver), 1)
        self.assertEqual(silver[0]["status"], "BLOCKED")

    def test_exit_code_2(self):
        metrics, publications = self._run()
        self.assertEqual(pipeline_exit_code(metrics, publications), 2)

    def test_ledger_registra_a_carga_como_bloqueada(self):
        self._run()
        from src.ingestion.idempotency import previous_load
        prev = previous_load(self.storage, "tb_clientes", "2025-08-01", "csv")
        self.assertEqual(prev["status"], "BLOCKED")


class TestContratoValidoSegue(TestContratoIlegivelBloqueia):
    """Contrato reconstruivel nao entra no bloqueio: o caminho normal continua."""

    def setUp(self):
        super().setUp()
        self.storage.write_text("contracts", "tb_clientes.yaml", (
            "table: tb_clientes\n"
            "description: clientes\n"
            "owner: time\n"
            "version: 1.0.0\n"
            "schema:\n"
            "  - name: id\n"
            "    type: integer\n"
            "    nullable: false\n"
            "    primary_key: true\n"
        ))
        self.mocks["profile"].return_value = {
            "table": "tb_clientes", "rows": 2, "profiling_ms": 1, "columns": {}}
        self.mocks["enrich"].return_value = {
            "table": "tb_clientes", "status": "SKIPPED", "inference_ms": 0, "documentation": ""}

    def test_gate_bloqueia_com_razao_de_contrato(self):
        metrics, _ = self._run()
        self.assertNotEqual(metrics[0]["gate_reason"], "CONTRACT_UNREADABLE")

    def test_nada_e_promovido_para_a_silver(self):
        self._run()
        self.assertIn("tb_clientes.parquet", self.storage.list("silver"))

    def test_profiling_e_slm_nao_executam(self):
        self._run()
        self.mocks["profile"].assert_called_once()
        self.mocks["enrich"].assert_called_once()

    def test_publicacao_da_silver_registrada_como_bloqueada(self):
        _, publications = self._run()
        silver = [p for p in publications if p.get("layer") == "silver"]
        self.assertEqual(silver, [])

    def test_exit_code_2(self):
        metrics, publications = self._run()
        self.assertEqual(pipeline_exit_code(metrics, publications), 0)

    def test_ledger_registra_a_carga_como_bloqueada(self):
        self._run()
        from src.ingestion.idempotency import previous_load
        prev = previous_load(self.storage, "tb_clientes", "2025-08-01", "csv")
        self.assertEqual(prev["status"], "PASS")


class TestRotuloDoResumo(unittest.TestCase):

    def test_contrato_ilegivel_tem_rotulo_proprio(self):
        self.assertEqual(
            gate_label({"gate_status": "BLOCKED", "gate_reason": "CONTRACT_UNREADABLE"}),
            "[CONTRATO]")

    def test_demais_rotulos_preservados(self):
        self.assertEqual(
            gate_label({"gate_status": "BLOCKED", "gate_reason": "VALIDATION_DLQ"}),
            "[QUARENTENA]")
        self.assertEqual(
            gate_label({"gate_status": "BLOCKED", "gate_reason": "REJECT_ABOVE_TOLERANCE"}),
            "[QUALIDADE]")
        self.assertEqual(gate_label({"gate_status": "PASS"}), "[LIBERADA]")


if __name__ == "__main__":
    unittest.main(verbosity=2)
