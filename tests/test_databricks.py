"""tests/test_databricks.py — Testes para DatabricksUploader (sem chamadas reais)."""
import base64, json, sys, tempfile, unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.connectors.databricks_uploader import DatabricksUploader, DiagnoseResult, upload_silver_table

HOST=  "https://community.cloud.databricks.com"
TOKEN= "dapi_test_token"
WID=   "abc123warehouse"
SAMPLE= pd.DataFrame({"id":["C1","C2"],"vl":[1.0,2.0]})

def _u(**kw):
    d = dict(host=HOST,token=TOKEN,warehouse_id=WID,dbfs_base="/nimbus/silver",catalog="hive_metastore",schema="nimbus")
    d.update(kw); return DatabricksUploader(**d)

def _pq(tmp):
    p = tmp/"tb_test.parquet"; SAMPLE.to_parquet(p,index=False); return p

def _ok(data=None):
    m=MagicMock(); m.ok=True; m.status_code=200
    m.text=json.dumps(data or {"handle":1}); m.json.return_value=data or {"handle":1}; return m

class TestInit(unittest.TestCase):
    def test_empty_host_raises(self):
        with self.assertRaises(ValueError) as ctx: DatabricksUploader(host="",token=TOKEN,warehouse_id=WID)
        self.assertIn("DATABRICKS_HOST", str(ctx.exception))
    def test_empty_token_raises(self):
        with self.assertRaises(ValueError): DatabricksUploader(host=HOST,token="",warehouse_id=WID)
    def test_empty_warehouse_raises(self):
        with self.assertRaises(ValueError) as ctx: DatabricksUploader(host=HOST,token=TOKEN,warehouse_id="")
        self.assertIn("DATABRICKS_WAREHOUSE_ID", str(ctx.exception))
    def test_valid_creates_instance(self): self.assertIsInstance(_u(), DatabricksUploader)
    def test_auth_header(self): self.assertIn(f"Bearer {TOKEN}", _u()._session.headers.get("Authorization",""))
    def test_trailing_slash(self): self.assertEqual(_u(host="https://h.com/")._url("x"), "https://h.com/api/2.0/x")

class TestDiagnoseResult(unittest.TestCase):
    def test_all_ok_true(self): r=DiagnoseResult(); r.add("1",True,"OK"); self.assertTrue(r.all_ok)
    def test_all_ok_false(self): r=DiagnoseResult(); r.add("1",True,"OK"); r.add("2",False,"FAIL"); self.assertFalse(r.all_ok)
    def test_levels_stored(self): r=DiagnoseResult(); r.add("t",True,"msg"); self.assertIn("t",r.levels)

class TestDiagnose(unittest.TestCase):
    def setUp(self): self.u = _u()
    def test_invalid_token_stops_level1(self):
        with patch.object(self.u._session,"get") as m:
            m.return_value.status_code=401; m.return_value.text="Unauthorized"
            r = self.u.diagnose()
        self.assertFalse(r.levels["1. Token e workspace"]["ok"])
        self.assertNotIn("2. SQL Warehouse", r.levels)
    def test_connection_error_stops_level1(self):
        import requests
        with patch.object(self.u._session,"get",side_effect=requests.exceptions.ConnectionError):
            r = self.u.diagnose()
        self.assertFalse(r.levels["1. Token e workspace"]["ok"])

class TestUploadParquetToFolder(unittest.TestCase):
    def setUp(self): self.tmp=Path(tempfile.mkdtemp()); self.u=_u(); self.pq=_pq(self.tmp)
    def test_file_not_found(self):
        with self.assertRaises(FileNotFoundError): self.u.upload_parquet_to_folder(Path("/nao/existe.parquet"))
    def test_returns_folder_path(self):
        with patch.object(self.u._session,"post",return_value=_ok({"handle":1})):
            f = self.u.upload_parquet_to_folder(self.pq,"tb_test")
        self.assertEqual(f,"/nimbus/silver/tb_test")
    def test_uses_stem_when_no_table_name(self):
        with patch.object(self.u._session,"post",return_value=_ok({"handle":1})):
            f = self.u.upload_parquet_to_folder(self.pq)
        self.assertIn("tb_test", f)
    def test_calls_create_addblock_close(self):
        urls=[]
        def cap(url,**kw): urls.append(url); return _ok({"handle":1})
        with patch.object(self.u._session,"post",side_effect=cap):
            self.u.upload_parquet_to_folder(self.pq,"tb_test")
        self.assertTrue(any("create" in u for u in urls))
        self.assertTrue(any("add-block" in u for u in urls))
        self.assertTrue(any("close" in u for u in urls))
    def test_sends_valid_base64(self):
        chunks=[]
        def cap(url,json=None,**kw):
            if json and "data" in json: chunks.append(json["data"])
            return _ok({"handle":1})
        with patch.object(self.u._session,"post",side_effect=cap):
            self.u.upload_parquet_to_folder(self.pq,"tb_test")
        self.assertGreater(len(chunks),0)
        for c in chunks: base64.b64decode(c)
    def test_api_error_raises(self):
        m=MagicMock(); m.ok=False; m.status_code=403; m.text="Forbidden"
        with patch.object(self.u._session,"post",return_value=m):
            with self.assertRaises(RuntimeError): self.u.upload_parquet_to_folder(self.pq,"tb_test")

