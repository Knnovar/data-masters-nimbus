from __future__ import annotations
from pathlib import Path
import json, re
from src.connectors.databricks_uploader import DatabricksUploader, dat_ref_from_run_id, databricks_configured

_FORMAT_BY_EXT = {
    ".csv" : "csv",
    ".tsv" : "csv",
    ".json": "json",
    ".txt" : "text",
    ".dat" : "text",
    ".pos" : "text",
    ".fix" : "text",
}

_TABLE_SUFFIX_BY_FORMAT = {
    "csv": "",
    "json": "_json",
    "text": "_txt",
}
_PROVENANCE = {
    "_ingest_file"  : "Nome do arquivo de origem (_metadata.file_name). ",
    "_ingest_time"  : "Data/hora de modificacao do arquivo na origem (_metadata.file_modification_time). ",
    "_ingest_run_id": "run_id do pipeline Nimbus que trouxe o arquivo. ",
}

class BronzeUploader(DatabricksUploader):
    TABLE_SUFFIX = ""
    TABLE_COMMENT= ("Camada Bronze do Nimbus: copia fiel do arquivo recebido da origem, "
                    "sem cast, sem validacao de contrato e sem gate de qualidade. "
                    "Uma tabela por formato de origem. "
                    "Nao consumir para negocio - use a tabela Silver correspondente.")
    @classmethod
    def detect_format(cls, local_path):
        return _FORMAT_BY_EXT.get(Path(local_path).suffix.lower())

    def bronze_table(self, table_name, fmt=None):
        """Uma tabela Bronze por formato de origem.
        
        O CSV mantem o nome puro e os outros formatos recebem sufixo, Sem isso os 3 formatos da mesma tabela se sobrescrevem no CREATE OR REPLACE e sobra o
        ultimo registrado (o posicional, que em format => 'text' tem so a coluna 'value').
        """
        suffix = _TABLE_SUFFIX_BY_FORMAT.get(fmt or "csv", "_{}".format(fmt))
        return "{}{}{}".format(table_name, suffix, self.TABLE_SUFFIX)


    def upload_raw(self, local_path, table_name=None, dat_ref=None, run_id=None):
        src = Path(local_path)
        if not src.exists():
            raise FileNotFoundError("Nao encontrado: {}".format(local_path))

        tbl = table_name or src.stem
        folder = self._volume_dir(tbl)
        d      = self._dat_ref(dat_ref)
        target = "{}/dat_ref={}/{}".format(folder, d, src.name)
        data   = src.read_bytes()

        print("[BRONZE] Upload: {} -> {}".format(src.name, target)
              + (" (run_id={})".format(run_id) if run_id else ""))
        resp = self._session.put(
            "{}/api/2.0/fs/files{}".format(self._host, target),
            params={"overwrite": "true"}, data=data,
            headers={"Content-Type": "application/octet-stream"}, timeout=50,
        )
        if not resp.ok:
            raise RuntimeError("Files API erro {}: {}".format(resp.status_code, resp.text[:300]))
        print("[BRONZE] Upload OK: {} ({:.1f} KB)".format(target, len(data) / 1024))
        return target

    @staticmethod
    def json_root_key(local_path):
        try:
            payload = json.loads(Path(local_path).read_text(encoding="utf-8"))
        except (ValueError, OSError, UnicodeDecodeError):
            return None
        if not isinstance(payload, dict):
            return None
        for key, value in payload.items():
            if isinstance(value, list) and re.match(r"^\w+$", str(key)):
                return key
        return None

    def _read_files_expr(self, source, fmt):
        """read_files apontando para o arquivo exato da carga.
        
        Ler o arquivo, e nao a raiz da tabela, torna o CTAS independente do que ficou de cargas anteriores no Volume (esquemas diferentes
        do mesmo cenario na mesma pasta fazem o read_files falhar com erro interno). """

        opts = ["format => '{}'".format(fmt),  "schemaEvolutionMode => 'none'"]
        if fmt == "json":
            opts += ["multiLine => true"]
        else:
            opts += ["inferColumnTypes => false"]
        if fmt == "csv":
            opts += ["header => true"]
        return "read_files('{}', {})".format(source, ", ".join(opts))

    def register_raw(self, table_name, source_path, fmt, run_id=None, dat_ref=None,
                     json_root_key=None):
        full = "{}.{}.{}".format(self._catalog, self._schema, self.bronze_table(table_name))
        self._sql("CREATE SCHEMA IF NOT EXISTS {}.{}".format(self._catalog, self._schema))
        source = self._read_files_expr(source_path, fmt)
        part = self.PARTITION_COLUMN
        if fmt == 'json' and json_root_key:
            select = ("SELECT _rec.*, {part}, _ingest_file, _ingest_time, "
                      "'{run}' AS _ingest_run_id FROM ("
                      "SELECT explode(`{key}`) AS _rec, {part},"
                      "_metadata.file_name AS _ingest_file, "
                      "_metadata.file_modification_time AS _ingest_time "
                      "FROM {src})").format(part=part, run=self._esc(run_id or ""),
                                           key=json_root_key, src=source)
        else:
            select = ("SELECT *, _metadata.file_name AS _ingest_file, "
            "_metadata.file_modification_time AS _ingest_time,"
            " '{run}' AS _ingest_run_id "
            "FROM {src}").format(part=part, run=self._esc(run_id or ""), src=source)
        self._sql("CREATE OR REPLACE TABLE {} AS {}".format(full, select))
        print("[BRONZE] Tabela registrada: {} <- {}".format(full, source_path))
        return full

    @staticmethod
    def _is_missing_table(err):
        low = str(err).lower()
        return "table_or_view_not_found" in low or "cannot be found" in low
    
    def describe_bronze(self, table_name, fmt=None):
        full = "{}.{}.{}".format(self._catalog, self._schema, self.bronze_table(table_name, fmt))
        applied = 0
        try:
            self._sql("COMMENT ON TABLE {} IS '{}'".format(full, self._esc(self.TABLE_COMMENT)))
            applied += 1
        except Exception as e:
            if self._is_missing_table(e):
                raise RuntimeError(
                    "{} nao existe depois do CREATE OR REPLACE - o statement " \
                    "anterior nao foi aguardado ou falhou em silencio: {}".format(full, e)
                )
            print("[BRONZE][WARN] COMMENT ON TABLE falhou: {}".format(e))

        comments = dict(_PROVENANCE)
        comments[self.PARTITION_COLUMN] = self.PARTITION_COMMENT
        for col, text in comments.items():
            try:
                self._sql("ALTER TABLE {} ALTER COLUMN `{}` COMMENT '{}'".format(
                    full, col, self._esc(text)))
                applied += 1
            except Exception as e:
                print("[BRONZE][WARN] Comentario de '{}' falhou: {}".format(col, e))

        try:
            self._sql("ALTER TABLE {} SET TAGS ('nimbus_layer' = 'bronze', "
                      "'validated' = 'false')".format(full))
            applied += 1
        except Exception as e:
            print("[BRONZE][WARN] SET TAGS falhou: {}".format(e))
        print("[BRONZE] Metadados tecnicos aplicados em {}: {} itens".format(full, applied))
        return applied

    def upload_and_register_raw(self, local_path, table_name=None, dat_ref=None,
                                run_id=None, skip_comments=False):

        tbl = table_name or Path(local_path).stem
        fmt = self.detect_format(local_path)
        target = self.upload_raw(local_path, table_name=tbl, dat_ref=dat_ref, run_id=run_id)

        if fmt is None:
            print("[BRONZE] Formato '{}' nao registravel via read_files - "
                  "arquivo mantido no Volume sem tabela.".format(Path(local_path).suffix))
            return None

        full = self.register_raw(tbl, target, fmt, run_id=run_id, 
                                 dat_ref=dat_ref,
                                 json_root_key=self.json_root_key(local_path) if fmt == 'json' else None)
        if not skip_comments:
            self.describe_bronze(tbl, fmt)
        return full

