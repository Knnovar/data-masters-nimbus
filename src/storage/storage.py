"""
src/storage/storage.py — Camada de abstração de storage com suporte a Parquet.

Estratégia de formato por camada:
  Bronze     → formato original preservado (CSV, JSON, TXT…)
  Silver     → Parquet via promote_to_parquet() após validação
  Gold       → Parquet
  Quarantine → formato original (cópia fiel do arquivo rejeitado)
  Contracts / Metrics / Reports → texto (YAML, JSON, MD)
"""

import io, json, shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

import pandas as pd
import pyarrow as pa


class StorageBase(ABC):
    @abstractmethod
    def write(self, layer, filename, df): pass
    @abstractmethod
    def write_parquet(self, layer, filename, df): pass
    @abstractmethod
    def read(self, layer, filename): pass
    @abstractmethod
    def move(self, filename, from_layer, to_layer): pass
    @abstractmethod
    def promote_to_parquet(self, filename, from_layer, to_layer, contract=None): pass
    @abstractmethod
    def list(self, layer): pass
    @abstractmethod
    def exists(self, layer, filename): pass
    @abstractmethod
    def write_text(self, layer, filename, content): pass
    @abstractmethod
    def read_path(self, layer, filename): pass


def _parquet_name(filename):
    return Path(filename).stem + ".parquet"


def _read_file(path):
    ext = path.suffix.lower()
    if ext == ".parquet":
        return pd.read_parquet(path)
    if ext == ".json":
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
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
                    except json.JSONDecodeError: continue
        return pd.json_normalize(records, max_level=5).astype(str)
    if ext in (".txt", ".dat", ".pos", ".fix"):
        sidecar = path.parent / (path.name + ".layout")
        if sidecar.exists():
            spec = json.loads(sidecar.read_text(encoding="utf-8"))
            return pd.read_fwf(path, colspecs=[tuple(c) for c in spec["colspecs"]],
                               names=spec["names"], dtype=str)
        try: return pd.read_fwf(path, dtype=str)
        except: return pd.read_csv(path, sep=r"\s+", dtype=str,
                                   on_bad_lines="skip", engine="python")
    sep = "\t" if ext == ".tsv" else ","
    return pd.read_csv(path, low_memory=False, dtype=str, sep=sep)


