"""
tests/test_steward_tags_quarantine.py - Evidencia do Data Steward no catalogo
e contrato de retorno da publicacao de quarentena.

Cobre dois defeitos que so aparecem com credencial valida:
    1. _table_tags() nao aplicava validated_by/validated_at (atributo errado),
    entao a evidencia de HITL nunca chegava ao Unity Catalog.
    2. publish_quarantine() estourava UnboundLocalError em falha de upload,
    em vez de devolver status ERROR.
    
Todos os testes usam mocks - nenhuma chamada real ao Databricks.
"""
import sys, tempfile, unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.connectors.bronze_uploader import publish_quarantine
from src.connectors.databricks_uploader import DatabricksUploader
from src.validation.contracts import DataContract, TolerancePolicy

HOST  = "https://adb-1234.azuredatabricks.net"
TOKEN = "dapi_test_token"
WID   = "abc123warehouse"


def _contract(**kw) -> DataContract:
    d = dict(
        table       = "tb_clientes",
        description = "Cadastro de clientes",
        owner       = "dados@banco.com",
        version     = "1.0.0",
        tolerance   = TolerancePolicy(),
        schema      = [],
    )
    d.update(kw)
    return DataContract(**d)

def _uploader() -> DatabricksUploader:
    return DatabricksUploader(host=HOST, token=TOKEN, warehouse_id=WID,
                              volume="landing", catalog="nimbus", schema="silver")

class TestStewardTags(unittest.TestCase):
    """A promocao do manifesto tem que virar tag de tabela no catalogo."""

    def test_validated_by_e_at_viram_tags(self):
        contract = _contract(manifest_status="VALIDATED",
                             validated_by="Renan Apolinario",
                             validated_at="2026-08-12T16:53:00")
        tags = _uploader()._table_tags(contract)
        self.assertEqual(tags["manifest_status"], "VALIDATED")
        self.assertEqual(tags["validated_by"], "Renan Apolinario")
        self.assertEqual(tags["validated_at"], "2026-08-12T16:53:00")

    def test_draft_nao_gera_evidencia(self):
        tags = _uploader()._table_tags(_contract())
        self.assertEqual(tags["manifest_status"], "DRAFT")
        self.assertNotIn("validated_by", tags)
        self.assertNotIn("validated_at", tags)

    def test_tags_base_preservadas(self):
        tags = _uploader()._table_tags(_contract(validated_by="Renan Apolinario"))
        self.assertEqual(tags["owner"], "dados@banco.com")
        self.assertEqual(tags["contract_version"], "1.0.0")

class TestPublishQuarantine(unittest.TestCase):
    """publish_quarantine nunca deve levantar excecao para o runner."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.file = self.tmp / "reject_tb_clientes.csv"
        self.file.write_text("id_cliente,erro\n,tipo\n", encoding="utf-8")

    def _enabled(self):
        return patch.multiple("config", DATABRICKS_QUARANTINE_UPLOAD=True,
                              DATABRICKS_HOST=HOST, DATABRICKS_TOKEN=TOKEN,
                              DATABRICKS_WAREHOUSE_ID=WID, create=True)

    def test_erro_de_upload_devolve_status_erro(self):
        with self._enabled(), patch("src.connectors.bronze_uploader.get_quarantine_uploader",
                                    side_effect=RuntimeError("boom")):
            result = publish_quarantine(self.file, "tb_clientes")
            self.assertEqual(result["status"], "ERROR")
            self.assertIn("boom", result["error"])
            self.assertEqual(result["layer"], "quarantine")

    def test_ok_quando_registrada(self):
        up = MagicMock()
        up.upload_and_register_raw.return_value = "nimbus.bronze.quarantine_tb_clientes"
        with self._enabled(), patch("src.connectors.bronze_uploader.get_quarantine_uploader",
                                    return_value=up):
            result = publish_quarantine(self.file, "tb_clientes",
                                        run_id="run_20240115_120000_abc")
        self.assertEqual(result["status"], "OK")
        self.assertEqual(result["target"], "nimbus.bronze.quarantine_tb_clientes")
        self.assertEqual(up.upload_and_register_raw.call_args.kwargs["dat_ref"], "2024-01-15")

    def test_arquivo_inexistente_nao_e_erro(self):
        with self._enabled():
            result = publish_quarantine(self.tmp / "nao_existe.csv", "tb_clientes")
        self.assertEqual(result["status"], "NO_DATA")

    def  test_desligado_por_flag(self):
        with patch.multiple("config", DATABRICKS_QUARANTINE_UPLOAD=False,
                            DATABRICKS_BRONZE_UPLOAD=False, create=True):
            result = publish_quarantine(self.file, "tb_clientes")
        self.assertEqual(result["status"], "DISABLED")

if __name__ == "__main__":
    unittest.main()

