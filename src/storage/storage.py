"""src/storage/storage.py — Abstração medallion com suporte a Parquet governado pelo Manifest."""
import io, json, shutil
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd

LINEAGE_COLUMNS = ["_ingest_file", "_ingest_format", "_ingest_time", "_ingest_run_id"]

_FORMAT_BY_SUFFIX = {
    ".csv": "csv", ".tsv": "tsv",
    ".json": "json", ".jsonl": "json", ".ndjson": "json",
    ".txt": "fixed", ".dat": "fixed", ".pos": "fixed", ".fix": "fixed",
    ".parquet": "parquet",
}

FIXED_SUFFIXES = {".txt", ".dat", ".pos", ".fix"}
DATA_SUFFIXES = {".csv", ".tsv", ".json", ".jsonl", ".ndjson",
                 ".txt", ".dat", ".pos", ".fix", ".parquet"}

def ingest_format(filename) -> str:
    return _FORMAT_BY_SUFFIX.get(Path(filename).suffix.lower(), "outro")

def add_lineage_columns(df, filename, run_id=None):
    """Acrescenta a linhagem tecnica ao Dataframe ja tipado.
    
    Aplicada depois do cast, de proposito: estas colunas nao sao declaradas no
    Manifest e nao devem aparecer como EXTRA_COLUMN nem passar pelo caster.
    """

    df = df.copy()
    df["_ingest_file"]      = Path(filename).name
    df["_ingest_format"]    = ingest_format(filename)
    df["_ingest_time"]      = datetime.now(timezone.utc).isoformat(timespec="seconds")
    df["_ingest_run_id"]    = run_id or ""
    return df
class StorageBase(ABC):
    last_cast_report: dict = {}
    last_reject_report: dict = {}
    @abstractmethod
    def write(self, layer, filename, df): pass
    @abstractmethod
    def write_parquet(self, layer, filename, df): pass
    @abstractmethod
    def read(self, layer, filename): pass
    @abstractmethod
    def move(self, filename, from_layer, to_layer): pass
    @abstractmethod
    def promote_to_parquet(self, filename, from_layer, to_layer, contract=None, run_id=None): pass
    @abstractmethod
    def list(self, layer): pass
    @abstractmethod
    def exists(self, layer, filename): pass
    @abstractmethod
    def write_text(self, layer, filename, content): pass
    @abstractmethod
    def read_path(self, layer, filename): pass

def _parquet_name(filename): return Path(filename).stem + ".parquet"

def _csv_name(filename): return Path(filename).stem + ".csv"

def _strict_typing():
    import config
    return getattr(config, "STRICT_TYPING", True)

def _apply_contract(storage, df, filename, contract):
    if contract is None:
        return df, None, None
    from src.storage.schema_utils import (apply_manifest_schema,manifest_to_arrow_schema,build_parquet_metadata)
    manifest_cols = {c.name.lower() for c in contract.schema}
    extra_cols = [c for c in df.columns if c.lower() not in manifest_cols]
    cast_report = {}
    if _strict_typing():
        from src.storage.strict_cast import apply_strict_schema
        df, rejected, cast_warnings, reject_summary = apply_strict_schema(df, contract, report=cast_report)
        storage.last_reject_report = reject_summary
        if len(rejected):
            storage.write("quarantine", "reject_" + _csv_name(filename), rejected)
    else:
        df, cast_warnings = apply_manifest_schema(df, contract, report=cast_report)
    storage.last_cast_report = cast_report
    arrow_schema = manifest_to_arrow_schema(contract, extra_columns=extra_cols + LINEAGE_COLUMNS)
    metadata = build_parquet_metadata(contract, cast_warnings)
    for w in cast_warnings:
        print("     [SCHEMA] [{}] {}".format(filename, w))
    return df, arrow_schema, metadata

def _read_file(path):
    ext = path.suffix.lower()
    if ext == ".parquet": return pd.read_parquet(path)
    if ext == ".json":
        with open(path, encoding="utf-8") as f: data = json.load(f)
        if isinstance(data, dict):
            for v in data.values():
                if isinstance(v, list): data = v; break
        if not isinstance(data, list): data = [data]
        return pd.json_normalize(data, max_level=5).astype(str)
    if ext in (".jsonl", ".ndjson"):
        records = []
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try: records.append(json.loads(line))
                    except: continue
        return pd.json_normalize(records, max_level=5).astype(str)
    if ext in FIXED_SUFFIXES:
        sidecar = path.parent / (path.name + ".layout")
        if sidecar.exists():
            spec = json.loads(sidecar.read_text(encoding="utf-8"))
            return pd.read_fwf(path, colspecs=[tuple(c) for c in spec["colspecs"]],
                               names=spec["names"], dtype=str)
        try: return pd.read_fwf(path, dtype=str)
        except: return pd.read_csv(path, sep=r"\s+", dtype=str, on_bad_lines="skip", engine="python")
    sep = "\t" if ext == ".tsv" else ","
    return pd.read_csv(path, low_memory=False, dtype=str, sep=sep)