class LocalStorage(StorageBase):
    def __init__(self, layer_map):
        self._layers = layer_map
        for path in layer_map.values():
            path.mkdir(parents=True, exist_ok=True)

    def _path(self, layer, filename):
        if layer not in self._layers:
            raise ValueError("Camada desconhecida: '{}'. Disponiveis: {}".format(
                layer, list(self._layers)))
        return self._layers[layer] / filename

    def write(self, layer, filename, df):
        path = self._path(layer, filename)
        df.to_csv(path, index=False, lineterminator="\n")
        print("   [WRITE] [{}] {} gravado ({} linhas)".format(layer.upper(), filename, len(df)))

    def write_parquet(self, layer, filename, df):
        """Grava Parquet simples (sem schema do Manifest). Usado por testes e MinIO."""""
        return self._write_parquet_with_schema(layer, filename, df,
                                               arrow_schema=None, metadata=None)

    def write_text(self, layer, filename, content):
        self._path(layer, filename).write_text(content, encoding="utf-8")

    def read(self, layer, filename):
        return _read_file(self._path(layer, filename))

    def read_path(self, layer, filename):
        return self._path(layer, filename)

    def move(self, filename, from_layer, to_layer):
        src = self._path(from_layer, filename)
        dst = self._path(to_layer, filename)
        if dst.exists(): dst.unlink()
        shutil.move(str(src), str(dst))
        print("   [MOVE] {}: {} -> {}".format(filename, from_layer.upper(), to_layer.upper()))

    def promote_to_parquet(self, filename, from_layer, to_layer, contract=None):
        from src.storage.schema_utils import (
            apply_manifest_schema, manifest_to_arrow_schema, build_parquet_metadata
        )
        src = self._path(from_layer, filename)
        df  = _read_file(src)

        schema_meta = None
        if contract is not None:
            # Identifica colunas extras (NON_BREAKING) presentes no dado mas nao no Manifest
            manifest_cols = {c.name.lower() for c in contract.schema}
            extra_cols    = [c for c in df.columns if c.lower() not in manifest_cols]

            df, cast_warnings = apply_manifest_schema(df, contract)
            arrow_schema      = manifest_to_arrow_schema(contract, extra_columns=extra_cols)
            schema_meta       = build_parquet_metadata(contract, cast_warnings)

            if cast_warnings:
                for w in cast_warnings:
                    print("   [SCHEMA] [{}] {}".format(filename, w))
        else:
            arrow_schema = None
            schema_meta  = None

        pq = self._write_parquet_with_schema(
            to_layer, filename, df, arrow_schema, schema_meta
        )

        # Arquiva o original em bronze/_archive/ para rastreabilidade
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

        # Upload opcional para Databricks
        if to_layer == "silver":
            from src.connectors.databricks_uploader import upload_silver_table
            upload_silver_table(self._path(to_layer, pq), table_name=Path(filename).stem)
            # try:
            #     from src.connectors.databricks_uploader import upload_silver_table
            #     upload_silver_table(self._path(to_layer, pq), table_name=Path(filename).stem)
            # except Exception as e:
            #     print("   [DATABRICKS] Upload ignorado: {}".format(e))

        return pq

    def _write_parquet_with_schema(self, layer, filename, df, arrow_schema, metadata):
        """Grava Parquet com schema e metadata opcionais do Manifest."""
        import pyarrow as pa
        import pyarrow.parquet as pq_mod

        pq_filename = _parquet_name(filename)
        path        = self._path(layer, pq_filename)

        try:
            table = pa.Table.from_pandas(df, schema=arrow_schema, safe=False)
        except Exception:
            # Fallback: deixa o pyarrow inferir se o schema declarado falhar
            print("   [SCHEMA] Schema do Manifest falhou, usando inferencia.")
            table = pa.Table.from_pandas(df)

        if metadata:
            existing_meta = table.schema.metadata or {}
            table = table.replace_schema_metadata({**existing_meta, **metadata})

        pq_mod.write_table(table, path, compression="snappy")
        size_kb = path.stat().st_size / 1024
        source  = "manifest" if arrow_schema else "inferido"
        print("   [PARQUET] [{}] {} ({} linhas, {:.1f} KB, schema={})".format(
            layer.upper(), pq_filename, len(df), size_kb, source))
        return pq_filename

    def list(self, layer):
        exts = {".csv", ".parquet", ".json", ".jsonl", ".txt", ".dat"}
        return [f.name for f in self._layers[layer].iterdir()
                if f.suffix.lower() in exts]

    def exists(self, layer, filename):
        return self._path(layer, filename).exists()


