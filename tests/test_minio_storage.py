"""
tests/test_minio_storage.py - Testes para MinIOStorage e get_storage().

Nao sobem servidor: o cliente `minio` e substituido por um duplo em memoria,
de modo que o que se testa e o contrato da classe (bucket por camada, criacao
condicional de bucket, prefixo, TLS, regiao, arquivamento, listagem) e nao a
implementacao do servidor S3.
"""

import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))
import src.storage.storage as storage_mod
from src.storage.storage import LocalStorage, MinIOStorage, get_storage

_LAYERS = ["bronze", "silver", "gold", "quarantine", "contracts", "metrics", "reports"]


class FakeS3Error(Exception):
    pass


class FakeObject:
    def __init__(self, object_name):
        self.object_name = object_name


class FakeCopySource:
    def __init__(self, bucket, name):
        self.bucket, self.name = bucket, name


class FakeMinio:
    """Duplo em memoria: objetos guardados em {bucket: {nome: bytes}}."""

    last_init = None

    def __init__(self, endpoint, access_key=None, secret_key=None,
                 secure=False, region=None):
        FakeMinio.last_init = {"endpoint": endpoint, "access_key": access_key,
                               "secret_key": secret_key, "secure": secure,
                               "region": region}
        self.objects = {}
        self.made_buckets = []
        self.existing_buckets = set(FakeMinio.preexisting)

    preexisting = ()

    def bucket_exists(self, bucket):
        return bucket in self.existing_buckets

    def make_bucket(self, bucket):
        self.existing_buckets.add(bucket)
        self.made_buckets.append(bucket)
        self.objects.setdefault(bucket, {})

    def put_object(self, bucket, name, data, length=None, content_type=None):
        self.objects.setdefault(bucket, {})[name] = data.read()

    def stat_object(self, bucket, name):
        if name not in self.objects.get(bucket, {}):
            raise FakeS3Error(name)
        return FakeObject(name)

    def fget_object(self, bucket, name, destino):
        if name not in self.objects.get(bucket, {}):
            raise FakeS3Error(name)
        Path(destino).parent.mkdir(parents=True, exist_ok=True)
        Path(destino).write_bytes(self.objects[bucket][name])

    def copy_object(self, bucket, name, source):
        self.objects.setdefault(bucket, {})[name] = \
            self.objects[source.bucket][source.name]

    def remove_object(self, bucket, name):
        self.objects.get(bucket, {}).pop(name, None)

    def list_objects(self, bucket, **kwargs):
        return [FakeObject(n) for n in sorted(self.objects.get(bucket, {}))]


def install_fake_minio(test, preexisting=()):
    """Injeta o duplo nos imports locais de MinIOStorage e devolve o tmp_dir."""
    FakeMinio.preexisting = tuple(preexisting)
    fake_minio_mod = type(sys)("minio")
    fake_minio_mod.Minio = FakeMinio
    fake_error_mod = type(sys)("minio.error")
    fake_error_mod.S3Error = FakeS3Error
    fake_common_mod = type(sys)("minio.commonconfig")
    fake_common_mod.CopySource = FakeCopySource

    patcher = patch.dict(sys.modules, {"minio": fake_minio_mod,
                                       "minio.error": fake_error_mod,
                                       "minio.commonconfig": fake_common_mod})
    patcher.start()
    test.addCleanup(patcher.stop)
    return Path(tempfile.mkdtemp())


def make_minio_storage(test, prefix="nimbus", preexisting=None, **kwargs):
    layer_map = {l: "{}-{}".format(prefix, l) for l in _LAYERS}
    if preexisting is None:
        preexisting = tuple(layer_map.values())
    tmp = install_fake_minio(test, preexisting)
    return MinIOStorage("localhost:9000", "ak", "sk", layer_map,
                        tmp / "_tmp", **kwargs)


SAMPLE = pd.DataFrame({"id": ["A1", "A2"], "nome": ["Ana", "Bruno"]})