class LocalStorage(StorageBase):
    def __init__(self, layer_map):
        self._layers = layer_map
        for path in layer_map.values(): path.mkdir(parents=True, exist_ok=True)

    def _path(self, layer, filename):
        if layer not in self._layers:
            raise ValueError("Camada desconhecida: '{}'. Disponiveis: {}".format(layer, list(self._layers)))
        return self._layers[layer] / filename

    def write(self, layer, filename, df):
        df.to_csv(self._path(layer, filename), index=False, lineterminator="\n")
        print("   [WRITE] [{}] {} ({} linhas)".format(layer.upper(), filename, len(df)))

    def _write_parquet_internal(self, layer, filename, df, arrow_schema=None, metadata=None):
        import pyarrow as pa, pyarrow.parquet as pq
        pq_name = _parquet_name(filename)
        path    = self._path(layer, pq_name)
        try:
            table = pa.Table.from_pandas(df, schema=arrow_schema, safe=False)
        except Exception:
            table = pa.Table.from_pandas(df)
        if metadata:
            existing = table.schema.metadata or {}
            table = table.replace_schema_metadata({**existing, **metadata})
        pq.write_table(table, path, compression="snappy")
        size_kb = path.stat().st_size / 1024
        src = "manifest" if arrow_schema else "inferido"
        print("   [PARQUET] [{}] {} ({} linhas, {:.1f} KB, schema={})".format(
            layer.upper(), pq_name, len(df), size_kb, src))
        return pq_name

    def write_parquet(self, layer, filename, df):
        return self._write_parquet_internal(layer, filename, df)

    def write_text(self, layer, filename, content):
        self._path(layer, filename).write_text(content, encoding="utf-8")

    def read(self, layer, filename): return _read_file(self._path(layer, filename))
    def read_path(self, layer, filename): return self._path(layer, filename)

    def move(self, filename, from_layer, to_layer):
        src = self._path(from_layer, filename)
        dst = self._path(to_layer, filename)
        if dst.exists(): dst.unlink()
        shutil.move(str(src), str(dst))
        print("   [MOVE] {}: {} -> {}".format(filename, from_layer.upper(), to_layer.upper()))

    def promote_to_parquet(self, filename, from_layer, to_layer, contract=None, run_id=None):
        self.last_cast_report = {}
        self.last_reject_report = {}
        src = self._path(from_layer, filename)
        df  = _read_file(src)
        df, arrow_schema, metadata = _apply_contract(self, df, filename, contract)
        df = add_lineage_columns(df, filename, run_id)
        pq = self._write_parquet_internal(to_layer, filename, df, arrow_schema, metadata)
        archive_dir = src.parent / "_archive"
        archive_dir.mkdir(exist_ok=True)
        archived = archive_dir / src.name
        if archived.exists(): archived.unlink()
        shutil.move(str(src), str(archived))
        sidecar = src.parent / (src.name + ".layout")
        if sidecar.exists():
            shutil.move(str(sidecar), str(archive_dir / sidecar.name))
        print("   [PROMOTE] {} -> {}/{} (snappy) | original em {}/_archive/".format(
            filename, to_layer.upper(), pq, from_layer))
        # if to_layer == "silver":
        #     try:
        #         from src.connectors.databricks_uploader import upload_silver_table
        #         upload_silver_table(self._path(to_layer, pq),
        #                             table_name=Path(filename).stem, contract=contract)
        #     except Exception as e:
        #         print("[DATABRICKS] Upload ignorado: {}".format(e))
        return pq

    def list(self, layer):
        return [f.name for f in self._layers[layer].iterdir()
                if f.suffix.lower() in DATA_SUFFIXES]

    def exists(self, layer, filename): return self._path(layer, filename).exists()

