"""
src/storage/storage.py — Camada de abstração de storage

Implementa o padrão de arquitetura medallion (Bronze → Silver → Gold)
com dois backends intercambiáveis:

  LocalStorage  → disco local (padrão, sem dependências externas)
  MinIOStorage  → MinIO/S3 (requer docker-compose up -d)

Estratégia de formato por camada:
  Bronze     → formato original do arquivo de origem (CSV, JSON, TXT…)
               Preservado exatamente como chegou, para rastreabilidade.
  Silver     → Parquet (compressão + schema embutido)
               Convertido na promoção Bronze → Silver pelo profiler.
  Gold       → Parquet
  Quarantine → formato original (cópia fiel do arquivo rejeitado)
  Contracts / Metrics / Reports → texto (YAML, JSON, MD)

A conversão para Parquet acontece no método promote_to_parquet(),
chamado pelo profiler após a validação bem-sucedida.
"""

import io
import json
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

import pandas as pd


# ─────────────────────────────────────────────────────────────────────────────
# Interface base
# ─────────────────────────────────────────────────────────────────────────────

class StorageBase(ABC):
    """Interface comum para todos os backends de storage."""

    @abstractmethod
    def write(self, layer: str, filename: str, df: pd.DataFrame) -> None:
        """Persiste um DataFrame como CSV na camada indicada."""

    @abstractmethod
    def write_parquet(self, layer: str, filename: str, df: pd.DataFrame) -> str:
        """
        Persiste um DataFrame como Parquet na camada indicada.
        Retorna o nome do arquivo Parquet gravado (com extensão .parquet).
        """

    @abstractmethod
    def read(self, layer: str, filename: str) -> pd.DataFrame:
        """Lê um arquivo da camada indicada e retorna um DataFrame."""

    @abstractmethod
    def move(self, filename: str, from_layer: str, to_layer: str) -> None:
        """Promove um arquivo entre camadas sem conversão de formato."""

    @abstractmethod
    def promote_to_parquet(
        self, filename: str, from_layer: str, to_layer: str
    ) -> str:
        """
        Promove um arquivo de uma camada para outra convertendo para Parquet.
        O arquivo original na camada de origem é removido após a conversão.
        Retorna o nome do arquivo Parquet gerado no destino.
        """

    @abstractmethod
    def list(self, layer: str) -> list:
        """Lista os arquivos disponíveis em uma camada."""

    @abstractmethod
    def exists(self, layer: str, filename: str) -> bool:
        """Verifica se um arquivo existe em uma camada."""

    @abstractmethod
    def write_text(self, layer: str, filename: str, content: str) -> None:
        """Persiste conteúdo texto (YAML, MD, JSON) na camada indicada."""

    @abstractmethod
    def read_path(self, layer: str, filename: str) -> Path:
        """
        Retorna um Path local para o arquivo.
        No MinIOStorage, faz download temporário para disco.
        """


# ─────────────────────────────────────────────────────────────────────────────
# Helpers de formato
# ─────────────────────────────────────────────────────────────────────────────

def _parquet_name(filename: str) -> str:
    """Converte qualquer nome de arquivo para a extensão .parquet."""
    return Path(filename).stem + ".parquet"


def _read_file(path: Path) -> pd.DataFrame:
    """
    Lê um arquivo detectando o formato pela extensão.
    Suporta: .parquet, .csv/.tsv, .json/.jsonl/.ndjson, .txt/.dat (fixed-width).
    """
    ext = path.suffix.lower()

    if ext == ".parquet":
        return pd.read_parquet(path)

    if ext == ".json":
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            for v in data.values():
                if isinstance(v, list):
                    data = v
                    break
        if not isinstance(data, list):
            data = [data]
        return pd.json_normalize(data, max_level=5).astype(str)

    if ext in (".jsonl", ".ndjson"):
        records = []
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return pd.json_normalize(records, max_level=5).astype(str)

    if ext in (".txt", ".dat", ".pos", ".fix"):
        sidecar = path.parent / (path.name + ".layout")
        if sidecar.exists():
            spec     = json.loads(sidecar.read_text(encoding="utf-8"))
            colspecs = [tuple(cs) for cs in spec["colspecs"]]
            return pd.read_fwf(path, colspecs=colspecs, names=spec["names"], dtype=str)
        try:
            return pd.read_fwf(path, dtype=str)
        except Exception:
            return pd.read_csv(
                path, sep=r"\s+", dtype=str, on_bad_lines="skip", engine="python"
            )

    sep = "\t" if ext == ".tsv" else ","
    return pd.read_csv(path, low_memory=False, dtype=str, sep=sep)