class TestBuckets(unittest.TestCase):

    def test_uma_bucket_por_camada(self):
        s = make_minio_storage(self)
        self.assertEqual(s._bucket("bronze"), "nimbus-bronze")
        self.assertEqual(s._bucket("quarantine"), "nimbus-quarantine")

    def test_camada_desconhecida_e_recusada(self):
        s = make_minio_storage(self)
        with self.assertRaises(ValueError):
            s._bucket("platinum")

    def test_prefixo_customizado_muda_todas_as_buckets(self):
        s = make_minio_storage(self, prefix="nimbus-tls2")
        self.assertEqual(s._bucket("silver"), "nimbus-tls2-silver")

    def test_bucket_inexistente_e_criada_por_padrao(self):
        s = make_minio_storage(self, preexisting=())
        self.assertEqual(len(s._client.made_buckets), len(_LAYERS))

    def test_create_buckets_false_recusa_bucket_inexistente(self):
        """Em conta gerenciada o pipeline nao pode criar bucket sozinho."""
        with self.assertRaises(RuntimeError):
            make_minio_storage(self, preexisting=(), create_buckets=False)

    def test_create_buckets_false_aceita_bucket_existente(self):
        s = make_minio_storage(self, create_buckets=False)
        self.assertEqual(s._client.made_buckets, [])


class TestParametrosDeConexao(unittest.TestCase):

    def test_tls_e_regiao_chegam_ao_cliente(self):
        make_minio_storage(self, secure=True, region="us-east-1")
        self.assertTrue(FakeMinio.last_init["secure"])
        self.assertEqual(FakeMinio.last_init["region"], "us-east-1")

    def test_default_e_sem_tls_e_sem_regiao(self):
        make_minio_storage(self)
        self.assertFalse(FakeMinio.last_init["secure"])
        self.assertIsNone(FakeMinio.last_init["region"])


class TestLeituraEEscrita(unittest.TestCase):

    def setUp(self):
        self.s = make_minio_storage(self)

    def test_write_text_e_read_path(self):
        self.s.write_text("contracts", "tb.yaml", "version: 1.0.0\n")
        destino = self.s.read_path("contracts", "tb.yaml")
        self.assertEqual(Path(destino).read_text(encoding="utf-8"), "version: 1.0.0\n")

    def test_write_dataframe_vira_csv_na_bucket(self):
        self.s.write("bronze", "tb.csv", SAMPLE)
        conteudo = self.s._client.objects["nimbus-bronze"]["tb.csv"].decode("utf-8")
        self.assertTrue(conteudo.startswith("id,nome"))

    def test_read_devolve_dataframe(self):
        self.s.write("bronze", "tb.csv", SAMPLE)
        df = self.s.read("bronze", "tb.csv")
        self.assertEqual(len(df), 2)
        self.assertEqual(list(df.columns), ["id", "nome"])

    def test_exists_true_e_false(self):
        self.s.write("bronze", "tb.csv", SAMPLE)
        self.assertTrue(self.s.exists("bronze", "tb.csv"))
        self.assertFalse(self.s.exists("bronze", "outra.csv"))

    def test_list_filtra_por_extensao_de_dados(self):
        self.s.write("bronze", "tb.csv", SAMPLE)
        self.s.write_text("bronze", "tb.csv.layout", "id 1 2\n")
        self.assertEqual(self.s.list("bronze"), ["tb.csv"])

    def test_write_parquet_devolve_nome_parquet(self):
        nome = self.s.write_parquet("silver", "tb.csv", SAMPLE)
        self.assertEqual(nome, "tb.parquet")
        self.assertIn("tb.parquet", self.s._client.objects["nimbus-silver"])