def QuarantineUploader(BronzeUploader):
    TABLE_COMMENT = ("Quarentena do Nimbus: linhas barradas antes da silver, com as colunas "
                     "_reject_columns, _reject_values, e _reject_reason "
                     "(TYPE_NOT_CONFORMANT, DUPLICATE_PK ou regra de contrato). "
                     "Nao consumir para negocio - existe para auditoria e reprocessamento.")
    def bronze_table(self, table_name, fmt=None):
        return "quarantine_{}".format(BronzeUploader.bronze_table(self, table_name, fmt))

    def volume_dir(self, table_name):
        return "{}/_quarantine".format(BronzeUploader._volume_dir(self, table_name))


def get_bronze_uploader():
        import config as cfg
        return BronzeUploader(
            host         = getattr(cfg, "DATABRICKS_HOST",          ""),
            token        = getattr(cfg, "DATABRICKS_TOKEN",         ""),
            warehouse_id = getattr(cfg, "DATABRICKS_WAREHOUSE_ID",  ""),
            volume       = getattr(cfg, "DATABRICKS_BRONZE_VOLUME", "landing"),
            catalog      = getattr(cfg, "DATABRICKS_CATALOG",       "nimbus"),
            schema       = getattr(cfg, "DATABRICKS_BRONZE_SCHEMA",        "bronze"), 
        )