class MinIOStorage(StorageBase):
    def __init__(self, endpoint, access_key, secret_key, layer_map, tmp_dir, 
                 secure=False, region=None, create_buckets=True):
        try:
            from minio import Minio
            from minio.error import S3Error
            self._S3Error = S3Error
        except ImportError:
            raise ImportError("Execute: pip install minio")
        self._client = Minio(endpoint, access_key=access_key, secret_key=secret_key,
                             secure=secure, region=region)
        self._layers = layer_map
        self._tmp = tmp_dir
        self._tmp.mkdir(parents=True, exist_ok=True)
        for bucket in layer_map.values():
            if self._client.bucket_exists(bucket):
                continue
            if not create_buckets:
                raise RuntimeError(
                    "Bucket '{}' nao existe e MINIO_CREATE_BUCKETS=false: " \
                    "crie o bucket pelo provedor antes de executar.".format(bucket)
                )
            self._client.make_bucket(bucket)

    def _bucket(self, layer):
        if layer not in self._layers: raise ValueError("Camada desconhecida: '{}'".format(layer))
        return self._layers[layer]

    def write(self, layer, filename, df):
        buf = io.BytesIO(df.to_csv(index=False, lineterminator="\n").encode("utf-8"))
        self._client.put_object(self._bucket(layer), filename, buf,
            length=buf.getbuffer().nbytes, content_type="text/csv")
        print("   [WRITE] [{}] {} -> MinIO ({} linhas)".format(layer.upper(), filename, len(df)))

    def write_parquet(self, layer, filename, df, arrow_schema=None, metadata=None):
        import pyarrow as pa, pyarrow.parquet as pq
        pq_name = _parquet_name(filename)
        tmp = self._tmp / pq_name
        try:
            table = pa.Table.from_pandas(df, schema=arrow_schema, safe=False)
        except Exception:
            table = pa.Table.from_pandas(df)
        if metadata:
            existing = table.schema.metadata or {}
            table = table.replace_schema_metadata({**existing, **metadata})
        pq.write_table(table, tmp, compression="snappy")
        data = tmp.read_bytes()
        self._client.put_object(self._bucket(layer), pq_name, io.BytesIO(data), length=len(data),
                                content_type="application/octet-stream")
        src = "manifest" if arrow_schema else "inferido"
        print("     [PARQUET] [{}] {} -> MinIO ({} linhas, {:.1f} KB, schema={})".format(
            layer.upper(), pq_name, len(df), len(data)/1024, src
        ))
        return pq_name

    def write_text(self, layer, filename, content):
        buf = io.BytesIO(content.encode("utf-8"))
        self._client.put_object(self._bucket(layer), filename, buf,
            length=buf.getbuffer().nbytes, content_type="text/plain")

    def read(self, layer, filename):
        """Le pelo mesmo dispatcher do backend local: CSV, JSON, JSONL e fixo."""
        return _read_file(self.read_path(layer, filename))

    def read_path(self, layer, filename):
        tmp = self._tmp / filename
        self._client.fget_object(self._bucket(layer), filename, str(tmp))
        if Path(filename).suffix.lower() in FIXED_SUFFIXES:
            sidecar = filename + ".layout"
            if self.exists(layer, sidecar):
                self._client.fget_object(self._bucket(layer), sidecar, str(self._tmp / sidecar))
        return tmp

    def move(self, filename, from_layer, to_layer):
        from minio.commonconfig import CopySource
        self._client.copy_object(self._bucket(to_layer), filename,
                                 CopySource(self._bucket(from_layer), filename))
        self._client.remove_object(self._bucket(from_layer), filename)

    def promote_to_parquet(self, filename, from_layer, to_layer, contract=None, run_id=None):
        self.last_cast_report = {}
        self.last_reject_report = {}
        tmp = self.read_path(from_layer, filename)
        df = _read_file(tmp)
        df, arrow_schema, metadata = _apply_contract(self, df, filename, contract)
        df = add_lineage_columns(df, filename, run_id)
        pq = self.write_parquet(to_layer, filename, df, arrow_schema, metadata)
        self._archive(from_layer, filename)
        print("  [PROMOTE] {} -> {}/{} (snappy) | original em {}/_archive".format(
            filename, to_layer.upper(), pq, from_layer
        ))
        return pq

    def _archive(self, layer, filename):
        from minio.commonconfig import CopySource
        bucket = self._bucket(layer)
        for name in (filename, filename + ".layout"):
            if not self.exists(layer, name):
                continue
            self._client.copy_object(bucket, "_archive/" + name, CopySource(bucket, name))
            self._client.remove_object(bucket, name)


    def list(self, layer):
        return [o.object_name for o in self._client.list_objects(self._bucket(layer))
                if Path(o.object_name).suffix.lower() in DATA_SUFFIXES]

    def exists(self, layer, filename):
        try: self._client.stat_object(self._bucket(layer), filename); return True
        except self._S3Error: return False

def get_storage():
    import config as cfg
    LAYERS = ["bronze","silver","gold","quarantine","contracts","metrics","reports"]
    if not getattr(cfg, "USE_MINIO", False):
        return LocalStorage({
            "bronze":     cfg.DATA_DIR / "landing",
            "silver":     cfg.DATA_DIR / "processed",
            "gold":       cfg.DATA_DIR / "gold",
            "quarantine": cfg.DATA_DIR / "quarantine",
            "contracts":  cfg.DATA_DIR / "contracts",
            "metrics":    cfg.DATA_DIR / "metrics",
            "reports":    cfg.DATA_DIR / "reports",
        })
    prefix = getattr(cfg, "BUCKET_PREFIX", "nimbus")
    return MinIOStorage(
        endpoint   = getattr(cfg, "MINIO_ENDPOINT",   "localhost:9000"),
        access_key = getattr(cfg, "MINIO_ACCESS_KEY", "minioadmin"),
        secret_key = getattr(cfg, "MINIO_SECRET_KEY", "minioadmin"),
        layer_map  = {l: "{}-{}".format(prefix, l) for l in LAYERS},
        tmp_dir    = cfg.DATA_DIR / "_tmp_minio",
        secure     = getattr(cfg, "MINIO_SECURE", False),
        region     = getattr(cfg, "MINIO_REGION", None),
        create_buckets = getattr(cfg, "MINIO_CREATE_BUCKETS", True),
    )
