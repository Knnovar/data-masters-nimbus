"""src/connectors/databricks_uploader.py — Nimbus -> Databricks via REST API (Delta Lake)."""
from __future__ import annotations
import json
import re
from pathlib import Path
from datetime import datetime,timezone
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

class _OAuthAuth(requests.auth.AuthBase):
    """Autentica cada request pelo SDK, reaproveitamendo 'databricks auth login'"""
    def __init__(self,host):
            try:
                from databricks.sdk.core import Config
            except ImportError:
                raise ValueError("Sem DATABRICKS_TOKEN a autenticacao usa OAuth: pip install databricks-sdk e databricks auth login --host <host>")
            self._config = Config(host=host)
    def __call__(self, requests):
            requests.headers.update(self._config.authenticate())
            return requests

class DatabricksUploader:
    
    def __init__(self, host, token="", warehouse_id="", volume="",
                 catalog="workspace", schema="nimbus"):
        if not host: raise ValueError("DATABRICKS_HOST nao configurado em config.py / .env")
        if not host.startswith(("http://","https://")): raise ValueError("DATABRICKS_HOST deve comecar com http:// ou https://")
        if not warehouse_id:
            raise ValueError("DATABRICKS_WAREHOUSE_ID nao configurado. SQL Editor > nome do warehouse > copy ID")
        if not volume:
            raise ValueError("DATABRICKS_VOLUME nao configurado (ex: landing)")
        self._host = host.rstrip("/"); self._token = token
        self._warehouse_id = warehouse_id; self._volume = volume.rstrip("/")
        self._catalog = catalog; self._schema = schema
        self._session = requests.Session()
        if token: self._session.headers.update({"Authorization": f"Bearer {token}"})
        else: self._session.auth = _OAuthAuth(self._host)

    def _url(self, ep): return f"{self._host}/api/2.0/{ep.lstrip('/')}"
    def _get(self, ep, **kw): return self._session.get(self._url(ep), timeout=15, **kw)
    def _post(self, ep, payload):
        resp = self._session.post(self._url(ep), json=payload, timeout=30)
        if not resp.ok: raise RuntimeError(f"API erro {resp.status_code} em {ep}: {resp.text[:300]}")
        return resp.json() if resp.text else {}
    _IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

    def _volume_dir(self, table_name):
        """Raiz da tabela no Volume - e o que o CTAS le."""
        if not self._IDENT.match(table_name):
            raise ValueError(f"Nome de tabela invalido para SQL/Volume: {table_name!r}")
        return f"/Volumes/{self._catalog}/{self._schema}/{self._volume}/{table_name}"

    @staticmethod
    def _dat_ref(dat_ref=None):
        d = dat_ref or datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", d): raise ValueError(f"dat_ref deve ser YYYY-MM-DD: {d!r}")
        return d

    def _partition_dir(self, table_name, dat_ref=None):
        """Particao Hive da carga: <tabela>/dat_ref=YYYY-MM-DD."""
        return f"{self._volume_dir(table_name)}/dat_ref={self._dat_ref(dat_ref)}"
    
    PARTITION_COLUMN = "dat_ref"
    PARTITION_COMMENT = ("Data de referencia da carga (particao Hive do volume). "
                         "Derivada do run_id do pipeline Nimbus - nao vem do arquivo de origem.")
    _TAG_KEY_INVALID = re.compile(r"[.,\-=/:\s]+")

    @classmethod
    def _tag_key(cls, raw):
        """Chave de tag no formato aceito pelo UC: sem . , - = / : nem espacos, até 256 caracteres"""
        return cls._TAG_KEY_INVALID.sub("_", str(raw).strip())[:256]
    @staticmethod
    def _esc(value):
        """Valor literal para SQL, com aspas simples escapadas"""
        return str(value).replace("'", chr(92) + "'")
    @classmethod
    def _tag_value(cls,value):
        """Valor de tag: o UC aceita no maximo 256 caracteres."""
        return cls._esc(str(value).strip()[:256])

    def _sql(self, stmt, wait=True):
        payload = {"statement": stmt, "warehouse_id": self._warehouse_id,
                   "wait_timeout": "50s" if wait else "0s",
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
            resp = self._session.get(f"sql/warehouse/{self._warehouse_id}")
            if resp.status_code == 200: r.add("1. Token e workspace", True, f"Autenticado em {self._host}")
            elif resp.status_code == 401:
                r.add("1. Token e workspace", False, "Credencial invalida. Gere um PAT em Settings > Developer, ou deixe DATABRICKS_TOKKEN vazio para usar OAuth.")
                return r
            else:
                r.add("1. Token e workspace", False, f"HTTP {resp.status_code}")
                return r
        except requests.exceptions.ConnectionError:
            r.add("1. Token e workspace", False, f"Nao foi possivel conectar a {self._host}")
            return r
        try:
            if resp.status_code == 200:
                d = resp.json(); state = d.get("state"); name = d.get("name", self._warehouse_id)
                if state is None: r.add("2. SQL Warehouse", True, f"'{name}' esta acessivel (sem campo state na resposta)")
                elif state in ("RUNNING","RESUMING"): r.add("2. SQL Warehouse", True, f"'{name}' esta {state}.")
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
        vol = f"{self._catalog}.{self._schema}.{self._volume}"
        try:
            probe = f"/Volumes/{self._catalog}/{self._schema}/{self._volume}/_probe"
            resp = self._session.put(f"{self._host}/api/2.0/fs/files{probe}", params={"overwrite": "true"}, data=b"nimbus", headers={"Content-Type": "application/octet-stream"}, timeout=30)
            if not resp.ok: raise RuntimeError(f"Files API {resp.status_code}: {resp.text[:200]}")
            self._session.delete(f"{self._host}/api/2.0/fs/files{probe}", timeout=30)
            r.add("4. Escrita no Volume", True, f"Permissao confirmada em {vol}")
        except Exception as e: r.add("4. Escrita no Volume", False, f"{e} | crie com: CREATE VOLUME IF NOT EXISTS {vol}")
        r.print_report()
        return r

    def upload_parquet_to_folder(self, local_path, table_name=None, dat_ref=None, run_id=None):
        """Envia o Parquet para <tabela>/dat_ref=<data>/part-<data>.parquet e devolve a raiz da tabela.
        
        Um arquivo por dat_ref: reprocessar a mesma data sobrescreve a carga (idempotente),
        datas diferentes convivem como particoes.
        """
        if not Path(local_path).exists(): raise FileNotFoundError(f"Nao encontrado: {local_path}")
        tbl = table_name or Path(local_path).stem
        folder = self._volume_dir(tbl)
        d = self._dat_ref(dat_ref)
        target = f"{folder}/dat_ref={d}/part-{d}.parquet"
        data = Path(local_path).read_bytes()
        print(f"[DATABRICKS] Upload: {Path(local_path).name} -> {target}" + (f" (run_id={run_id})" if run_id else ""))
        resp = self._session.put(f"{self._host}/api/2.0/fs/files{target}", params={"overwrite": "true"}, data=data, headers={"Content-Type": "application/octet-stream"}, timeout=50)
        if not resp.ok: raise RuntimeError(f"Files API erro {resp.status_code}: {resp.text[:300]}")
        print(f"[DATABRICKS] Upload OK: {target} ({len(data)/1024:.1f} KB)")
        return folder

    def register_or_refresh(self, table_name, volume_folder):
        """Managed table (Delta) via CTAS lendo o Parquet do Volume."""
        full = f"{self._catalog}.{self._schema}.{table_name}"
        self._sql(f"CREATE SCHEMA IF NOT EXISTS {self._catalog}.{self._schema}")
        self._sql(f"CREATE OR REPLACE TABLE {full} AS "
                  f"SELECT * FROM read_files('{volume_folder}', format => 'parquet', "
                  f"schemaEvolutionMode => 'none', mergeSchema => true)")
        print(f"[DATABRICKS] Tabela registrada: {full} <- {volume_folder}")
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
        try:
            self._sql(f"ALTER TABLE {full} ALTER COLUMN `{self.PARTITION_COLUMN}`"
                        f"COMMENT '{self._esc(self.PARTITION_COMMENT)}'")
            count += 1
        except Exception as e:
                print(f"[DATABRICKS][WARN] Comentario de '{self.PARTITION_COLUMN}' Falhou: {e}")
        print(f"[DATABRICKS] {count}/{len(list(schema)) + 1} colunas comentadas em {full}")
        return count

    def _table_tags(self, contract):
        """Tags de tabela derivadas do Manifest"""
        tags = {}
        reg = getattr(contract, "regulatory", None)
        if reg:
            for t in reg.tags or []:
                if str(t).startswith("# TODO"): continue
                tags[self._tag_key(t)] = "true"
            if reg.data_classification:tags["data_classification"] = reg.data_classification
            if reg.retention_years: tags["retention_years"] = str(reg.retention_years)
        if getattr(contract, "owner", None): tags["owner"] = contract.owner
        if getattr(contract, "manifest_status", None): tags["manifest_status"] = contract.manifest_status
        if getattr(contract, 'version', None): tags["contract_version"] = contract.version
        steward = getattr(contract, "steward", None)
        if steward and steward.email: tags["steward"] = steward.email
        source = getattr(contract, "source", None)
        if source and source.system: tags["source_system"] = source.system
        return tags

    def apply_table_metadata(self, table_name, contract=None):
        """COMMENT ON TABLE + SET TAGS de tabela e colunas, a partir do Manifest.
        
        Reaplicado a cada carga porque o CREATE OR REPLACE TABLE do CTAS descarta
        comentarios e tags da versao anterior.
        """
        if contract is None: return 0
        full = f"{self._catalog}.{self._schema}.{table_name}"
        applied = 0
        doc = [p for p in (getattr(contract, "description", None),
                         getattr(contract, "business_context", None)) if p]
        if doc:
            try:
                self._sql(f"COMMENT ON TABLE {full} IS '{self._esc(' | '.join(doc))}'")
                applied += 1
            except Exception as e:
                print(f"[DATABRICKS][WARN] COMMENT ON TABLE falhou: {e}")
        tags = self._table_tags(contract)
        if tags:
            pairs = ", ".join(f"'{self._tag_key(k)}' = '{self._tag_value(v)}'" for k, v in tags.items())
            try:
                self._sql(f"ALTER TABLE {full} SET TAGS ({pairs})")
                applied += len(tags)
            except Exception as e:
                print(f"[DATABRICKS][WARN] SET TAGS na tabela falhou: {e}")

        for col in getattr(contract, "schema", []) or []:
            flags = [f for f in (col.regulatory_flags or []) if not str(f).startswith("# TODO")]
            if not flags: continue
            pairs = ", ".join(f"'{self._tag_key(f)}' = 'true'" for f in flags)
            try:
                self._sql(f"ALTER TABLE {full} ALTER COLUMN `{col.name}` SET TAGS ({pairs})")
                applied += len(flags)
            except Exception as e:
                print(f"[DATABRICKS][WARN] SET TAGS em `{col.name}` falhou: {e}")
        print(f"[DATABRICKS] Metadados do contrato aplicados em {full}: {applied} itens")
        return applied



    def upload_and_register(self, local_path, table_name=None, contract=None, skip_comments=False, dat_ref=None, run_id=None):
        tbl    = table_name or Path(local_path).stem
        folder = self.upload_parquet_to_folder(local_path, table_name=tbl, dat_ref=dat_ref, run_id=run_id)
        full = self.register_or_refresh(tbl, folder)
        if not skip_comments:
            self.populate_column_comments(tbl, local_path, contract=contract)
            self.apply_table_metadata(tbl, contract=contract)
        return full

    def test_connection(self):
        try:
            resp = self._session.get(f"{self._host}/api/2.1/unity-catalog/catalogs", timeout=15)
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
        volume      = getattr(cfg, "DATABRICKS_VOLUME",      "landing"),
        catalog      = getattr(cfg, "DATABRICKS_CATALOG",      "workspace"),
        schema       = getattr(cfg, "DATABRICKS_SCHEMA",       "nimbus"),
    )

