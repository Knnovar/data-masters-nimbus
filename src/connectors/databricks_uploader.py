"""
src/connectors/databricks_uploader.py — Integração Nimbus -> Databricks via REST API.

Compatível com Databricks for Students (Community Edition).
Requer apenas host do workspace e token de acesso pessoal em config.py.
"""
from __future__ import annotations
import base64
from pathlib import Path
from typing import Optional
import requests


class DatabricksUploader:
    _BLOCK_SIZE = 1_000_000  # 1MB — limite da DBFS API por bloco

    def __init__(self, host, token, dbfs_base="/nimbus/silver",
                 catalog="hive_metastore", schema="nimbus"):
        if not host or not token:
            raise ValueError(
                "DATABRICKS_HOST e DATABRICKS_TOKEN precisam estar preenchidos em config.py.")
        self._host      = host.rstrip("/")
        self._token     = token
        self._dbfs_base = dbfs_base
        self._catalog   = catalog
        self._schema    = schema
        self._session   = requests.Session()
        self._session.headers.update({
            "Authorization": "Bearer {}".format(token),
            "Content-Type" : "application/json",
        })

    def _url(self, endpoint):
        return "{}/api/2.0/{}".format(self._host, endpoint.lstrip("/"))

    def _post(self, endpoint, payload):
        resp = self._session.post(self._url(endpoint), json=payload, timeout=30)
        if not resp.ok:
            raise RuntimeError("Databricks API erro {}: {}".format(
                resp.status_code, resp.text[:300]))
        return resp.json() if resp.text else {}

    def _sql(self, statement, warehouse_id=None):
        payload = {"statement": statement, "wait_timeout": "30s"}
        if warehouse_id:   payload["warehouse_id"] = warehouse_id
        if self._catalog:  payload["catalog"]       = self._catalog
        if self._schema:   payload["schema"]        = self._schema
        resp = self._session.post(self._url("sql/statements"), json=payload, timeout=60)
        if not resp.ok:
            raise RuntimeError("SQL erro {}: {}".format(resp.status_code, resp.text[:300]))
        return resp.json()

    def upload_parquet(self, local_path: Path, overwrite=True) -> str:
        if not local_path.exists():
            raise FileNotFoundError("Arquivo nao encontrado: {}".format(local_path))
        dbfs_path = "{}/{}".format(self._dbfs_base, local_path.name)
        print("[DATABRICKS] Upload: {} -> dbfs:{}".format(local_path.name, dbfs_path))
        handle = self._post("dbfs/create", {"path": dbfs_path, "overwrite": overwrite})["handle"]
        data   = local_path.read_bytes()
        total  = len(data)
        sent   = 0
        while sent < total:
            chunk = data[sent: sent + self._BLOCK_SIZE]
            self._post("dbfs/add-block", {
                "handle": handle,
                "data"  : base64.b64encode(chunk).decode("utf-8"),
            })
            sent += len(chunk)
            print("[DATABRICKS]   {:.0f}% ({}/{} bytes)".format(sent/total*100, sent, total))
        self._post("dbfs/close", {"handle": handle})
        print("[DATABRICKS] Upload concluido: dbfs:{} ({:.1f} KB)".format(
            dbfs_path, total/1024))
        return "dbfs:{}".format(dbfs_path)

    def register_table(self, table_name, dbfs_path, warehouse_id=None):
        self._sql("CREATE SCHEMA IF NOT EXISTS {}".format(self._schema),
                  warehouse_id=warehouse_id)
        result = self._sql(
            "CREATE OR REPLACE TABLE {schema}.{table} "
            "USING PARQUET LOCATION '{path}'".format(
                schema=self._schema, table=table_name, path=dbfs_path),
            warehouse_id=warehouse_id,
        )
        state = result.get("status", {}).get("state", "UNKNOWN")
        if state not in ("SUCCEEDED", "PENDING", "RUNNING"):
            raise RuntimeError("Registro falhou. Status: {}".format(state))
        print("[DATABRICKS] Tabela registrada: {}.{} -> {}".format(
            self._schema, table_name, dbfs_path))
        print("[DATABRICKS] SQL Editor: SELECT * FROM {}.{} LIMIT 100;".format(
            self._schema, table_name))

    def upload_and_register(self, local_path: Path, table_name=None,
                            warehouse_id=None, register=True) -> str:
        tbl       = table_name or local_path.stem
        dbfs_path = self.upload_parquet(local_path)
        if register:
            self.register_table(tbl, dbfs_path, warehouse_id=warehouse_id)
        return dbfs_path

    def test_connection(self) -> bool:
        try:
            resp = self._session.get(self._url("clusters/list"), timeout=10)
            if resp.status_code == 200:
                print("[DATABRICKS] Conexao OK: {}".format(self._host))
                return True
            print("[DATABRICKS] Erro {}: {}".format(resp.status_code, resp.text[:200]))
            return False
        except requests.exceptions.ConnectionError:
            print("[DATABRICKS] Nao foi possivel conectar a: {}".format(self._host))
            return False


def get_uploader() -> DatabricksUploader:
    import config as cfg
    return DatabricksUploader(
        host      = getattr(cfg, "DATABRICKS_HOST",      ""),
        token     = getattr(cfg, "DATABRICKS_TOKEN",     ""),
        dbfs_base = getattr(cfg, "DATABRICKS_DBFS_BASE", "/nimbus/silver"),
        catalog   = getattr(cfg, "DATABRICKS_CATALOG",   "hive_metastore"),
        schema    = getattr(cfg, "DATABRICKS_SCHEMA",    "nimbus"),
    )


def upload_silver_table(silver_path: Path, table_name=None,
                        warehouse_id=None) -> Optional[str]:
    import config as cfg
    if not getattr(cfg, "DATABRICKS_AUTO_UPLOAD", False):
        return None
    host  = getattr(cfg, "DATABRICKS_HOST",  "")
    token = getattr(cfg, "DATABRICKS_TOKEN", "")
    if not host or not token:
        print("[DATABRICKS] Upload ignorado: credenciais nao configuradas em config.py")
        return None
    try:
        u = DatabricksUploader(
            host=host, token=token,
            dbfs_base=getattr(cfg, "DATABRICKS_DBFS_BASE", "/nimbus/silver"),
            catalog  =getattr(cfg, "DATABRICKS_CATALOG",   "hive_metastore"),
            schema   =getattr(cfg, "DATABRICKS_SCHEMA",    "nimbus"),
        )
        return u.upload_and_register(silver_path, table_name=table_name,
                                     warehouse_id=warehouse_id)
    except Exception as e:
        print("[DATABRICKS] Upload falhou (nao bloqueante): {}".format(e))
        return None