# ─────────────────────────────────────────────────────────────────────────────
# Backend local
# ─────────────────────────────────────────────────────────────────────────────

class LocalStorage(StorageBase):
    """
    Backend de disco local.

    Estratégia de formato:
        Bronze / Quarantine → formato original preservado
        Silver / Gold       → Parquet (via promote_to_parquet)
        Contracts / Metrics / Reports → texto
    """

    def __init__(self, layer_map: dict):
        self._layers = layer_map
        for path in layer_map.values():
            path.mkdir(parents=True, exist_ok=True)

    def _path(self, layer: str, filename: str) -> Path:
        if layer not in self._layers:
            raise ValueError(
                "Camada desconhecida: '{}'. Disponiveis: {}".format(
                    layer, list(self._layers)
                )
            )
        return self._layers[layer] / filename

    # ── Escrita ───────────────────────────────────────────────────────────────

    def write(self, layer: str, filename: str, df: pd.DataFrame) -> None:
        """Grava CSV — usado no Bronze e na Quarantine."""
        path = self._path(layer, filename)
        df.to_csv(path, index=False, lineterminator="\n")
        print("   [WRITE] [{}] {} gravado ({} linhas)".format(
            layer.upper(), filename, len(df)
        ))

    def write_parquet(self, layer: str, filename: str, df: pd.DataFrame) -> str:
        """
        Grava Parquet na camada indicada.
        Converte o nome do arquivo para .parquet automaticamente.
        Retorna o nome do arquivo gravado.
        """
        parquet_filename = _parquet_name(filename)
        path             = self._path(layer, parquet_filename)
        df.to_parquet(path, index=False, engine="pyarrow", compression="snappy")
        size_kb = path.stat().st_size / 1024
        print("   [PARQUET] [{}] {} gravado ({} linhas, {:.1f} KB)".format(
            layer.upper(), parquet_filename, len(df), size_kb
        ))
        return parquet_filename

    def write_text(self, layer: str, filename: str, content: str) -> None:
        path = self._path(layer, filename)
        path.write_text(content, encoding="utf-8")

    # ── Leitura ───────────────────────────────────────────────────────────────

    def read(self, layer: str, filename: str) -> pd.DataFrame:
        """Lê qualquer formato detectando pela extensão."""
        return _read_file(self._path(layer, filename))

    def read_path(self, layer: str, filename: str) -> Path:
        return self._path(layer, filename)

    # ── Movimentação e promoção ───────────────────────────────────────────────

    def move(self, filename: str, from_layer: str, to_layer: str) -> None:
        """Move o arquivo sem conversão — usado para Quarantine (DLQ)."""
        src = self._path(from_layer, filename)
        dst = self._path(to_layer, filename)
        if dst.exists():
            dst.unlink()
        shutil.move(str(src), str(dst))
        print("   [MOVE] {}: {} -> {}".format(
            filename, from_layer.upper(), to_layer.upper()
        ))

    def promote_to_parquet(
        self, filename: str, from_layer: str, to_layer: str
    ) -> str:
        """
        Lê o arquivo em from_layer, converte para Parquet e grava em to_layer.
        Remove o arquivo original após a conversão bem-sucedida.

        Usado pelo profiler para promover Bronze → Silver em Parquet.

        Args:
            filename   : Nome do arquivo na camada de origem.
            from_layer : Camada de origem (normalmente 'bronze').
            to_layer   : Camada de destino (normalmente 'silver').

        Returns:
            Nome do arquivo Parquet gravado no destino (ex: 'tb_clientes.parquet').
        """
        src = self._path(from_layer, filename)
        df  = _read_file(src)

        parquet_filename = self.write_parquet(to_layer, filename, df)

        # Bronze preserva o arquivo original para rastreabilidade —
        # apenas move para um subdiretório _archive/ dentro da própria camada.
        archive_dir = src.parent / "_archive"
        archive_dir.mkdir(exist_ok=True)
        archived = archive_dir / src.name
        if archived.exists():
            archived.unlink()
        shutil.move(str(src), str(archived))

        # Arquiva sidecar .layout junto se existir (fixed-width)
        sidecar = src.parent / (src.name + ".layout")
        if sidecar.exists():
            shutil.move(str(sidecar), str(archive_dir / sidecar.name))

        print("   [PROMOTE] {} -> {}/{} (Parquet, snappy) | original arquivado em {}/{}".format(
            filename, to_layer.upper(), parquet_filename,
            from_layer, "_archive/" + filename
        ))
        return parquet_filename

    # ── Listagem ──────────────────────────────────────────────────────────────

    def list(self, layer: str) -> list:
        """Lista todos os arquivos de dados (CSV e Parquet) de uma camada."""
        extensions = {".csv", ".parquet", ".json", ".jsonl", ".txt", ".dat"}
        return [
            f.name for f in self._layers[layer].iterdir()
            if f.suffix.lower() in extensions
        ]

    def exists(self, layer: str, filename: str) -> bool:
        return self._path(layer, filename).exists()


