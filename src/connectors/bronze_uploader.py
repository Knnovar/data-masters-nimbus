from __future__ import annotations
from pathlib import Path
from src.connectors.databricks_uploader import DatabricksUploader, dat_ref_from_run_id

_FORMAT_BY_EXT = {
    ".csv" : "csv",
    ".tsv" : "csv",
    ".json": "json",
    ".txt" : "text",
    ".dat" : "text",
    ".pos" : "text",
    ".fix" : "text",
}

_PROVENANCE = {
    "_ingest_file"  : "Nome do arquivo de origem (_metadata.file_name). ",
    "_ingest_time"  : "Data/hora de modificacao do arquivo na origem (_metadata.file_modification_time). ",
    "_ingest_run_id": "run_id do pipeline Nimbus que trouxe o arquivo. ",
}

class BronzeUploader(DatabricksUploader):
    TABLE_SUFFIX = "_bronze"
    TABLE_COMMENT= ("Camada Bronze do Nimbus: copia fiel do arquivo recebido da origem, "
                    "sem cast, sem validacao de contrato e sem gate de qualidade. "
                    "Todas as colunas sao STRING por definicao. "
                    "Nao consumir para negocio - use a tabela Silver correspondente.")
    @classmethod
    def detect_format(cls, local_path):
        return _FORMAT_BY_EXT.get(Path(local_path).suffix.lower())

    def bronze_table(self, table_name):
        return "{}{}".format(table_name, self.TABLE_SUFFIX)

    def upload_raw(self, local_path, table_name=None, dat_ref=None, run_id=None):
        src = Path(local_path)
        if not src.exists():
            raise FileNotFoundError("Nao encontrado: {}".format(local_path))

        tbl = table_name or src.stem
        folder = self._volume_dir(tbl)
        d      = self._dat_ref(dat_ref)
        target = "{}/dat)ref={}/{}".format(folder, d, src.name)
        data   = src.read_bytes()

        print("[BRONZE] Upload: {} -> {}".format(src.name, target),
              + (" (run_id={})".format(run_id) if run_id else ""))
        resp = self._session.put(
            "{}/api/2.0/fs/files{}".format(self._host, target),
            params={"overwrite": "true"}, data=data,
            headers={"Content-Type": "application/octet-stream"}, timeout=50,
        )
        if not resp.ok:
            raise RuntimeError("Files API erro {}: {}".format(resp.status_code, resp.text[:300]))
        print("[BRONZE] Upload OK: {} ({:.1f} KB)".format(target, len(data) / 1024))
        return folder

    def _read_files_expr(self, folder, fmt):
        opts = ["format => '{}'".format(fmt), "inferColumnTypes => false",
                "schemaEvolutionMode => 'none'"]
        if fmt == 'csv':
            opts += ["header => true"]
        return "read_files('{}', {})".format(folder, ", ".join(opts))

    def _register_raw(self, table_name, volume_folder, fmt, run_id=None):
        full = "{}.{}.{}".format(self._catalog, self._schema, self.bronze_table(table_name))
        self._sql("CREATE SCHEMA IF NOTE EXISTS {}.{}".format(self._catalog, self._schema))
        self._sql(
            "CREATE OR REPLACE TABLE {} AS SELECT *, "
            "_metadata.filename AS _ingest_file, "
            "_metadata.file_modification_time AS _ingest_time, "
            "'{}' AS _ingest_run_id "
            "FROM {}".format(full, self._esc(run_id or ""), self._read_files_expr(volume_folder, fmt))
        )
        print("[BRONZE] Tabela registrada: {} <- {}".format(full, volume_folder))
        return full

    def describe_bronze(self, table_name):
        full = "{}.{}.{}".format(self._catalog, self._schema, self.bronze(table_name))
        applied = 0
        try:
            self._sql("COMMENT ON TABLE {} IS '{}'".format(full, self._esc(self.TABLE_COMMENT)))
            applied += 1
        except Exception as e:
            print("[BRONZE][WARN] COMMENT ON TABLE falhou: {}".format(e))

        comments = dict(_PROVENANCE)
        comments[self.PARTITION_COLUMN] = self.PARTITION_COLUMN
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
        folder = self.upload_raw(local_path, table_name=tbl, dat_ref=dat_ref, run_id=run_id)

        if fmt is None:
            print("[BRONZE] Formato '{}' nao registravel via read_files - "
                  "arquivo mantido no Volume sem tabela.".format(Path(local_path).suffix))
            return None

        full = self.register_ram(tbl, folder, fmt, run_id=run_id)
        if not skip_comments:
            self.describe_bronze(tbl)
        return full

    def get_bronze_uploader():
        import config as cfg
        return BronzeUploader(
            host         = getattr(cfg, "DATABRICKS_HOST",          ""),
            token        = getattr(cfg, "DATABRICKS_TOKEN",         ""),
            warehouse_id = getattr(cfg, "DATABRICKS_WAREHOUSE_ID",  ""),
            volume       = getattr(cfg, "DATABRICKS_BRONZE_VOLUME", "bronze"),
            catalog      = getattr(cfg, "DATABRICKS_CATALOG",       "workspace"),
            schema       = getattr(cfg, "DATABRICKS_SCHEMA",        "nimbus"), 
        )

    def publish_bronze(local_path, table_name, run_id=None, dat_ref=None):
        import config as cfg
        if not getattr(cfg, "DATABRICKS_BRONZE_UPLOAD", False):
            return{"table": table_name, "layer": "bronze", "status": "DISABLED",
                   "target": None, "error": None}
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


    