def publish_bronze(local_path, table_name, run_id=None, dat_ref=None):
        import config as cfg
        if not getattr(cfg, "DATABRICKS_BRONZE_UPLOAD", False):
            return{"table": table_name, "layer": "bronze", "status": "DISABLED",
                   "target": None, "error": None}
        if not databricks_configured():
            return{"table": table_name, "layer":"bronze", "status": "SKIPPED",
                   "target": None,
                   "error": "sem DATABRICKS_HOST/WAREHOUSE_ID - publicacao ignorada"}
        if dat_ref is None and run_id:
            dat_ref = dat_ref_from_run_id(run_id)
        try:
            full = get_bronze_uploader().upload_and_register_raw(
                local_path, table_name=table_name, dat_ref=dat_ref, run_id=run_id)
            return {"table":table_name, "layer": "bronze",
                    "status": "OK" if full else "UPLOADED", "target": full, "error": None}
        except Exception as e:
            print("[BRONZE] Publicacao Falhou em {}: {}".format(table_name, e))
            return {"table": table_name, "layer": "bronze", "status": "ERROR",
                    "target": None, "error": str(e)}
        
def get_quarantine_uploader():
    import config as cfg
    return QuarantineUploader(
        host         = getattr(cfg, "DATABRICKS_HOST",          ""),
        token        = getattr(cfg, "DATABRICKS_TOKEN",         ""),
        warehouse_id = getattr(cfg, "DATABRICKS_WAREHOUSE_ID",  ""),
        volume       = getattr(cfg, "DATABRICKS_BRONZE_VOLUME", "landing"),
        catalog      = getattr(cfg, "DATABRICKS_CATALOG",       "nimbus"),
        schema       = getattr(cfg, "DATABRICKS_BRONZE_SCHEMA",        "bronze"), 
    )

def pulish_quarantine(local_path, table_name, run_id=None, dat_ref=None):
    import config as cfg
    result = {"table": table_name, "layer": "quarantine", "status": None,
              "target": None, "error": None}
    enabled = getattr(cfg, "DATABRICKS_QUARANTINE_UPLOAD", 
                      getattr(cfg, "DATABRICKS_BRONZE_UPLOAD", False))
    
    if not enabled:
        return dict(result, status="DISABLED")
    if databricks_configured():
        return dict(result, status="SKIPPED",
                    error="sem DATABRICKS_HOST/WAREHOUSE_ID - publicacao ignorada")
    if local_path is None or not Path(local_path).exists():
        return dict(result, status="NO_DATA")
    if dat_ref is None and run_id:
        dat_ref= dat_ref_from_run_id(run_id)
    try:
        full = get_quarantine_uploader().upload_and_register_raw(
            local_path, table_name=table_name, dat_ref=dat_ref, run_id=run_id)
        return dict(result, status="OK" if full else "UPLOADED", target=full)
    except Exception as e:
        print("[QUARANTINE] Publicacao falhou em {}: {}".format(table_name, e))
        return dict(result, error="ERROR", error=str(e))
    
    

    