# ─────────────────────────────────────────────────────────────────────────────
# Backend MinIO
# ─────────────────────────────────────────────────────────────────────────────

class MinIOStorage(StorageBase):
    """
    Backend MinIO/S3 — requer docker-compose up -d e pip install minio.

    Mesma estratégia de formato do LocalStorage:
        Bronze / Quarantine → CSV (formato original)
        Silver / Gold       → Parquet (via promote_to_parquet)
    """

    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        layer_map: dict,
        tmp_dir: Path,
    ):
        try:
            from minio import Minio
            from minio.error import S3Error
            self._S3Error = S3Error
        except ImportError:
            raise ImportError(
                "MinIO nao instalado. Execute: pip install minio\n"
                "Ou use USE_MINIO=False em config.py para rodar com disco local."
            )

        from minio import Minio
        self._client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=False)
        self._layers = layer_map
        self._tmp    = tmp_dir
        self._tmp.mkdir(parents=True, exist_ok=True)
        self._ensure_buckets()

    def _ensure_buckets(self) -> None:
        for bucket in self._layers.values():
            if not self._client.bucket_exists(bucket):
                self._client.make_bucket(bucket)

    def _bucket(self, layer: str) -> str:
        if layer not in self._layers:
            raise ValueError("Camada desconhecida: '{}'".format(layer))
        return self._layers[layer]

    def write(self, layer: str, filename: str, df: pd.DataFrame) -> None:
        buf = io.BytesIO(df.to_csv(index=False, lineterminator="\n").encode("utf-8"))
        self._client.put_object(
            self._bucket(layer), filename, buf,
            length=buf.getbuffer().nbytes, content_type="text/csv"
        )
        print("   [WRITE] [{}] {} -> MinIO ({} linhas)".format(
            layer.upper(), filename, len(df)
        ))

    def write_parquet(self, layer: str, filename: str, df: pd.DataFrame) -> str:
        parquet_filename = _parquet_name(filename)
        tmp_path         = self._tmp / parquet_filename
        df.to_parquet(tmp_path, index=False, engine="pyarrow", compression="snappy")
        with open(tmp_path, "rb") as f:
            data = f.read()
        buf = io.BytesIO(data)
        self._client.put_object(
            self._bucket(layer), parquet_filename, buf,
            length=len(data), content_type="application/octet-stream"
        )
        size_kb = len(data) / 1024
        print("   [PARQUET] [{}] {} -> MinIO ({} linhas, {:.1f} KB)".format(
            layer.upper(), parquet_filename, len(df), size_kb
        ))
        return parquet_filename

    def write_text(self, layer: str, filename: str, content: str) -> None:
        buf = io.BytesIO(content.encode("utf-8"))
        self._client.put_object(
            self._bucket(layer), filename, buf,
            length=buf.getbuffer().nbytes, content_type="text/plain"
        )

    def read(self, layer: str, filename: str) -> pd.DataFrame:
        ext = Path(filename).suffix.lower()
        if ext == ".parquet":
            tmp_path = self._tmp / filename
            self._client.fget_object(self._bucket(layer), filename, str(tmp_path))
            return pd.read_parquet(tmp_path)
        response = self._client.get_object(self._bucket(layer), filename)
        return pd.read_csv(io.BytesIO(response.read()), low_memory=False, dtype=str)

    def read_path(self, layer: str, filename: str) -> Path:
        tmp_path = self._tmp / filename
        self._client.fget_object(self._bucket(layer), filename, str(tmp_path))
        return tmp_path

    def move(self, filename: str, from_layer: str, to_layer: str) -> None:
        from minio.commonconfig import CopySource
        src_bucket = self._bucket(from_layer)
        dst_bucket = self._bucket(to_layer)
        self._client.copy_object(dst_bucket, filename, CopySource(src_bucket, filename))
        self._client.remove_object(src_bucket, filename)
        print("   [MOVE] {}: {} -> {} (MinIO)".format(
            filename, from_layer.upper(), to_layer.upper()
        ))

    def promote_to_parquet(
        self, filename: str, from_layer: str, to_layer: str
    ) -> str:
        """Lê do MinIO, converte para Parquet e regrava no bucket de destino."""
        tmp_src = self._tmp / filename
        self._client.fget_object(self._bucket(from_layer), filename, str(tmp_src))
        df               = _read_file(tmp_src)
        parquet_filename = self.write_parquet(to_layer, filename, df)
        self._client.remove_object(self._bucket(from_layer), filename)
        print("   [PROMOTE] {} -> {}/{} (MinIO Parquet)".format(
            filename, to_layer.upper(), parquet_filename
        ))
        return parquet_filename

    def list(self, layer: str) -> list:
        objects = self._client.list_objects(self._bucket(layer))
        return [
            obj.object_name for obj in objects
            if obj.object_name.endswith((".csv", ".parquet", ".json"))
        ]

    def exists(self, layer: str, filename: str) -> bool:
        try:
            self._client.stat_object(self._bucket(layer), filename)
            return True
        except self._S3Error:
            return False


# ─────────────────────────────────────────────────────────────────────────────
# Factory
# ─────────────────────────────────────────────────────────────────────────────

def get_storage() -> StorageBase:
    """
    Retorna o backend correto conforme config.py.

    USE_MINIO = False -> LocalStorage (padrao, sem dependencias externas)
    USE_MINIO = True  -> MinIOStorage (requer docker-compose up -d)
    """
    import config as cfg

    LAYER_NAMES = ["bronze", "silver", "gold", "quarantine", "contracts", "metrics", "reports"]

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

    minio_map = {layer: "nimbus-{}".format(layer) for layer in LAYER_NAMES}
    return MinIOStorage(
        endpoint   = getattr(cfg, "MINIO_ENDPOINT",   "localhost:9000"),
        access_key = getattr(cfg, "MINIO_ACCESS_KEY", "minioadmin"),
        secret_key = getattr(cfg, "MINIO_SECRET_KEY", "minioadmin"),
        layer_map  = minio_map,
        tmp_dir    = cfg.DATA_DIR / "_tmp_minio",
    )
