"""
src/connectors/databricks_uploader.py — Integração Nimbus -> Databricks via REST API.

Compatível com Databricks for Students (Free Edition).
Requer apenas host do workspace e token de acesso pessoal em config.py.
"""
from __future__ import annotations
from pathlib import Path
from typing import Optional
import requests


class DatabricksUploader:
    # _BLOCK_SIZE = 1_000_000  # 1MB — limite da DBFS API por bloco

    def __init__(self, host, token, 
                 catalog="workspace", schema="nimbus", volume="landing", warehouse_id=""):
        if not host or not token:
            raise ValueError(
                "DATABRICKS_HOST e DATABRICKS_TOKEN precisam estar preenchidos em config.py.")
        if not host.startswith("http"):
            raise ValueError("DATABRICKS_HOST precisa ser URL completa, ex: https://dbc-xxxx.cloud.databricks.com")
        self._host      = host.rstrip("/")
        self._token     = token
        self._catalog   = catalog
        self._schema    = schema
        self._volume    = volume
        self._warehouse_id = warehouse_id
        self._session   = requests.Session()
        self._session.headers.update({
            "Authorization": "Bearer {}".format(token),
        })

    def _url(self, endpoint):
        return "{}/api/2.0/{}".format(self._host, endpoint.lstrip("/"))

    def _post(self, endpoint, payload):
        htpps = self._session.post(self._url(endpoint), json=payload, timeout=30)
        if not resp.ok:
            raise RuntimeError("Databricks API erro {}: {}".format(
                resp.status_code, resp.text[:300]))
        return resp.json() if resp.text else {}

    def _sql(self, statement, warehouse_id=None):
        wid = warehouse_id or self._warehouse_id
        if not wid:
            raise ValueError("DATABRICKS_WAREHOUSE_ID obrigatorio para Free Edition")
        payload = {"statement": statement, "warehouse_id": wid, "wait_timeout": "30s"}
        if self._catalog:  payload["catalog"]       = self._catalog
        if self._schema:   payload["schema"]        = self._schema
        resp = self._session.post(self._url("sql/statements"), json=payload, timeout=60)
        if not resp.ok:
            raise RuntimeError("SQL erro {}: {}".format(resp.status_code, resp.text[:300]))
        result = resp.json()
        state = result.get("status", {}).get("state", "UNKNOWN")
        if state not in ("SUCCEEDED", "PENDING", "RUNNING"):
            error = result.get("status", {}).get("error", {}.get("message", ""))
            raise RuntimeError("SQL falhou. Status: {} {}".format(state, error))
        return result

    def _volume_path(self, filename: str) -> str:
        return "/Volumes/{}/{}/{}/{}".format(
            self._catalog, self._schema, self._volume, filename)

    def upload_parquet(self, local_path: Path, overwrite: bool=True) -> str:
        """ PUT único de bytes crus - sem base64, sem handle, sem blocos."""
        if not local_path.exists():
            raise FileNotFoundError("Arquivo local nao encontrado: {}".format(local_path))
        volume_path = self._volume_path(local_path.name)
        data = local_path.read_bytes()
        print("[DATABRICKS] Upload {} -> {}".format(local_path.name, volume_path))
        resp = self._session.put("{}api/2.0/fs/files{}".format(self._host, volume_path),
            params={"overwrite": "true" if overwrite else "false"},
            data=data,
            headers={"Content-Type": "application/octet-stream"},
            timeout=120,
        )
        if not resp.ok:
            raise RuntimeError("Files API erro {}: {}".format(resp.status_code, resp.text[:300]))
        print("[DATABRICKS] Upload concluido: {}({:.1f}) KB".format(volume_path, len(data)/1024))
        return volume_path

    def register_table(self, table_name, volume_path, warehouse_id=None):
        """ Cria managed table (Delta) lendo o Parquet do Volume."""
        self._sql("CREATE SCHEMA IF NOT EXISTS {}.{}".format(self._catalog, self._schema), warehouse_id=warehouse_id)
        self._sql(
            "CREATE OR REPLACE TABLE {cat}.{shc}.{tbl} AS "
            "SELECT * FROM read_files('{path}', format => 'parquet')".format(
                cat=self._catalog, shc=self._schema, tbl=table_name, path=volume_path), warehouse_id=warehouse_id)
        print("[DATABRICKS] Tabela registrada: {}.{}.{} <- {}".format(
            self._catalog, self._schema, table_name, volume_path))
        print("[DATABRICKS] SQL Editor: SELECT * FROM {}.{}.{} LIMIT 100;".format(
            self._catalog, self._schema, table_name))
 
    def upload_and_register(self, local_path: Path, table_name=None,
                            warehouse_id=None, register=True) -> str:
        tbl       = table_name or local_path.stem
        dbfs_path = self.upload_parquet(local_path)
        if register:
            self.register_table(tbl, self._volume_path(), warehouse_id=warehouse_id)
        return dbfs_path

    def test_connection(self) -> bool:
        """Valida Token + acesso ao Unity Catalog (Free Edition nao tem cluster para listar)."""
        try:
            resp = self._session.get(("{}/api/2.1/unity-catalog/catalogs").format(self._host), timeout=10)
            if resp.status_code == 200:
                names = [c.get("name") for c in resp.json().get("catalogs", [])]
                print("[DATABRICKS] Conexao OK: {} | Catalogos: {}".format(self._host, ", ".join(n for n in names if n) or "nenhum"))
                return True
            print("[DATABRICKS] Erro {}: {}".format(resp.status_code, resp.text[:200]))
            return False
        except requests.exceptions.ConnectionError:
            print("[DATABRICKS] Nao foi possivel conectar a: {}".format(self._host))
            return False


def get_uploader() -> DatabricksUploader:
    import config as cfg
    return DatabricksUploader(
        catalog   = getattr(cfg, "DATABRICKS_CATALOG",   "workspace"),
        schema    = getattr(cfg, "DATABRICKS_SCHEMA",    "nimbus"),
        volume    = getattr(cfg, "DATABRICKS_VOLUME",    "landing"),
        host      = getattr(cfg, "DATABRICKS_HOST",      ""),
        token     = getattr(cfg, "DATABRICKS_TOKEN",     ""),
        warehouse_id = getattr(cfg, "DATABRICKS_WAREHOUSE_ID", ""),
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
    u = get_uploader()
    return u.upload_and_register(silver_path, table_name=table_name, warehouse_id=warehouse_id)
    # try:
    #     u = DatabricksUploader(
    #         host=host, token=token,
    #         schema   =getattr(cfg, "DATABRICKS_SCHEMA",    "nimbus"),
    #         warehouse_id = getattr(cfg, "DATABRICKS_WAREHOUSE_ID", ""),
    #         volume    = getattr(cfg, "DATABRICKS_VOLUME",    "landing"),
    #     )
    #     return u.upload_and_register(silver_path, table_name=table_name,
    #                                  warehouse_id=warehouse_id)
    # except Exception as e:
    #     print("[DATABRICKS] Upload falhou (nao bloqueante): {}".format(e))
    #     return None