class TestMovimentacao(unittest.TestCase):

    def setUp(self):
        self.s = make_minio_storage(self)

    def test_move_troca_de_bucket(self):
        self.s.write("bronze", "tb.csv", SAMPLE)
        self.s.move("tb.csv", "bronze", "quarantine")
        self.assertFalse(self.s.exists("bronze", "tb.csv"))
        self.assertTrue(self.s.exists("quarantine", "tb.csv"))

    def test_promote_gera_parquet_e_arquiva_o_original(self):
        self.s.write("bronze", "tb.csv", SAMPLE)
        nome = self.s.promote_to_parquet("tb.csv", "bronze", "silver",
                                         run_id="run_1", dat_ref="2024-04-01")
        self.assertEqual(nome, "tb.parquet")
        self.assertTrue(self.s.exists("silver", "tb.parquet"))
        self.assertFalse(self.s.exists("bronze", "tb.csv"))
        self.assertIn("_archive/tb.csv", self.s._client.objects["nimbus-bronze"])

    def test_promote_grava_colunas_de_linhagem(self):
        self.s.write("bronze", "tb.csv", SAMPLE)
        self.s.promote_to_parquet("tb.csv", "bronze", "silver",
                                  run_id="run_1", dat_ref="2024-04-01")
        destino = self.s.read_path("silver", "tb.parquet")
        df = pd.read_parquet(destino)
        self.assertEqual(df["_ingest_run_id"].iloc[0], "run_1")
        self.assertEqual(df["_ingest_dat_ref"].iloc[0], "2024-04-01")


class TestGetStorage(unittest.TestCase):

    def test_use_minio_false_devolve_local(self):
        import config as cfg
        with patch.object(cfg, "USE_MINIO", False):
            self.assertIsInstance(get_storage(), LocalStorage)

    def test_use_minio_true_devolve_minio_com_as_variaveis(self):
        import config as cfg
        install_fake_minio(self, preexisting=[
            "acme-{}".format(l) for l in _LAYERS])
        with patch.object(cfg, "USE_MINIO", True), \
             patch.object(cfg, "MINIO_ENDPOINT", "s3.exemplo.com"), \
             patch.object(cfg, "MINIO_ACCESS_KEY", "chave"), \
             patch.object(cfg, "MINIO_SECRET_KEY", "segredo"), \
             patch.object(cfg, "MINIO_SECURE", True), \
             patch.object(cfg, "MINIO_REGION", "sa-east-1"), \
             patch.object(cfg, "BUCKET_PREFIX", "acme"), \
             patch.object(cfg, "MINIO_CREATE_BUCKETS", False):
            s = get_storage()
        self.assertIsInstance(s, MinIOStorage)
        self.assertEqual(s._bucket("bronze"), "acme-bronze")
        self.assertEqual(FakeMinio.last_init["endpoint"], "s3.exemplo.com")
        self.assertTrue(FakeMinio.last_init["secure"])
        self.assertEqual(FakeMinio.last_init["region"], "sa-east-1")
        self.assertEqual(FakeMinio.last_init["access_key"], "chave")

    def test_use_minio_true_sem_credencial_falha_explicito(self):
        import config as cfg
        install_fake_minio(self)
        for chave, segredo in (("", ""), ("chave", ""), ("", "segredo")):
            with self.subTest(access_key=chave, secret_key=segredo):
                with patch.object(cfg, "USE_MINIO", True), \
                     patch.object(cfg, "MINIO_ACCESS_KEY", chave), \
                     patch.object(cfg, "MINIO_SECRET_KEY", segredo):
                    with self.assertRaises(RuntimeError) as ctx:
                        get_storage()
                self.assertIn("MINIO_ACCESS_KEY", str(ctx.exception))

    def test_local_e_minio_expoem_a_mesma_interface(self):
        metodos = ["write", "write_text", "write_parquet", "read", "read_path",
                   "move", "promote_to_parquet", "list", "exists"]
        for nome in metodos:
            with self.subTest(metodo=nome):
                self.assertTrue(hasattr(LocalStorage, nome))
                self.assertTrue(hasattr(MinIOStorage, nome))


if __name__ == "__main__":
    unittest.main()
