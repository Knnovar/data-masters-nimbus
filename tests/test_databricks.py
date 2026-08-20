"""tests/test_databricks.py — Testes para DatabricksUploader (sem chamadas reais)."""

import base64, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.connectors.databricks_uploader import DatabricksUploader, upload_silver_table

HOST  = "https://community.cloud.databricks.com"
TOKEN = "dapi_test_token"
SAMPLE = pd.DataFrame({"id": ["C1","C2"], "valor": [1.0, 2.0]})


def _uploader(**kw):
    d = dict(host=HOST, token=TOKEN, dbfs_base="/nimbus/silver",
             catalog="hive_metastore", schema="nimbus")
    d.update(kw)
    return DatabricksUploader(**d)


def _parquet(tmp):
    p = tmp / "tb_test.parquet"
    SAMPLE.to_parquet(p, index=False)
    return p


class TestInit(unittest.TestCase):
    def test_empty_host_raises(self):
        with self.assertRaises(ValueError): DatabricksUploader(host="", token=TOKEN)
    def test_empty_token_raises(self):
        with self.assertRaises(ValueError): DatabricksUploader(host=HOST, token="")
    def test_valid_creates_instance(self):
        self.assertIsInstance(_uploader(), DatabricksUploader)
    def test_authorization_header(self):
        u = _uploader()
        self.assertIn("Bearer {}".format(TOKEN),
                      u._session.headers.get("Authorization",""))


class TestUpload(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.u   = _uploader()
        self.pq  = _parquet(self.tmp)

    def _mock(self):
        m = MagicMock()
        m.ok = True
        m.text = '{"handle":1}'
        m.json.return_value = {"handle": 1}
        return m

    def test_file_not_found_raises(self):
        with self.assertRaises(FileNotFoundError):
            self.u.upload_parquet(Path("/nao/existe.parquet"))

    def test_returns_dbfs_path(self):
        with patch.object(self.u._session, "post", return_value=self._mock()):
            result = self.u.upload_parquet(self.pq)
        self.assertTrue(result.startswith("dbfs:"))
        self.assertIn("tb_test.parquet", result)

    def test_calls_create_addblock_close(self):
        urls = []
        def capture(url, **kw):
            urls.append(url)
            return self._mock()
        with patch.object(self.u._session, "post", side_effect=capture):
            self.u.upload_parquet(self.pq)
        self.assertTrue(any("create"    in u for u in urls))
        self.assertTrue(any("add-block" in u for u in urls))
        self.assertTrue(any("close"     in u for u in urls))

    def test_sends_base64(self):
        chunks = []
        def capture(url, json=None, **kw):
            if "add-block" in url and json:
                chunks.append(json.get("data",""))
            return self._mock()
        with patch.object(self.u._session, "post", side_effect=capture):
            self.u.upload_parquet(self.pq)
        self.assertGreater(len(chunks), 0)
        for c in chunks:
            base64.b64decode(c)  # nao levanta = e base64 valido

    def test_api_error_raises(self):
        m = MagicMock(); m.ok = False; m.status_code = 403; m.text = "Forbidden"
        with patch.object(self.u._session, "post", return_value=m):
            with self.assertRaises(RuntimeError): self.u.upload_parquet(self.pq)


class TestRegister(unittest.TestCase):
    def setUp(self):
        self.u = _uploader()

    def test_sends_create_schema_and_table(self):
        stmts = []
        def capture(url, json=None, **kw):
            if "sql/statements" in url and json:
                stmts.append(json.get("statement",""))
            m = MagicMock(); m.ok = True
            m.text = '{"status":{"state":"SUCCEEDED"}}'
            m.json.return_value = {"status":{"state":"SUCCEEDED"}}
            return m
        with patch.object(self.u._session, "post", side_effect=capture):
            self.u.register_table("tb_clientes", "dbfs:/nimbus/tb_clientes.parquet")
        self.assertTrue(any("CREATE SCHEMA" in s for s in stmts))
        self.assertTrue(any("CREATE OR REPLACE TABLE" in s and "tb_clientes" in s
                            for s in stmts))

    def test_includes_location(self):
        stmts = []
        def capture(url, json=None, **kw):
            if "sql/statements" in url and json:
                stmts.append(json.get("statement",""))
            m = MagicMock(); m.ok = True
            m.text = '{"status":{"state":"SUCCEEDED"}}'
            m.json.return_value = {"status":{"state":"SUCCEEDED"}}
            return m
        with patch.object(self.u._session, "post", side_effect=capture):
            self.u.register_table("tb_clientes", "dbfs:/nimbus/tb_clientes.parquet")
        self.assertTrue(any("LOCATION" in s and "tb_clientes.parquet" in s
                            for s in stmts))


class TestUploadSilverTable(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.pq  = _parquet(self.tmp)

    def test_returns_none_when_disabled(self):
        with patch("config.DATABRICKS_AUTO_UPLOAD", False):
            self.assertIsNone(upload_silver_table(self.pq))

    def test_returns_none_without_host(self):
        with patch("config.DATABRICKS_AUTO_UPLOAD", True), \
             patch("config.DATABRICKS_HOST", ""),          \
             patch("config.DATABRICKS_TOKEN", TOKEN):
            self.assertIsNone(upload_silver_table(self.pq))

    def test_exception_does_not_propagate(self):
        with patch("config.DATABRICKS_AUTO_UPLOAD", True), \
             patch("config.DATABRICKS_HOST", HOST),        \
             patch("config.DATABRICKS_TOKEN", TOKEN),      \
             patch("src.connectors.databricks_uploader.DatabricksUploader.upload_and_register",
                   side_effect=RuntimeError("API error")):
            self.assertIsNone(upload_silver_table(self.pq))


class TestConnection(unittest.TestCase):
    def test_returns_true_on_200(self):
        u = _uploader()
        with patch.object(u._session, "get") as m:
            m.return_value.status_code = 200
            self.assertTrue(u.test_connection())

    def test_returns_false_on_401(self):
        u = _uploader()
        with patch.object(u._session, "get") as m:
            m.return_value.status_code = 401
            m.return_value.text = "Unauthorized"
            self.assertFalse(u.test_connection())

    def test_returns_false_on_connection_error(self):
        u = _uploader()
        import requests
        with patch.object(u._session, "get",
                          side_effect=requests.exceptions.ConnectionError):
            self.assertFalse(u.test_connection())


if __name__ == "__main__":
    unittest.main()
