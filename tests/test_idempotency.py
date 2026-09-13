"""
tests/test_idempotency.py - Testes para src/ingestion/idempotency.py

Cobre a identidade da carga (dat_ref), o SHA-256 do arquivo de entrada e a
distincao entre reprocessar o mesmo arquivo e receber um arquivo diferente para
a mesma janela de dados - que e o caso em que --skip-existing nao pode pular.
"""

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.ingestion.idempotency import (FIRST_LOAD, LEDGER_NAME,
                                       REPROCESS_IDENTICAL,
                                       REPROCESS_MODIFIED, announce,
                                       classify_load, file_sha256, load_ledger,
                                       previous_load, record_load,
                                       resolve_dat_ref, short_sha)
from src.storage.storage import LocalStorage

_LAYERS = ["bronze", "silver", "gold", "quarantine", "contracts", "metrics", "reports"]


def make_storage(base: Path) -> LocalStorage:
    return LocalStorage({l: base / l for l in _LAYERS})


class TestResolveDatRef(unittest.TestCase):

    def test_cli_tem_precedencia(self):
        self.assertEqual(resolve_dat_ref("run_20240101_000000_abc", "2023-12-31"),
                         "2023-12-31")

    def test_deriva_do_run_id_quando_nao_informada(self):
        self.assertEqual(resolve_dat_ref("run_20240115_101112_abc"), "2024-01-15")

    def test_formato_invalido_e_recusado(self):
        with self.assertRaises(ValueError):
            resolve_dat_ref("run_20240115_101112_abc", "15/01/2024")