class TestConvertToDelta(unittest.TestCase):
    def setUp(self): self.u=_u()
    def _sql_ok(self): return {"status":{"state":"SUCCEEDED"}}
    def test_sends_convert_sql(self):
        stmts=[]
        def cap(s,**kw): stmts.append(s); return self._sql_ok()
        with patch.object(self.u,"_sql",side_effect=cap): self.u.convert_to_delta("/nimbus/silver/tb_c")
        self.assertTrue(any("CONVERT TO DELTA" in s for s in stmts))
    def test_already_delta_returns_true(self):
        with patch.object(self.u,"_sql",side_effect=RuntimeError("already delta")):
            self.assertTrue(self.u.convert_to_delta("/nimbus/silver/tb_test"))
    def test_real_error_propagates(self):
        with patch.object(self.u,"_sql",side_effect=RuntimeError("network error")):
            with self.assertRaises(RuntimeError): self.u.convert_to_delta("/nimbus/silver/tb_test")

class TestRegisterOrRefresh(unittest.TestCase):
    def setUp(self): self.u=_u()
    def test_creates_when_not_exists(self):
        stmts=[]
        def cap(s,**kw): stmts.append(s); return {"status":{"state":"SUCCEEDED"},"result":{"data_array":[]}}
        with patch.object(self.u,"_sql",side_effect=cap):
            self.u.register_or_refresh("tb_test","/nimbus/silver/tb_test")
        self.assertTrue(any("CREATE TABLE" in s for s in stmts))
    def test_refreshes_when_exists(self):
        stmts=[]
        def cap(s,**kw):
            stmts.append(s)
            rows=[["tb_test"]] if "SHOW TABLES" in s else []
            return {"status":{"state":"SUCCEEDED"},"result":{"data_array":rows}}
        with patch.object(self.u,"_sql",side_effect=cap):
            self.u.register_or_refresh("tb_test","/nimbus/silver/tb_test")
        self.assertTrue(any("REFRESH" in s for s in stmts))
    def test_returns_full_table_name(self):
        def cap(s,**kw): return {"status":{"state":"SUCCEEDED"},"result":{"data_array":[]}}
        with patch.object(self.u,"_sql",side_effect=cap):
            r = self.u.register_or_refresh("tb_clientes","/nimbus/silver/tb_clientes")
        self.assertIn("nimbus",r); self.assertIn("tb_clientes",r)
    def test_uses_delta_location(self):
        stmts=[]
        def cap(s,**kw): stmts.append(s); return {"status":{"state":"SUCCEEDED"},"result":{"data_array":[]}}
        with patch.object(self.u,"_sql",side_effect=cap):
            self.u.register_or_refresh("tb_test","/nimbus/silver/tb_test")
        create = next(s for s in stmts if "CREATE TABLE" in s)
        self.assertIn("USING DELTA", create); self.assertIn("LOCATION", create)

