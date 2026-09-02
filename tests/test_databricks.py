"""
tests/test_databricks.py — Testes para DatabricksUploader (Volumes + Files API).

Todos os testes usam mocks — nenhuma chamada real ao Databricks.
Cobre: DiagnoseResult, diagnose(), upload_parquet_to_folder() via Files API,
       register_or_refresh() via CTAS, populate_column_comments(),
       apply_table_metadata(), upload_and_register(), publish_table(),
       upload_silver_table(), dat_ref_from_run_id().
"""
import json, sys, tempfile, unittest
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.connectors.databricks_uploader import (
    DatabricksUploader, DiagnoseResult,
    publish_table, upload_silver_table, dat_ref_from_run_id,
)

HOST = "https://adb-1234.azuredatabricks.net"
TOKEN = "dapi_test_token"
WID   = "abc123warehouse"
VOL   = "landing"

SAMPLE = pd.DataFrame({"id": ["C1","C2"], "vl": [1.0, 2.0]})


def _u(**kw):
    d = dict(host=HOST, token=TOKEN, warehouse_id=WID, volume=VOL,
             catalog="workspace", schema="nimbus")
    d.update(kw)
    return DatabricksUploader(**d)


def _pq(tmp: Path, name="tb_test.parquet") -> Path:
    p = tmp / name
    SAMPLE.to_parquet(p, index=False)
    return p


def _ok(data=None, status_code=200):
    m = MagicMock()
    m.ok = (status_code < 400)
    m.status_code = status_code
    m.text = json.dumps(data or {})
    m.json.return_value = data or {}
    return m


def _sql_ok(rows=None):
    return {"status": {"state": "SUCCEEDED"}, "result": {"data_array": rows or []}}


# ═════════════════════════════════════════════════════════════════════════════
# TestInit
# ═════════════════════════════════════════════════════════════════════════════
class TestInit(unittest.TestCase):
    def test_empty_host_raises(self):
        with self.assertRaises(ValueError) as ctx:
            DatabricksUploader(host="", token=TOKEN, warehouse_id=WID, volume=VOL)
        self.assertIn("DATABRICKS_HOST", str(ctx.exception))

    def test_host_missing_scheme_raises(self):
        with self.assertRaises(ValueError):
            DatabricksUploader(host="adb-1234.azuredatabricks.net", token=TOKEN,
                               warehouse_id=WID, volume=VOL)

    def test_empty_warehouse_raises(self):
        with self.assertRaises(ValueError) as ctx:
            DatabricksUploader(host=HOST, token=TOKEN, warehouse_id="", volume=VOL)
        self.assertIn("DATABRICKS_WAREHOUSE_ID", str(ctx.exception))

    def test_empty_volume_raises(self):
        with self.assertRaises(ValueError) as ctx:
            DatabricksUploader(host=HOST, token=TOKEN, warehouse_id=WID, volume="")
        self.assertIn("DATABRICKS_VOLUME", str(ctx.exception))

    def test_valid_with_token(self):
        u = _u()
        self.assertIsInstance(u, DatabricksUploader)
        self.assertIn(f"Bearer {TOKEN}", u._session.headers.get("Authorization", ""))

    def test_trailing_slash_stripped(self):
        u = _u(host="https://host.com/")
        self.assertEqual(u._url("x"), "https://host.com/api/2.0/x")

    def test_volume_dir_format(self):
        u = _u()
        self.assertEqual(u._volume_dir("tb_clientes"),
                         "/Volumes/workspace/nimbus/landing/tb_clientes")

    def test_volume_dir_invalid_name_raises(self):
        u = _u()
        with self.assertRaises(ValueError):
            u._volume_dir("tabela-com-hifem")

    def test_partition_dir_format(self):
        u = _u()
        d = u._partition_dir("tb_test", "2024-01-15")
        self.assertEqual(d, "/Volumes/workspace/nimbus/landing/tb_test/dat_ref=2024-01-15")

    def test_dat_ref_invalid_raises(self):
        u = _u()
        with self.assertRaises(ValueError):
            u._dat_ref("15/01/2024")


# ═════════════════════════════════════════════════════════════════════════════
# TestDiagnoseResult
# ═════════════════════════════════════════════════════════════════════════════
class TestDiagnoseResult(unittest.TestCase):
    def test_all_ok_true(self):
        r = DiagnoseResult()
        r.add("1", True, "OK"); r.add("2", True, "OK")
        self.assertTrue(r.all_ok)

    def test_all_ok_false(self):
        r = DiagnoseResult()
        r.add("1", True, "OK"); r.add("2", False, "FAIL")
        self.assertFalse(r.all_ok)

    def test_levels_stored(self):
        r = DiagnoseResult()
        r.add("token", True, "autenticado")
        self.assertIn("token", r.levels)
        self.assertTrue(r.levels["token"]["ok"])