class TestFileSha256(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def test_hash_confere_com_hashlib(self):
        p = self.tmp / "entrada.csv"
        p.write_bytes(b"id,nome\n1,Ana\n")
        self.assertEqual(file_sha256(p),
                         hashlib.sha256(b"id,nome\n1,Ana\n").hexdigest())

    def test_arquivo_maior_que_um_bloco(self):
        """Leitura em blocos nao pode alterar o hash de arquivo grande."""
        conteudo = b"x" * (3 * 1024 * 1024 + 7)
        p = self.tmp / "grande.bin"
        p.write_bytes(conteudo)
        self.assertEqual(file_sha256(p), hashlib.sha256(conteudo).hexdigest())

    def test_conteudo_diferente_muda_o_hash(self):
        a, b = self.tmp / "a.csv", self.tmp / "b.csv"
        a.write_bytes(b"1")
        b.write_bytes(b"2")
        self.assertNotEqual(file_sha256(a), file_sha256(b))

    def test_arquivo_inexistente_devolve_none(self):
        self.assertIsNone(file_sha256(self.tmp / "nao_existe.csv"))

    def test_diretorio_devolve_none(self):
        self.assertIsNone(file_sha256(self.tmp))

    def test_caminho_vazio_devolve_none(self):
        self.assertIsNone(file_sha256(None))
        self.assertIsNone(file_sha256(""))


class TestShortSha(unittest.TestCase):

    def test_prefixo_de_doze_caracteres(self):
        self.assertEqual(short_sha("a" * 64), "a" * 12)

    def test_none_nao_quebra_o_log(self):
        self.assertEqual(short_sha(None), "-")


class TestClassifyLoad(unittest.TestCase):

    def test_sem_carga_anterior_e_primeira_carga(self):
        self.assertEqual(classify_load(None, "abc"), FIRST_LOAD)
        self.assertEqual(classify_load({}, "abc"), FIRST_LOAD)

    def test_mesmo_hash_e_reprocessamento_identico(self):
        self.assertEqual(classify_load({"input_sha256": "abc"}, "abc"),
                         REPROCESS_IDENTICAL)

    def test_hash_diferente_e_reprocessamento_modificado(self):
        self.assertEqual(classify_load({"input_sha256": "abc"}, "def"),
                         REPROCESS_MODIFIED)

    def test_carga_antiga_sem_hash_nao_acusa_divergencia(self):
        """Compatibilidade retroativa: sem hash gravado, nao se afirma que mudou."""
        self.assertEqual(classify_load({"run_id": "run_x"}, "abc"),
                         REPROCESS_IDENTICAL)

    def test_hash_atual_ausente_nao_acusa_divergencia(self):
        self.assertEqual(classify_load({"input_sha256": "abc"}, None),
                         REPROCESS_IDENTICAL)


class TestLedger(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.s   = make_storage(self.tmp)

    def test_ledger_inexistente_e_dict_vazio(self):
        self.assertEqual(load_ledger(self.s), {})

    def test_ledger_corrompido_nao_interrompe_a_carga(self):
        self.s.write_text("metrics", LEDGER_NAME, "{ isso nao e json")
        self.assertEqual(load_ledger(self.s), {})

    def test_primeira_carga_grava_hash_e_situacao(self):
        entry = record_load(self.s, "tb_clientes", "2024-04-01", "csv",
                            "run_1", "PASS", rows=500,
                            input_sha="a" * 64, input_file="tb_clientes.csv")
        self.assertEqual(entry["input_situation"], FIRST_LOAD)
        self.assertEqual(entry["input_sha256"], "a" * 64)
        self.assertEqual(entry["input_file"], "tb_clientes.csv")
        self.assertEqual(entry["reprocess_count"], 0)
        self.assertNotIn("previous_sha256", entry)

    def test_ledger_persiste_em_json_na_camada_de_metricas(self):
        record_load(self.s, "tb_clientes", "2024-04-01", "csv", "run_1", "PASS",
                    input_sha="a" * 64)
        raw = json.loads((self.tmp / "metrics" / LEDGER_NAME).read_text(encoding="utf-8"))
        self.assertIn("tb_clientes|2024-04-01|csv", raw)

    def test_chave_e_tabela_dat_ref_formato(self):
        record_load(self.s, "tb_clientes", "2024-04-01", "csv", "run_1", "PASS",
                    input_sha="a" * 64)
        record_load(self.s, "tb_clientes", "2024-04-01", "json", "run_1", "PASS",
                    input_sha="b" * 64)
        self.assertEqual(len(load_ledger(self.s)), 2)

    def test_reprocessamento_identico_incrementa_contador(self):
        record_load(self.s, "tb_clientes", "2024-04-01", "csv", "run_1", "PASS",
                    input_sha="a" * 64)
        entry = record_load(self.s, "tb_clientes", "2024-04-01", "csv", "run_2",
                            "PASS", input_sha="a" * 64)
        self.assertEqual(entry["input_situation"], REPROCESS_IDENTICAL)
        self.assertEqual(entry["reprocess_count"], 1)
        self.assertNotIn("previous_sha256", entry)

    def test_arquivo_modificado_preserva_o_hash_anterior(self):
        record_load(self.s, "tb_clientes", "2024-04-01", "csv", "run_1", "PASS",
                    input_sha="a" * 64)
        entry = record_load(self.s, "tb_clientes", "2024-04-01", "csv", "run_2",
                            "PASS", input_sha="b" * 64)
        self.assertEqual(entry["input_situation"], REPROCESS_MODIFIED)
        self.assertEqual(entry["previous_sha256"], "a" * 64)
        self.assertEqual(entry["input_sha256"], "b" * 64)

    def test_previous_load_devolve_none_para_chave_desconhecida(self):
        self.assertIsNone(previous_load(self.s, "tb_x", "2024-04-01", "csv"))

    def test_carga_sem_hash_herda_o_hash_registrado(self):
        """Uma run sem hash disponivel nao pode apagar o hash ja auditado."""
        record_load(self.s, "tb_clientes", "2024-04-01", "csv", "run_1", "PASS",
                    input_sha="a" * 64, input_file="tb_clientes.csv")
        entry = record_load(self.s, "tb_clientes", "2024-04-01", "csv", "run_2",
                            "PASS", input_sha=None)
        self.assertEqual(entry["input_sha256"], "a" * 64)
        self.assertEqual(entry["input_file"], "tb_clientes.csv")


class TestAnnounce(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.s   = make_storage(self.tmp)

    def _primeira_carga(self, sha="a" * 64, status="PASS"):
        record_load(self.s, "tb_clientes", "2024-04-01", "csv", "run_1", status,
                    input_sha=sha, input_file="tb_clientes.csv")

    def test_primeira_carga_nao_pula(self):
        self.assertFalse(announce(self.s, "tb_clientes", "2024-04-01", "csv",
                                  skip_existing=True, input_sha="a" * 64))

    def test_reprocessamento_identico_sem_skip_nao_pula(self):
        self._primeira_carga()
        self.assertFalse(announce(self.s, "tb_clientes", "2024-04-01", "csv",
                                  input_sha="a" * 64))

    def test_skip_existing_pula_carga_identica_concluida(self):
        self._primeira_carga()
        self.assertTrue(announce(self.s, "tb_clientes", "2024-04-01", "csv",
                                 skip_existing=True, input_sha="a" * 64))

    def test_skip_existing_pula_carga_com_warning(self):
        self._primeira_carga(status="WARNING")
        self.assertTrue(announce(self.s, "tb_clientes", "2024-04-01", "csv",
                                 skip_existing=True, input_sha="a" * 64))

    def test_skip_existing_nao_pula_carga_bloqueada(self):
        """BLOCKED nao e carga concluida - tem que ser reprocessada."""
        self._primeira_carga(status="BLOCKED")
        self.assertFalse(announce(self.s, "tb_clientes", "2024-04-01", "csv",
                                  skip_existing=True, input_sha="a" * 64))

    def test_arquivo_modificado_nunca_e_pulado(self):
        self._primeira_carga()
        self.assertFalse(announce(self.s, "tb_clientes", "2024-04-01", "csv",
                                  skip_existing=True, input_sha="b" * 64))

    def test_outra_dat_ref_e_carga_nova(self):
        self._primeira_carga()
        self.assertFalse(announce(self.s, "tb_clientes", "2024-05-01", "csv",
                                  skip_existing=True, input_sha="a" * 64))

    def test_outro_formato_e_carga_nova(self):
        self._primeira_carga()
        self.assertFalse(announce(self.s, "tb_clientes", "2024-04-01", "json",
                                  skip_existing=True, input_sha="a" * 64))


class TestCicloCompleto(unittest.TestCase):
    """Sequencia real: primeira carga -> mesma entrada -> entrada divergente."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.s   = make_storage(self.tmp)

    def test_tres_situacoes_em_sequencia(self):
        self.s.write_text("bronze", "tb.csv", "id,nome\n1,Ana\n")
        sha1 = file_sha256(self.s.read_path("bronze", "tb.csv"))

        self.assertFalse(announce(self.s, "tb", "2024-04-01", "csv",
                                  skip_existing=True, input_sha=sha1))
        e1 = record_load(self.s, "tb", "2024-04-01", "csv", "run_1", "PASS",
                         rows=1, input_sha=sha1, input_file="tb.csv")
        self.assertEqual(e1["input_situation"], FIRST_LOAD)

        self.assertTrue(announce(self.s, "tb", "2024-04-01", "csv",
                                 skip_existing=True, input_sha=sha1))

        self.s.write_text("bronze", "tb.csv", "id,nome\n1,Ana\n2,Bruno\n")
        sha2 = file_sha256(self.s.read_path("bronze", "tb.csv"))
        self.assertNotEqual(sha1, sha2)

        self.assertFalse(announce(self.s, "tb", "2024-04-01", "csv",
                                  skip_existing=True, input_sha=sha2))
        e2 = record_load(self.s, "tb", "2024-04-01", "csv", "run_2", "PASS",
                         rows=2, input_sha=sha2, input_file="tb.csv")
        self.assertEqual(e2["input_situation"], REPROCESS_MODIFIED)
        self.assertEqual(e2["previous_sha256"], sha1)


if __name__ == "__main__":
    unittest.main()