class MinIOStorage(StorageBase):
    def __init__(self, endpoint, access_key, secret_key, layer_map, tmp_dir):
        try:
            from minio import Minio
            from minio.error import S3Error
            self._S3Error = S3Error
        except ImportError:
            raise ImportError("Execute: pip install minio")
        from minio import Minio
        self._client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=False)
        self._layers = layer_map
        self._tmp    = tmp_dir
        self._tmp.mkdir(parents=True, exist_ok=True)
        self._ensure_buckets()

    def _ensure_buckets(self):
        for bucket in self._layers.values():
            if not self._client.bucket_exists(bucket):
                self._client.make_bucket(bucket)

    def _bucket(self, layer):
        if layer not in self._layers:
            raise ValueError("Camada desconhecida: '{}'".format(layer))
        return self._layers[layer]

    def write(self, layer, filename, df):
        buf = io.BytesIO(df.to_csv(index=False, lineterminator="\n").encode("utf-8"))
        self._client.put_object(self._bucket(layer), filename, buf,
            length=buf.getbuffer().nbytes, content_type="text/csv")
        print("   [WRITE] [{}] {} -> MinIO ({} linhas)".format(layer.upper(), filename, len(df)))

    def write_parquet(self, layer, filename, df):
        import tempfile, os
        pq  = _parquet_name(filename)
        tmp = self._tmp / pq
        df.to_parquet(tmp, index=False, engine="pyarrow", compression="snappy")
        data = tmp.read_bytes()
        self._client.put_object(self._bucket(layer), pq, io.BytesIO(data),
            length=len(data), content_type="application/octet-stream")
        print("   [PARQUET] [{}] {} -> MinIO ({} linhas, {:.1f} KB)".format(
            layer.upper(), pq, len(df), len(data)/1024))
        return pq

    def write_text(self, layer, filename, content):
        buf = io.BytesIO(content.encode("utf-8"))
        self._client.put_object(self._bucket(layer), filename, buf,
            length=buf.getbuffer().nbytes, content_type="text/plain")

    def read(self, layer, filename):
        ext = Path(filename).suffix.lower()
        if ext == ".parquet":
            tmp = self._tmp / filename
            self._client.fget_object(self._bucket(layer), filename, str(tmp))
            return pd.read_parquet(tmp)
        response = self._client.get_object(self._bucket(layer), filename)
        return pd.read_csv(io.BytesIO(response.read()), low_memory=False, dtype=str)

    def read_path(self, layer, filename):
        tmp = self._tmp / filename
        self._client.fget_object(self._bucket(layer), filename, str(tmp))
        return tmp

    def move(self, filename, from_layer, to_layer):
        from minio.commonconfig import CopySource
        self._client.copy_object(self._bucket(to_layer), filename,
                                 CopySource(self._bucket(from_layer), filename))
        self._client.remove_object(self._bucket(from_layer), filename)
        print("   [MOVE] {}: {} -> {} (MinIO)".format(
            filename, from_layer.upper(), to_layer.upper()))

    def promote_to_parquet(self, filename, from_layer, to_layer, contract=None):
        tmp = self._tmp / filename
        self._client.fget_object(self._bucket(from_layer), filename, str(tmp))
        df  = _read_file(tmp)
        pq  = self.write_parquet(to_layer, filename, df)
        self._client.remove_object(self._bucket(from_layer), filename)
        print("   [PROMOTE] {} -> {}/{} (MinIO Parquet)".format(
            filename, to_layer.upper(), pq))
        if to_layer == "silver":
            try:
                from src.connectors.databricks_uploader import upload_silver_table
                upload_silver_table(self._tmp / pq, table_name=Path(filename).stem)
            except Exception as e:
                print("   [DATABRICKS] Upload ignorado: {}".format(e))
        return pq

    def list(self, layer):
        objects = self._client.list_objects(self._bucket(layer))
        return [o.object_name for o in objects
                if o.object_name.endswith((".csv", ".parquet", ".json"))]

    def exists(self, layer, filename):
        try:
            self._client.stat_object(self._bucket(layer), filename)
            return True
        except self._S3Error:
            return False


def get_storage():
    import config as cfg
    LAYERS = ["bronze","silver","gold","quarantine","contracts","metrics","reports"]
    if not getattr(cfg, "USE_MINIO", False):
        local_map = {
            "bronze"    : cfg.DATA_DIR / "landing",
            "silver"    : cfg.DATA_DIR / "processed",
            "gold"      : cfg.DATA_DIR / "gold",
            "quarantine": cfg.DATA_DIR / "quarantine",
            "contracts" : cfg.DATA_DIR / "contracts",
            "metrics"   : cfg.DATA_DIR / "metrics",
            "reports"   : cfg.DATA_DIR / "reports",
        }
        return LocalStorage(local_map)
    minio_map = {l: "nimbus-{}".format(l) for l in LAYERS}
    return MinIOStorage(
        endpoint   = getattr(cfg, "MINIO_ENDPOINT",   "localhost:9000"),
        access_key = getattr(cfg, "MINIO_ACCESS_KEY", "minioadmin"),
        secret_key = getattr(cfg, "MINIO_SECRET_KEY", "minioadmin"),
        layer_map  = minio_map,
        tmp_dir    = cfg.DATA_DIR / "_tmp_minio",
    )