def publish_table(silver_path, table_name, contract=None, run_id=None, dat_ref=None):
    """Publica uma tabela no Databricks e devolve o status - nunca levanta.
    
    status: OK (tabela registrada), DISABLED (DATABRICKS_AUTO__UPLOAD=False),
    ERROR (falha real, que o chamador deve refletir no exit code).
    """
    import config as cfg
    if not getattr(cfg, "DATABRICKS_AUTO_UPLOAD", False):
        return {"table": table_name, "status": "DISABLED", "target": None, "error": None}
    try:
        full = upload_silver_table(silver_path, table_name=table_name, contract=contract, dat_ref=dat_ref, run_id=run_id)

        if full is None:
            return {"table": table_name, "status": "ERROR", "target": None, "error": "configuracao incompleta (host/warehouse)"}
        return{"table": table_name, "status": "OK", "target": full, "error": None}
    except Exception as e:
        print("[DATABRICKS] Publicacao FALHOU em {}: {}".format(table_name, e))
        return {"table": table_name, "status": "ERROR", "target": None, "error": str(e)}

def dat_ref_from_run_id(run_id):
    """run_YYYYMMDD_HHMMSS_xxxxx - > 'YYYY-MM-DD'. None quando nao reconhece o formato."""

    m = re.match(r"^run_(\d{4})(\d{2})(\d{2})_", run_id or "")
    return "-".join(m.groups()) if m else None

