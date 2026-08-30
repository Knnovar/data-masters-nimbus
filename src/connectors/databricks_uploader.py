"""src/connectors/databricks_uploader.py — Nimbus -> Databricks via REST API (Delta Lake)."""
from __future__ import annotations
import base64, json
from pathlib import Path
from typing import Optional
import requests

class DiagnoseResult:
    def __init__(self): self.levels = {}
    def add(self, level, ok, message): self.levels[level] = {"ok": ok, "message": message}
    @property
    def all_ok(self): return all(v["ok"] for v in self.levels.values())
    def print_report(self):
        print("\n[DATABRICKS] Diagnostico de conectividade\n" + "-"*50)
        for level, r in self.levels.items():
            print("  [{:5}] {}: {}".format("OK" if r["ok"] else "FALHA", level, r["message"]))
        print("-"*50)
        print("  Tudo pronto para upload.\n" if self.all_ok else "  Corrija os itens FALHA antes de fazer upload.\n")

class DatabricksUploader:
    _BLOCK_SIZE = 1_000_000

    def __init__(self, host, token, warehouse_id, dbfs_base="/nimbus/silver",
                 catalog="hive_metastore", schema="nimbus"):
        if not host: raise ValueError("DATABRICKS_HOST nao configurado em config.py / .env")
        if not token: raise ValueError("DATABRICKS_TOKEN nao configurado em config.py / .env")
        if not warehouse_id:
            raise ValueError("DATABRICKS_WAREHOUSE_ID nao configurado. SQL Editor > nome do warehouse > copy ID")
        self._host = host.rstrip("/"); self._token = token
        self._warehouse_id = warehouse_id; self._dbfs_base = dbfs_base.rstrip("/")
        self._catalog = catalog; self._schema = schema
        self._session = requests.Session()
        self._session.headers.update({"Authorization": f"Bearer {token}", "Content-Type": "application/json"})

    def _url(self, ep): return f"{self._host}/api/2.0/{ep.lstrip('/')}"
    def _get(self, ep, **kw): return self._session.get(self._url(ep), timeout=15, **kw)
    def _post(self, ep, payload):
        resp = self._session.post(self._url(ep), json=payload, timeout=30)
        if not resp.ok: raise RuntimeError(f"API erro {resp.status_code} em {ep}: {resp.text[:300]}")
        return resp.json() if resp.text else {}

    def _sql(self, stmt, wait=True):
        payload = {"statement": stmt, "warehouse_id": self._warehouse_id,
                   "wait_timeout": "60s" if wait else "0s",
                   "catalog": self._catalog, "schema": self._schema}
        resp = self._session.post(self._url("sql/statements"), json=payload, timeout=90)
        if not resp.ok: raise RuntimeError(f"SQL erro {resp.status_code}: {resp.text[:300]}\nStmt: {stmt[:200]}")
        result = resp.json()
        state  = result.get("status", {}).get("state", "UNKNOWN")
        if state == "FAILED":
            raise RuntimeError("SQL falhou: {}".format(result.get("status",{}).get("error",{}).get("message","sem detalhe")))
        return result

    def diagnose(self):
        r = DiagnoseResult()
        try:
            resp = self._get("clusters/list")
            if resp.status_code == 200: r.add("1. Token e workspace", True, f"Autenticado em {self._host}")
            elif resp.status_code == 401:
                r.add("1. Token e workspace", False, "Token invalido. Gere um novo em User Settings > Access Tokens.")
                return r
            else:
                r.add("1. Token e workspace", False, f"HTTP {resp.status_code}")
                return r
        except requests.exceptions.ConnectionError:
            r.add("1. Token e workspace", False, f"Nao foi possivel conectar a {self._host}")
            return r
        try:
            resp = self._get(f"sql/warehouses/{self._warehouse_id}")
            if resp.status_code == 200:
                d = resp.json(); state = d.get("state","?"); name = d.get("name", self._warehouse_id)
                if state in ("RUNNING","STARTING"): r.add("2. SQL Warehouse", True, f"'{name}' esta {state}")
                else: r.add("2. SQL Warehouse", False, f"'{name}' esta {state}. Inicie o warehouse.")
            elif resp.status_code == 404:
                r.add("2. SQL Warehouse", False, f"Warehouse '{self._warehouse_id}' nao encontrado.")
            else: r.add("2. SQL Warehouse", False, f"HTTP {resp.status_code}")
        except Exception as e: r.add("2. SQL Warehouse", False, str(e))
        try:
            check = self._sql(f"SHOW SCHEMAS IN {self._catalog} LIKE '{self._schema}'")
            rows  = check.get("result", {}).get("data_array", [])
            if rows: r.add("3. Schema no metastore", True, f"{self._catalog}.{self._schema} existe")
            else:
                self._sql(f"CREATE SCHEMA IF NOT EXISTS {self._catalog}.{self._schema}")
                r.add("3. Schema no metastore", True, f"{self._catalog}.{self._schema} criado")
        except Exception as e: r.add("3. Schema no metastore", False, str(e))
        try:
            probe = f"{self._dbfs_base}/_probe"
            h = self._post("dbfs/create", {"path": probe, "overwrite": True})["handle"]
            self._post("dbfs/close", {"handle": h})
            self._post("dbfs/delete", {"path": probe, "recursive": False})
            r.add("4. Escrita no DBFS", True, f"Permissao confirmada em {self._dbfs_base}")
        except Exception as e: r.add("4. Escrita no DBFS", False, str(e))
        r.print_report()
        return r

    def upload_parquet_to_folder(self, local_path, table_name=None):
        if not Path(local_path).exists(): raise FileNotFoundError(f"Nao encontrado: {local_path}")
        tbl = table_name or Path(local_path).stem
        folder = f"{self._dbfs_base}/{tbl}"
        dbfs_file = f"{folder}/{Path(local_path).name}"
        print(f"[DATABRICKS] Upload: {Path(local_path).name} -> dbfs:{dbfs_file}")
        h = self._post("dbfs/create", {"path": dbfs_file, "overwrite": True})["handle"]
        data = Path(local_path).read_bytes(); total = len(data); sent = 0
        while sent < total:
            chunk = data[sent: sent + self._BLOCK_SIZE]
            self._post("dbfs/add-block", {"handle": h, "data": base64.b64encode(chunk).decode()})
            sent += len(chunk)
            print(f"[DATABRICKS]   {sent/total*100:.0f}% ({sent}/{total})", end="\r")
        self._post("dbfs/close", {"handle": h})
        print(f"\n[DATABRICKS] Upload OK: dbfs:{dbfs_file} ({total/1024:.1f} KB)")
        return folder

    def convert_to_delta(self, dbfs_folder):
        print(f"[DATABRICKS] CONVERT TO DELTA: dbfs:{dbfs_folder}")
        try:
            self._sql(f"CONVERT TO DELTA parquet.`dbfs:{dbfs_folder}`")
            print(f"[DATABRICKS] Delta OK")
            return True
        except RuntimeError as e:
            if "already" in str(e).lower() or "delta" in str(e).lower():
                print("[DATABRICKS] Ja e Delta — sem conversao necessaria")
                return True
            raise

    def register_or_refresh(self, table_name, dbfs_folder):
        full = f"{self._catalog}.{self._schema}.{table_name}"
        try:
            check  = self._sql(f"SHOW TABLES IN {self._schema} LIKE '{table_name}'")
            exists = bool(check.get("result", {}).get("data_array", []))
        except Exception: exists = False
        if exists:
            self._sql(f"REFRESH TABLE {full}")
            print(f"[DATABRICKS] REFRESH OK — {full}")
        else:
            self._sql(f"CREATE TABLE IF NOT EXISTS {full} USING DELTA LOCATION 'dbfs:{dbfs_folder}'")
            print(f"[DATABRICKS] Tabela registrada: {full}")
            print(f"[DATABRICKS] SQL Editor: SELECT * FROM {full} LIMIT 100;")
        return full

    def populate_column_comments(self, table_name, local_parquet_path, contract=None):
        try:
            import pyarrow.parquet as pq
            schema = pq.read_schema(str(local_parquet_path))
        except Exception as e:
            print(f"[DATABRICKS] Nao foi possivel ler metadata: {e}")
            return 0
        col_info = {}
        if contract:
            for col in contract.schema:
                desc  = col.description or ""
                flags = col.regulatory_flags or []
                if desc.startswith("# TODO"): desc = ""
                col_info[col.name] = {"description": desc, "flags": flags}
        full  = f"{self._catalog}.{self._schema}.{table_name}"
        count = 0
        for field in schema:
            info    = col_info.get(field.name, {})
            parts   = []
            if info.get("description"): parts.append(info["description"])
            if info.get("flags"):       parts.append("Regulatory: {}".format(", ".join(info["flags"])))
            comment = " | ".join(parts) if parts else f"Tipo: {field.type}"
            try:
                self._sql(f"ALTER TABLE {full} ALTER COLUMN `{field.name}` COMMENT '{comment.replace(chr(39), chr(92)+chr(39))}'")
                count += 1
            except Exception as e:
                print(f"[DATABRICKS]   [WARN] Comentario de '{field.name}' falhou: {e}")
        print(f"[DATABRICKS] {count}/{len(list(schema))} colunas comentadas em {full}")
        return count

    def upload_and_register(self, local_path, table_name=None, contract=None, skip_comments=False):
        tbl    = table_name or Path(local_path).stem
        folder = self.upload_parquet_to_folder(local_path, table_name=tbl)
        self.convert_to_delta(folder)
        full = self.register_or_refresh(tbl, folder)
        if not skip_comments:
            self.populate_column_comments(tbl, local_path, contract=contract)
        return full

    def test_connection(self):
        try:
            resp = self._get("clusters/list")
            if resp.status_code == 200: print(f"[DATABRICKS] Conexao OK: {self._host}"); return True
            print(f"[DATABRICKS] Erro {resp.status_code}"); return False
        except requests.exceptions.ConnectionError:
            print(f"[DATABRICKS] Nao foi possivel conectar: {self._host}"); return False