# ═════════════════════════════════════════════════════════════════════════════
# TestUploadParquetToFolder — Files API
# ═════════════════════════════════════════════════════════════════════════════
class TestUploadParquetToFolder(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.u   = _u()
        self.pq  = _pq(self.tmp)

    def test_file_not_found_raises(self):
        with self.assertRaises(FileNotFoundError):
            self.u.upload_parquet_to_folder(Path("/nao/existe.parquet"))

    def test_returns_volume_folder_path(self):
        with patch.object(self.u._session, "put", return_value=_ok()):
            folder = self.u.upload_parquet_to_folder(self.pq, "tb_test", dat_ref="2024-01-15")
        self.assertIn("tb_test", folder)
        self.assertIn("/Volumes/", folder)

    def test_uses_files_api_put(self):
        urls = []
        def capture(url, **kw): urls.append(url); return _ok()
        with patch.object(self.u._session, "put", side_effect=capture):
            self.u.upload_parquet_to_folder(self.pq, "tb_test", dat_ref="2024-01-15")
        self.assertTrue(any("/api/2.0/fs/files" in u for u in urls),
            "Deve usar Files API (/api/2.0/fs/files), nao DBFS API")

    def test_path_includes_dat_ref_partition(self):
        urls = []
        def capture(url, **kw): urls.append(url); return _ok()
        with patch.object(self.u._session, "put", side_effect=capture):
            self.u.upload_parquet_to_folder(self.pq, "tb_test", dat_ref="2024-06-15")
        self.assertTrue(any("dat_ref=2024-06-15" in u for u in urls),
            "Path deve incluir particao Hive dat_ref=YYYY-MM-DD")

    def test_path_includes_volume_root(self):
        urls = []
        def capture(url, **kw): urls.append(url); return _ok()
        with patch.object(self.u._session, "put", side_effect=capture):
            self.u.upload_parquet_to_folder(self.pq, "tb_clientes", dat_ref="2024-01-01")
        self.assertTrue(any("/Volumes/workspace/nimbus/landing/tb_clientes" in u for u in urls))

    def test_sends_binary_data(self):
        data_sent = []
        def capture(url, data=None, **kw): data_sent.append(data); return _ok()
        with patch.object(self.u._session, "put", side_effect=capture):
            self.u.upload_parquet_to_folder(self.pq, "tb_test", dat_ref="2024-01-01")
        self.assertGreater(len(data_sent), 0)
        self.assertIsInstance(data_sent[0], bytes)

    def test_no_dbfs_create_call(self):
        """Garante que nao usa a API DBFS antiga (create/add-block/close)."""
        post_urls = []
        def capture_post(url, **kw): post_urls.append(url); return _ok()
        with patch.object(self.u._session, "put", return_value=_ok()), \
             patch.object(self.u._session, "post", side_effect=capture_post):
            self.u.upload_parquet_to_folder(self.pq, "tb_test", dat_ref="2024-01-01")
        self.assertFalse(any("dbfs/create" in u for u in post_urls),
            "Nao deve chamar dbfs/create — upload usa Files API PUT")

    def test_api_error_raises(self):
        with patch.object(self.u._session, "put", return_value=_ok(status_code=403)):
            with self.assertRaises(RuntimeError) as ctx:
                self.u.upload_parquet_to_folder(self.pq, "tb_test", dat_ref="2024-01-01")
        self.assertIn("Files API", str(ctx.exception))

    def test_overwrite_param_sent(self):
        params_sent = []
        def capture(url, params=None, **kw): params_sent.append(params or {}); return _ok()
        with patch.object(self.u._session, "put", side_effect=capture):
            self.u.upload_parquet_to_folder(self.pq, "tb_test", dat_ref="2024-01-01")
        self.assertTrue(any(p.get("overwrite") in ("true", True) for p in params_sent))

    def test_idempotent_same_date_overwrites(self):
        """Mesma dat_ref envia overwrite=true — reprocessamento e seguro."""
        params_list = []
        def capture(url, params=None, **kw): params_list.append(params or {}); return _ok()
        with patch.object(self.u._session, "put", side_effect=capture):
            self.u.upload_parquet_to_folder(self.pq, "tb_test", dat_ref="2024-01-01")
            self.u.upload_parquet_to_folder(self.pq, "tb_test", dat_ref="2024-01-01")
        for p in params_list:
            self.assertEqual(str(p.get("overwrite","")).lower(), "true")


# ═════════════════════════════════════════════════════════════════════════════
# TestRegisterOrRefresh — CTAS via read_files
# ═════════════════════════════════════════════════════════════════════════════
class TestRegisterOrRefresh(unittest.TestCase):
    def setUp(self): self.u = _u()

    def test_uses_create_or_replace_table(self):
        stmts = []
        def cap(s, **kw): stmts.append(s); return _sql_ok()
        with patch.object(self.u, "_sql", side_effect=cap):
            self.u.register_or_refresh("tb_test", "/Volumes/workspace/nimbus/landing/tb_test")
        self.assertTrue(any("CREATE OR REPLACE TABLE" in s for s in stmts))

    def test_uses_read_files_not_delta_location(self):
        stmts = []
        def cap(s, **kw): stmts.append(s); return _sql_ok()
        with patch.object(self.u, "_sql", side_effect=cap):
            self.u.register_or_refresh("tb_test", "/Volumes/workspace/nimbus/landing/tb_test")
        ctas = next(s for s in stmts if "CREATE OR REPLACE TABLE" in s)
        self.assertIn("read_files", ctas)
        self.assertNotIn("USING DELTA LOCATION", ctas)

    def test_no_convert_to_delta(self):
        """register_or_refresh nao deve chamar CONVERT TO DELTA."""
        stmts = []
        def cap(s, **kw): stmts.append(s); return _sql_ok()
        with patch.object(self.u, "_sql", side_effect=cap):
            self.u.register_or_refresh("tb_test", "/Volumes/workspace/nimbus/landing/tb_test")
        self.assertFalse(any("CONVERT TO DELTA" in s for s in stmts))

    def test_reads_from_volume_path(self):
        stmts = []
        def cap(s, **kw): stmts.append(s); return _sql_ok()
        with patch.object(self.u, "_sql", side_effect=cap):
            self.u.register_or_refresh("tb_clientes", "/Volumes/workspace/nimbus/landing/tb_clientes")
        ctas = next(s for s in stmts if "CREATE OR REPLACE TABLE" in s)
        self.assertIn("/Volumes/workspace/nimbus/landing/tb_clientes", ctas)

    def test_returns_full_table_name(self):
        def cap(s, **kw): return _sql_ok()
        with patch.object(self.u, "_sql", side_effect=cap):
            result = self.u.register_or_refresh("tb_clientes", "/Volumes/...")
        self.assertIn("nimbus", result)
        self.assertIn("tb_clientes", result)

    def test_creates_schema_first(self):
        stmts = []
        def cap(s, **kw): stmts.append(s); return _sql_ok()
        with patch.object(self.u, "_sql", side_effect=cap):
            self.u.register_or_refresh("tb_test", "/Volumes/...")
        self.assertTrue(any("CREATE SCHEMA IF NOT EXISTS" in s for s in stmts))

    def test_parquet_format_specified(self):
        stmts = []
        def cap(s, **kw): stmts.append(s); return _sql_ok()
        with patch.object(self.u, "_sql", side_effect=cap):
            self.u.register_or_refresh("tb_test", "/Volumes/...")
        ctas = next(s for s in stmts if "CREATE OR REPLACE TABLE" in s)
        self.assertIn("parquet", ctas.lower())


# ═════════════════════════════════════════════════════════════════════════════
# TestPopulateColumnComments
# ═════════════════════════════════════════════════════════════════════════════
class TestPopulateColumnComments(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.u   = _u()
        self.pq  = _pq(self.tmp)

    def _contract(self, cols):
        schema = [SimpleNamespace(name=c["name"], description=c.get("desc",""),
                  regulatory_flags=c.get("flags",[]), type="string",
                  nullable=True, business_rules=[]) for c in cols]
        return SimpleNamespace(table="tb_test", version="1.0",
                               manifest_status="VALIDATED", schema=schema,
                               regulatory=None, description=None,
                               business_context=None, owner=None, steward=None, source=None)

    def test_sends_alter_column_comment(self):
        stmts = []
        def cap(s, **kw): stmts.append(s); return _sql_ok()
        with patch.object(self.u, "_sql", side_effect=cap):
            count = self.u.populate_column_comments("tb_test", self.pq)
        self.assertGreater(count, 0)
        self.assertTrue(any("ALTER TABLE" in s and "COMMENT" in s for s in stmts))

    def test_uses_description_from_contract(self):
        stmts = []
        def cap(s, **kw): stmts.append(s); return _sql_ok()
        c = self._contract([{"name":"id","desc":"Identificador unico"},{"name":"vl","desc":"Valor"}])
        with patch.object(self.u, "_sql", side_effect=cap):
            self.u.populate_column_comments("tb_test", self.pq, contract=c)
        self.assertTrue(any("Identificador unico" in s for s in stmts))

    def test_skips_todo_descriptions(self):
        stmts = []
        def cap(s, **kw): stmts.append(s); return _sql_ok()
        c = self._contract([{"name":"id","desc":"# TODO: descrever"},{"name":"vl","desc":""}])
        with patch.object(self.u, "_sql", side_effect=cap):
            self.u.populate_column_comments("tb_test", self.pq, contract=c)
        self.assertFalse(any("# TODO" in s for s in stmts))

    def test_includes_regulatory_flags(self):
        stmts = []
        def cap(s, **kw): stmts.append(s); return _sql_ok()
        c = self._contract([{"name":"id","desc":"CPF","flags":["LGPD_SENSITIVE"]},{"name":"vl","desc":""}])
        with patch.object(self.u, "_sql", side_effect=cap):
            self.u.populate_column_comments("tb_test", self.pq, contract=c)
        self.assertTrue(any("LGPD_SENSITIVE" in s for s in stmts))

    def test_dat_ref_partition_column_commented(self):
        """Coluna dat_ref adicionada pelo pipeline deve ganhar comentario."""
        stmts = []
        def cap(s, **kw): stmts.append(s); return _sql_ok()
        with patch.object(self.u, "_sql", side_effect=cap):
            self.u.populate_column_comments("tb_test", self.pq)
        self.assertTrue(any("dat_ref" in s for s in stmts))

    def test_bad_parquet_returns_zero(self):
        with patch.object(self.u, "_sql"): return_value = _sql_ok()
        count = self.u.populate_column_comments("tb_test", Path("/nao/existe.parquet"))
        self.assertEqual(count, 0)


# ═════════════════════════════════════════════════════════════════════════════
# TestApplyTableMetadata
# ═════════════════════════════════════════════════════════════════════════════
class TestApplyTableMetadata(unittest.TestCase):
    def setUp(self): self.u = _u()

    def _contract(self, desc=None, tags=None, schema_cols=None):
        reg = SimpleNamespace(tags=tags or [], data_classification=None, retention_years=None)
        schema = []
        for c in (schema_cols or []):
            schema.append(SimpleNamespace(name=c["name"],
                          regulatory_flags=c.get("flags",[]),
                          type="string", nullable=True, description="", business_rules=[]))
        return SimpleNamespace(table="tb_test", version="1.0",
                               manifest_status="VALIDATED", schema=schema,
                               regulatory=reg, description=desc,
                               business_context=None, owner=None,
                               steward=None, source=None)

    def test_returns_zero_without_contract(self):
        self.assertEqual(self.u.apply_table_metadata("tb_test", contract=None), 0)

    def test_comment_on_table_sent(self):
        stmts = []
        def cap(s, **kw): stmts.append(s); return _sql_ok()
        c = self._contract(desc="Tabela de clientes")
        with patch.object(self.u, "_sql", side_effect=cap):
            self.u.apply_table_metadata("tb_test", contract=c)
        self.assertTrue(any("COMMENT ON TABLE" in s for s in stmts))

    def test_set_tags_sent_for_regulatory(self):
        stmts = []
        def cap(s, **kw): stmts.append(s); return _sql_ok()
        c = self._contract(tags=["LGPD"])
        with patch.object(self.u, "_sql", side_effect=cap):
            self.u.apply_table_metadata("tb_test", contract=c)
        self.assertTrue(any("SET TAGS" in s for s in stmts))

    def test_skips_todo_tags(self):
        stmts = []
        def cap(s, **kw): stmts.append(s); return _sql_ok()
        c = self._contract(tags=["# TODO: definir tag"])
        with patch.object(self.u, "_sql", side_effect=cap):
            self.u.apply_table_metadata("tb_test", contract=c)
        self.assertFalse(any("# TODO" in s for s in stmts))

    def test_column_tags_sent(self):
        stmts = []
        def cap(s, **kw): stmts.append(s); return _sql_ok()
        c = self._contract(schema_cols=[{"name":"cpf","flags":["LGPD_SENSITIVE"]}])
        with patch.object(self.u, "_sql", side_effect=cap):
            self.u.apply_table_metadata("tb_test", contract=c)
        self.assertTrue(any("ALTER COLUMN" in s and "SET TAGS" in s for s in stmts))


# ═════════════════════════════════════════════════════════════════════════════
# TestPublishTable
# ═════════════════════════════════════════════════════════════════════════════
class TestPublishTable(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.pq  = _pq(self.tmp)

    def test_returns_disabled_when_auto_upload_false(self):
        with patch("config.DATABRICKS_AUTO_UPLOAD", False):
            result = publish_table(self.pq, "tb_test")
        self.assertEqual(result["status"], "DISABLED")
        self.assertIsNone(result["error"])

    def test_returns_error_on_exception(self):
        with patch("config.DATABRICKS_AUTO_UPLOAD", True), \
             patch("src.connectors.databricks_uploader.upload_silver_table",
                   side_effect=RuntimeError("boom")):
            result = publish_table(self.pq, "tb_test")
        self.assertEqual(result["status"], "ERROR")
        self.assertIsNotNone(result["error"])

    def test_never_raises_exception(self):
        """publish_table nunca deve propagar excecao."""
        with patch("config.DATABRICKS_AUTO_UPLOAD", True), \
             patch("src.connectors.databricks_uploader.upload_silver_table",
                   side_effect=Exception("qualquer erro")):
            try:
                result = publish_table(self.pq, "tb_test")
                self.assertIn(result["status"], ("OK","ERROR","DISABLED"))
            except Exception as e:
                self.fail(f"publish_table propagou excecao: {e}")

    def test_table_name_in_result(self):
        with patch("config.DATABRICKS_AUTO_UPLOAD", False):
            result = publish_table(self.pq, "tb_clientes")
        self.assertEqual(result["table"], "tb_clientes")


# ═════════════════════════════════════════════════════════════════════════════
# TestUploadSilverTable
# ═════════════════════════════════════════════════════════════════════════════
class TestUploadSilverTable(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.pq  = _pq(self.tmp)

    def test_none_when_disabled(self):
        with patch("config.DATABRICKS_AUTO_UPLOAD", False):
            self.assertIsNone(upload_silver_table(self.pq))

    def test_none_when_host_missing(self):
        with patch("config.DATABRICKS_AUTO_UPLOAD", True), \
             patch("config.DATABRICKS_HOST", ""),           \
             patch("config.DATABRICKS_WAREHOUSE_ID", WID):
            self.assertIsNone(upload_silver_table(self.pq))

    def test_none_when_warehouse_missing(self):
        with patch("config.DATABRICKS_AUTO_UPLOAD", True), \
             patch("config.DATABRICKS_HOST", HOST),         \
             patch("config.DATABRICKS_WAREHOUSE_ID", ""):
            self.assertIsNone(upload_silver_table(self.pq))


# ═════════════════════════════════════════════════════════════════════════════
# TestDatRefFromRunId
# ═════════════════════════════════════════════════════════════════════════════
class TestDatRefFromRunId(unittest.TestCase):
    def test_extracts_date_from_run_id(self):
        self.assertEqual(dat_ref_from_run_id("run_20240115_143022_abc123"), "2024-01-15")

    def test_returns_none_for_invalid_format(self):
        self.assertIsNone(dat_ref_from_run_id("invalid"))

    def test_returns_none_for_none_input(self):
        self.assertIsNone(dat_ref_from_run_id(None))

    def test_returns_none_for_empty_string(self):
        self.assertIsNone(dat_ref_from_run_id(""))

    def test_various_dates(self):
        self.assertEqual(dat_ref_from_run_id("run_20231231_000000_xyz"), "2023-12-31")
        self.assertEqual(dat_ref_from_run_id("run_20240601_120000_abc"), "2024-06-01")


# ═════════════════════════════════════════════════════════════════════════════
# TestTagHelpers
# ═════════════════════════════════════════════════════════════════════════════
class TestTagHelpers(unittest.TestCase):
    def test_tag_key_replaces_special_chars(self):
        k = DatabricksUploader._tag_key("LGPD.SCR-BACEN 4658")
        self.assertFalse(any(c in k for c in ".,- =:/"))

    def test_tag_key_max_256(self):
        self.assertLessEqual(len(DatabricksUploader._tag_key("x" * 300)), 256)

    def test_tag_value_escapes_single_quotes(self):
        v = DatabricksUploader._esc("it's a test")
        # Verifica que a aspa simples foi escapada (\\' presente no resultado)
        self.assertIn("\\'", v)

    def test_tag_value_max_256(self):
        self.assertLessEqual(len(DatabricksUploader._tag_value("x" * 300)), 256)


if __name__ == "__main__":
    unittest.main()