def upload_silver_table(silver_path, table_name=None, contract=None, dat_ref=None, run_id=None):
    import config as cfg
    if not getattr(cfg, "DATABRICKS_AUTO_UPLOAD", False): return None
    if dat_ref is None and run_id: dat_ref = dat_ref_from_run_id(run_id)
    host = getattr(cfg, "DATABRICKS_HOST", "")
    token = getattr(cfg, "DATABRICKS_TOKEN", "")
    wid   = getattr(cfg, "DATABRICKS_WAREHOUSE_ID", "")
    volume = getattr(cfg, "DATABRICKS_VOLUME", "")
    missing = [k for k,v in [("DATABRICKS_HOST",host),("DATABRICKS_WAREHOUSE_ID",wid)] if not v]
    if missing:
        print("[DATABRICKS] Upload ignorado: {} nao configurados em config.py".format(", ".join(missing)))
        return None
    u = DatabricksUploader(host=host, token=token, warehouse_id=wid,
            volume=volume or getattr(cfg,"DATABRICKS_VOLUME","landing"),
            catalog=getattr(cfg,"DATABRICKS_CATALOG","workspace"),
            schema=getattr(cfg,"DATABRICKS_SCHEMA","nimbus"))
    return u.upload_and_register(silver_path, table_name=table_name, contract=contract, dat_ref=dat_ref, run_id=run_id)
 