class TestPopulateColumnComments(unittest.TestCase):
    def setUp(self): self.tmp=Path(tempfile.mkdtemp()); self.u=_u(); self.pq=_pq(self.tmp)
    def _contract(self, cols):
        schema=[SimpleNamespace(name=c["name"],description=c.get("desc",""),
                regulatory_flags=c.get("flags",[]),type="string",nullable=True,business_rules=[]) for c in cols]
        return SimpleNamespace(table="tb_test",version="1.0",manifest_status="VALIDATED",schema=schema)
    def test_sends_alter_column(self):
        stmts=[]
        def cap(s,**kw): stmts.append(s); return {"status":{"state":"SUCCEEDED"}}
        with patch.object(self.u,"_sql",side_effect=cap):
            count = self.u.populate_column_comments("tb_test",self.pq)
        self.assertGreater(count,0); self.assertTrue(any("ALTER TABLE" in s and "COMMENT" in s for s in stmts))
    def test_uses_description(self):
        stmts=[]
        def cap(s,**kw): stmts.append(s); return {"status":{"state":"SUCCEEDED"}}
        c=self._contract([{"name":"id","desc":"Identificador"},{"name":"vl","desc":"Valor"}])
        with patch.object(self.u,"_sql",side_effect=cap):
            self.u.populate_column_comments("tb_test",self.pq,contract=c)
        self.assertTrue(any("Identificador" in s for s in stmts))
    def test_skips_todo(self):
        stmts=[]
        def cap(s,**kw): stmts.append(s); return {"status":{"state":"SUCCEEDED"}}
        c=self._contract([{"name":"id","desc":"# TODO: descrever"}])
        with patch.object(self.u,"_sql",side_effect=cap):
            self.u.populate_column_comments("tb_test",self.pq,contract=c)
        self.assertFalse(any("# TODO" in s for s in stmts))
    def test_includes_regulatory_flags(self):
        stmts=[]
        def cap(s,**kw): stmts.append(s); return {"status":{"state":"SUCCEEDED"}}
        c=self._contract([{"name":"id","desc":"CPF","flags":["LGPD_SENSITIVE"]},{"name":"vl","desc":""}])
        with patch.object(self.u,"_sql",side_effect=cap):
            self.u.populate_column_comments("tb_test",self.pq,contract=c)
        self.assertTrue(any("LGPD_SENSITIVE" in s for s in stmts))
    def test_bad_parquet_returns_zero(self):
        with patch.object(self.u,"_sql"): count=self.u.populate_column_comments("tb_test",Path("/nao/existe.parquet"))
        self.assertEqual(count,0)

class TestUploadSilverTable(unittest.TestCase):
    def setUp(self): self.tmp=Path(tempfile.mkdtemp()); self.pq=_pq(self.tmp)
    def test_none_when_disabled(self):
        with patch("config.DATABRICKS_AUTO_UPLOAD",False): self.assertIsNone(upload_silver_table(self.pq))
    def test_none_when_host_missing(self):
        with patch("config.DATABRICKS_AUTO_UPLOAD",True),patch("config.DATABRICKS_HOST",""),\
             patch("config.DATABRICKS_TOKEN",TOKEN),patch("config.DATABRICKS_WAREHOUSE_ID",WID):
            self.assertIsNone(upload_silver_table(self.pq))
    def test_none_when_warehouse_missing(self):
        with patch("config.DATABRICKS_AUTO_UPLOAD",True),patch("config.DATABRICKS_HOST",HOST),\
             patch("config.DATABRICKS_TOKEN",TOKEN),patch("config.DATABRICKS_WAREHOUSE_ID",""):
            self.assertIsNone(upload_silver_table(self.pq))
    def test_exception_does_not_propagate(self):
        with patch("config.DATABRICKS_AUTO_UPLOAD",True),patch("config.DATABRICKS_HOST",HOST),\
             patch("config.DATABRICKS_TOKEN",TOKEN),patch("config.DATABRICKS_WAREHOUSE_ID",WID),\
             patch("src.connectors.databricks_uploader.DatabricksUploader.upload_and_register",
                   side_effect=RuntimeError("API error")):
            self.assertIsNone(upload_silver_table(self.pq))

class TestConnection(unittest.TestCase):
    def test_200_returns_true(self):
        u=_u()
        with patch.object(u._session,"get") as m: m.return_value.status_code=200; self.assertTrue(u.test_connection())
    def test_401_returns_false(self):
        u=_u()
        with patch.object(u._session,"get") as m: m.return_value.status_code=401; m.return_value.text="x"; self.assertFalse(u.test_connection())
    def test_connection_error_returns_false(self):
        import requests; u=_u()
        with patch.object(u._session,"get",side_effect=requests.exceptions.ConnectionError): self.assertFalse(u.test_connection())

if __name__ == "__main__":
    unittest.main()
