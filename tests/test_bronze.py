"""
tests/test_bronze.py — Testes para BronzeUploader (arquivo bruto -> Volume UC).

Todos os testes usam mocks — nenhuma chamada real ao Databricks.
Cobre: detect_format, upload_raw, register_raw, describe_bronze,
       upload_and_register_raw, publish_bronze, get_bronze_uploader.
"""
import json, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.connectors.bronze_uploader import (
    BronzeUploader, publish_bronze, get_bronze_uploader,
)

HOST = "https://adb-1234.azuredatabricks.net"
TOKEN = "dapi_test_token"
WID   = "abc123warehouse"
VOL   = "landing"


def _u(**kw):
    d = dict(host=HOST, token=TOKEN, warehouse_id=WID, volume=VOL,
             catalog="nimbus", schema="bronze")
    d.update(kw)
    return BronzeUploader(**d)


def _ok(data=None, status_code=200):
    m = MagicMock()
    m.ok = (status_code < 400)
    m.status_code = status_code
    m.text = json.dumps(data or {})
    m.json.return_value = data or {}
    return m


def _sql_ok(rows=None):
    return {"status": {"state": "SUCCEEDED"}, "result": {"data_array": rows or []}}


def _csv(tmp: Path, name="tb_clientes.csv") -> Path:
    p = tmp / name
    p.write_text("cd_cliente,nm_cliente\nC1,Ana\n", encoding="utf-8")
    return p


# ═════════════════════════════════════════════════════════════════════════════
# TestDetectFormat
# ═════════════════════════════════════════════════════════════════════════════
class TestDetectFormat(unittest.TestCase):
    def test_csv(self):
        self.assertEqual(BronzeUploader.detect_format("tb.csv"), "csv")

    def test_json(self):
        self.assertEqual(BronzeUploader.detect_format("tb.json"), "json")

    def test_fixed_width_txt(self):
        self.assertEqual(BronzeUploader.detect_format("tb.txt"), "text")

    def test_unknown_returns_none(self):
        self.assertIsNone(BronzeUploader.detect_format("tb.layout"))

    def test_case_insensitive(self):
        self.assertEqual(BronzeUploader.detect_format("TB.CSV"), "csv")