def get_uploader():
    import config as cfg
    return DatabricksUploader(
        host         = getattr(cfg, "DATABRICKS_HOST",         ""),
        token        = getattr(cfg, "DATABRICKS_TOKEN",        ""),
        warehouse_id = getattr(cfg, "DATABRICKS_WAREHOUSE_ID", ""),
        dbfs_base    = getattr(cfg, "DATABRICKS_DBFS_BASE",    "/nimbus/silver"),
        catalog      = getattr(cfg, "DATABRICKS_CATALOG",      "hive_metastore"),
        schema       = getattr(cfg, "DATABRICKS_SCHEMA",       "nimbus"),
    )

def upload_silver_table(silver_path, table_name=None, contract=None):
    import config as cfg
    if not getattr(cfg, "DATABRICKS_AUTO_UPLOAD", False): return None
    host = getattr(cfg, "DATABRICKS_HOST", "")
    token = getattr(cfg, "DATABRICKS_TOKEN", "")
    wid   = getattr(cfg, "DATABRICKS_WAREHOUSE_ID", "")
    missing = [k for k,v in [("DATABRICKS_HOST",host),("DATABRICKS_TOKEN",token),("DATABRICKS_WAREHOUSE_ID",wid)] if not v]
    if missing:
        print("[DATABRICKS] Upload ignorado: {} nao configurados em config.py".format(", ".join(missing)))
        return None
    try:
        u = DatabricksUploader(host=host, token=token, warehouse_id=wid,
            dbfs_base=getattr(cfg,"DATABRICKS_DBFS_BASE","/nimbus/silver"),
            catalog=getattr(cfg,"DATABRICKS_CATALOG","hive_metastore"),
            schema=getattr(cfg,"DATABRICKS_SCHEMA","nimbus"))
        return u.upload_and_register(silver_path, table_name=table_name, contract=contract)
    except Exception as e:
        print(f"[DATABRICKS] Upload falhou (nao bloqueante): {e}")
        return None
