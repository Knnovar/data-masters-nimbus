"""
src/storage/storage.py — Camada de abstração de storage

Implementa o padrão de arquitetura medallion (Bronze → Silver → Gold)
com dois backends intercambiáveis:

  LocalStorage  → disco local (padrão, sem dependências externas)
  MinIOStorage  → MinIO/S3 (requer docker-compose up -d)

A escolha do backend é feita em config.py via USE_MINIO.
O restante do pipeline não sabe qual backend está em uso.

Mapeamento de camadas:
  bronze     → dado bruto recebido (landing)
  silver     → dado validado e processado
  gold       → dado agregado, pronto para consumo analítico
  quarantine → arquivos com breaking change (DLQ)

Uso:
    from src.storage.storage import get_storage
    storage = get_storage()

    storage.write("bronze", "tb_clientes.csv", df)
    df = storage.read("bronze", "tb_clientes.csv")
    storage.move("tb_clientes.csv", "bronze", "silver")
    files = storage.list("silver")
"""

import io
import shutil
from abc import ABC, abstractmethod
from pathlib import Path

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
    def read(self, layer: str, filename: str) -> pd.DataFrame:
        """Lê um arquivo da camada indicada e retorna um DataFrame."""

    @abstractmethod
    def move(self, filename: str, from_layer: str, to_layer: str) -> None:
        """Promove um arquivo entre camadas (ex: bronze → silver)."""

    @abstractmethod
    def list(self, layer: str) -> list[str]:
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
        Retorna um Path local para o arquivo — necessário para módulos
        que recebem Path diretamente (DuckDB, pandas read_csv).
        No MinIOStorage, faz download temporário para disco.
        """


# ─────────────────────────────────────────────────────────────────────────────
# Backend local
# ─────────────────────────────────────────────────────────────────────────────

class LocalStorage(StorageBase):
    """
    Backend de disco local.

    Cada camada vira um subdiretório de data/:
        bronze     → data/landing/
        silver     → data/processed/
        gold       → data/gold/
        quarantine → data/quarantine/
        contracts  → data/contracts/
        metrics    → data/metrics/
        reports    → data/reports/
    """

    def __init__(self, layer_map: dict[str, Path]):
        self._layers = layer_map
        for path in layer_map.values():
            path.mkdir(parents=True, exist_ok=True)

    def _path(self, layer: str, filename: str) -> Path:
        if layer not in self._layers:
            raise ValueError(f"Camada desconhecida: '{layer}'. Disponíveis: {list(self._layers)}")
        return self._layers[layer] / filename

    def write(self, layer: str, filename: str, df: pd.DataFrame) -> None:
        path = self._path(layer, filename)
        df.to_csv(path, index=False)
        print(f"   [WRITE] [{layer.upper()}] {filename} gravado ({len(df)} linhas)")

    def read(self, layer: str, filename: str) -> pd.DataFrame:
        path = self._path(layer, filename)
        return pd.read_csv(path, low_memory=False, dtype=str)

    def move(self, filename: str, from_layer: str, to_layer: str) -> None:
        src = self._path(from_layer, filename)
        dst = self._path(to_layer, filename)
        if dst.exists():
            dst.unlink()
        shutil.move(str(src), str(dst))
        print(f"   [MOVE] {filename}: {from_layer.upper()} -> {to_layer.upper()}")

    def list(self, layer: str) -> list[str]:
        return [f.name for f in self._layers[layer].glob("*.csv")]

    def exists(self, layer: str, filename: str) -> bool:
        return self._path(layer, filename).exists()

    def write_text(self, layer: str, filename: str, content: str) -> None:
        path = self._path(layer, filename)
        path.write_text(content, encoding="utf-8")

    def read_path(self, layer: str, filename: str) -> Path:
        return self._path(layer, filename)


# ─────────────────────────────────────────────────────────────────────────────
# Backend MinIO
# ─────────────────────────────────────────────────────────────────────────────

class MinIOStorage(StorageBase):
    """
    Backend MinIO/S3 — requer docker-compose up -d e pip install minio.

    Cada camada vira um bucket:
        bronze     → data-masters-bronze
        silver     → data-masters-silver
        gold       → data-masters-gold
        quarantine → data-masters-quarantine
        contracts  → data-masters-contracts
        metrics    → data-masters-metrics
        reports    → data-masters-reports

    Em produção Azure, troque o endpoint e credenciais por:
        endpoint   → <storage-account>.blob.core.windows.net
        access_key → via Azure Key Vault / dbutils.secrets
    """

    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        layer_map: dict[str, str],
        tmp_dir: Path,
    ):
        try:
            from minio import Minio
            from minio.error import S3Error
            self._S3Error = S3Error
        except ImportError:
            raise ImportError(
                "MinIO não instalado. Execute: pip install minio\n"
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
            raise ValueError(f"Camada desconhecida: '{layer}'")
        return self._layers[layer]

    def write(self, layer: str, filename: str, df: pd.DataFrame) -> None:
        buf = io.BytesIO(df.to_csv(index=False).encode("utf-8"))
        self._client.put_object(
            self._bucket(layer), filename, buf, length=buf.getbuffer().nbytes,
            content_type="text/csv"
        )
        print(f"   [WRITE] [{layer.upper()}] {filename} -> MinIO ({len(df)} linhas)")

    def read(self, layer: str, filename: str) -> pd.DataFrame:
        response = self._client.get_object(self._bucket(layer), filename)
        return pd.read_csv(io.BytesIO(response.read()), low_memory=False, dtype=str)

    def move(self, filename: str, from_layer: str, to_layer: str) -> None:
        from minio.commonconfig import CopySource
        src_bucket = self._bucket(from_layer)
        dst_bucket = self._bucket(to_layer)
        # CopySource obrigatório a partir do minio-py 7.x
        self._client.copy_object(dst_bucket, filename, CopySource(src_bucket, filename))
        self._client.remove_object(src_bucket, filename)
        print(f"   [MOVE] {filename}: {from_layer.upper()} -> {to_layer.upper()} (MinIO)")

    def list(self, layer: str) -> list[str]:
        objects = self._client.list_objects(self._bucket(layer))
        return [obj.object_name for obj in objects if obj.object_name.endswith(".csv")]

    def exists(self, layer: str, filename: str) -> bool:
        try:
            self._client.stat_object(self._bucket(layer), filename)
            return True
        except self._S3Error:
            return False

    def write_text(self, layer: str, filename: str, content: str) -> None:
        buf = io.BytesIO(content.encode("utf-8"))
        self._client.put_object(
            self._bucket(layer), filename, buf, length=buf.getbuffer().nbytes,
            content_type="text/plain"
        )

    def read_path(self, layer: str, filename: str) -> Path:
        """Faz download temporário para que DuckDB e pandas possam ler por path."""
        tmp_path = self._tmp / filename
        self._client.fget_object(self._bucket(layer), filename, str(tmp_path))
        return tmp_path


# ─────────────────────────────────────────────────────────────────────────────
# Factory — ponto de entrada único para o restante do código
# ─────────────────────────────────────────────────────────────────────────────

def get_storage() -> StorageBase:
    """
    Retorna o backend correto conforme config.py.

    USE_MINIO = False → LocalStorage (padrão, sem dependências externas)
    USE_MINIO = True  → MinIOStorage (requer docker-compose up -d)
    """
    import config as cfg

    # Camadas comuns a ambos os backends
    LAYER_NAMES = ["bronze", "silver", "gold", "quarantine", "contracts", "metrics", "reports"]

    if not getattr(cfg, "USE_MINIO", False):
        # Mapeia cada camada para um diretório local
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

    # MinIO
    minio_map = {layer: f"data-masters-{layer}" for layer in LAYER_NAMES}
    return MinIOStorage(
        endpoint   = getattr(cfg, "MINIO_ENDPOINT",   "localhost:9000"),
        access_key = getattr(cfg, "MINIO_ACCESS_KEY", "minioadmin"),
        secret_key = getattr(cfg, "MINIO_SECRET_KEY", "minioadmin"),
        layer_map  = minio_map,
        tmp_dir    = cfg.DATA_DIR / "_tmp_minio",
    )