# ═════════════════════════════════════════════════════════════════════════════
# TestUploadRaw
# ═════════════════════════════════════════════════════════════════════════════
class TestUploadRaw(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.u   = _u()
        self.csv = _csv(self.tmp)

    def test_file_not_found_raises(self):
        with self.assertRaises(FileNotFoundError):
            self.u.upload_raw(Path("/nao/existe.csv"))

    def test_keeps_original_filename(self):
        urls = []
        def cap(url, **kw): urls.append(url); return _ok()
        with patch.object(self.u._session, "put", side_effect=cap):
            self.u.upload_raw(self.csv, "tb_clientes", dat_ref="2024-01-15")
        self.assertTrue(any("tb_clientes.csv" in u for u in urls),
            "Bronze deve preservar o nome original, nao part-YYYY-MM-DD.parquet")

    def test_path_includes_dat_ref(self):
        urls = []
        def cap(url, **kw): urls.append(url); return _ok()
        with patch.object(self.u._session, "put", side_effect=cap):
            self.u.upload_raw(self.csv, "tb_clientes", dat_ref="2024-06-15")
        self.assertTrue(any("dat_ref=2024-06-15" in u for u in urls))

    def test_path_uses_bronze_schema(self):
        urls = []
        def cap(url, **kw): urls.append(url); return _ok()
        with patch.object(self.u._session, "put", side_effect=cap):
            self.u.upload_raw(self.csv, "tb_clientes", dat_ref="2024-01-01")
        self.assertTrue(any("/Volumes/nimbus/bronze/landing/tb_clientes" in u for u in urls))

    def test_returns_volume_folder(self):
        with patch.object(self.u._session, "put", return_value=_ok()):
            folder = self.u.upload_raw(self.csv, "tb_clientes", dat_ref="2024-01-01")
        self.assertEqual(folder, "/Volumes/nimbus/bronze/landing/tb_clientes")

    def test_api_error_raises(self):
        with patch.object(self.u._session, "put", return_value=_ok(status_code=403)):
            with self.assertRaises(RuntimeError):
                self.u.upload_raw(self.csv, "tb_clientes", dat_ref="2024-01-01")


# ═════════════════════════════════════════════════════════════════════════════
# TestRegisterRaw
# ═════════════════════════════════════════════════════════════════════════════
class TestRegisterRaw(unittest.TestCase):
    def setUp(self): self.u = _u()

    def test_ctas_uses_read_files(self):
        stmts = []
        def cap(s, **kw): stmts.append(s); return _sql_ok()
        with patch.object(self.u, "_sql", side_effect=cap):
            self.u.register_raw("tb_clientes", "/Volumes/nimbus/bronze/landing/tb_clientes", "csv")
        ctas = next(s for s in stmts if "CREATE OR REPLACE TABLE" in s)
        self.assertIn("read_files", ctas)
        self.assertIn("inferColumnTypes => false", ctas)
        self.assertIn("header => true", ctas)

    def test_adds_ingest_provenance_columns(self):
        stmts = []
        def cap(s, **kw): stmts.append(s); return _sql_ok()
        with patch.object(self.u, "_sql", side_effect=cap):
            self.u.register_raw("tb_clientes", "/Volumes/...", "csv", run_id="run_20240115_000000_abc")
        ctas = next(s for s in stmts if "CREATE OR REPLACE TABLE" in s)
        self.assertIn("_ingest_file", ctas)
        self.assertIn("_ingest_time", ctas)
        self.assertIn("_ingest_run_id", ctas)
        self.assertIn("run_20240115_000000_abc", ctas)

    def test_json_skips_csv_header_option(self):
        stmts = []
        def cap(s, **kw): stmts.append(s); return _sql_ok()
        with patch.object(self.u, "_sql", side_effect=cap):
            self.u.register_raw("tb_clientes", "/Volumes/...", "json")
        ctas = next(s for s in stmts if "CREATE OR REPLACE TABLE" in s)
        self.assertNotIn("header => true", ctas)

    def test_returns_full_name_in_bronze_schema(self):
        with patch.object(self.u, "_sql", return_value=_sql_ok()):
            full = self.u.register_raw("tb_clientes", "/Volumes/...", "csv")
        self.assertEqual(full, "nimbus.bronze.tb_clientes")

    def test_table_name_has_no_suffix(self):
        self.assertEqual(self.u.bronze_table("tb_clientes"), "tb_clientes")


# ═════════════════════════════════════════════════════════════════════════════
# TestDescribeBronze
# ═════════════════════════════════════════════════════════════════════════════
class TestDescribeBronze(unittest.TestCase):
    def test_comment_and_layer_tag(self):
        u = _u()
        stmts = []
        def cap(s, **kw): stmts.append(s); return _sql_ok()
        with patch.object(u, "_sql", side_effect=cap):
            count = u.describe_bronze("tb_clientes")
        self.assertGreater(count, 0)
        self.assertTrue(any("COMMENT ON TABLE" in s for s in stmts))
        self.assertTrue(any("nimbus_layer" in s and "bronze" in s for s in stmts))
        self.assertTrue(any("validated" in s and "false" in s for s in stmts))


# ═════════════════════════════════════════════════════════════════════════════
# TestUploadAndRegisterRaw
# ═════════════════════════════════════════════════════════════════════════════
class TestUploadAndRegisterRaw(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.u   = _u()
        self.csv = _csv(self.tmp)

    def test_unknown_format_uploads_without_table(self):
        layout = self.tmp / "tb_clientes.layout"
        layout.write_text("colspecs", encoding="utf-8")
        with patch.object(self.u, "upload_raw", return_value="/Volumes/...") as up, \
             patch.object(self.u, "register_raw") as reg:
            result = self.u.upload_and_register_raw(layout, table_name="tb_clientes")
        up.assert_called_once()
        reg.assert_not_called()
        self.assertIsNone(result)

    def test_csv_registers_and_describes(self):
        with patch.object(self.u, "upload_raw", return_value="/Volumes/..."), \
             patch.object(self.u, "register_raw", return_value="nimbus.bronze.tb_clientes") as reg, \
             patch.object(self.u, "describe_bronze") as desc:
            full = self.u.upload_and_register_raw(self.csv, table_name="tb_clientes")
        reg.assert_called_once()
        desc.assert_called_once()
        self.assertEqual(full, "nimbus.bronze.tb_clientes")

    def test_skip_comments(self):
        with patch.object(self.u, "upload_raw", return_value="/Volumes/..."), \
             patch.object(self.u, "register_raw", return_value="nimbus.bronze.tb_clientes"), \
             patch.object(self.u, "describe_bronze") as desc:
            self.u.upload_and_register_raw(self.csv, table_name="tb_clientes", skip_comments=True)
        desc.assert_not_called()


# ═════════════════════════════════════════════════════════════════════════════
# TestPublishBronze
# ═════════════════════════════════════════════════════════════════════════════
class TestPublishBronze(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.csv = _csv(self.tmp)

    def test_disabled_when_flag_false(self):
        with patch("config.DATABRICKS_BRONZE_UPLOAD", False):
            result = publish_bronze(self.csv, "tb_clientes")
        self.assertEqual(result["status"], "DISABLED")
        self.assertEqual(result["layer"], "bronze")

    def test_never_raises(self):
        with patch("config.DATABRICKS_BRONZE_UPLOAD", True), \
             patch("src.connectors.bronze_uploader.get_bronze_uploader",
                   side_effect=Exception("boom")):
            result = publish_bronze(self.csv, "tb_clientes")
        self.assertEqual(result["status"], "ERROR")
        self.assertIsNotNone(result["error"])

    def test_ok_when_registered(self):
        up = MagicMock()
        up.upload_and_register_raw.return_value = "nimbus.bronze.tb_clientes"
        with patch("config.DATABRICKS_BRONZE_UPLOAD", True), \
             patch("src.connectors.bronze_uploader.get_bronze_uploader", return_value=up):
            result = publish_bronze(self.csv, "tb_clientes", run_id="run_20240115_120000_abc")
        self.assertEqual(result["status"], "OK")
        self.assertEqual(result["target"], "nimbus.bronze.tb_clientes")
        self.assertEqual(up.upload_and_register_raw.call_args.kwargs["dat_ref"], "2024-01-15")

    def test_uploaded_when_no_table(self):
        up = MagicMock()
        up.upload_and_register_raw.return_value = None
        with patch("config.DATABRICKS_BRONZE_UPLOAD", True), \
             patch("src.connectors.bronze_uploader.get_bronze_uploader", return_value=up):
            result = publish_bronze(self.csv, "tb_clientes")
        self.assertEqual(result["status"], "UPLOADED")


class TestGetBronzeUploader(unittest.TestCase):
    def test_uses_bronze_schema_from_config(self):
        with patch("config.DATABRICKS_HOST", HOST), \
             patch("config.DATABRICKS_TOKEN", TOKEN), \
             patch("config.DATABRICKS_WAREHOUSE_ID", WID), \
             patch("config.DATABRICKS_BRONZE_VOLUME", VOL), \
             patch("config.DATABRICKS_CATALOG", "nimbus"), \
             patch("config.DATABRICKS_BRONZE_SCHEMA", "bronze"):
            u = get_bronze_uploader()
        self.assertEqual(u._catalog, "nimbus")
        self.assertEqual(u._schema, "bronze")


if __name__ == "__main__":
    unittest.main()
