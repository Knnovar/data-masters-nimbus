import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.generators.data_generator import (
    seed_all,
    _uuid4,
    _cpf,
    _nome,
    _cnpj,
    _random_date,
    _inject_nulls,
    _gerar_clientes,
    _contrato_clientes,
    _gerar_transacoes,
    _gerar_contratos_credito,
    _contrato_transacoes,
    _contrato_contratos_credito,
    generate_all
)
from src.ingestion.idempotency import file_sha256

LAYERS = ["bronze", "silver", "gold", "quarantine", "contracts", "metrics", "reports"]


def _storage():
    from src.storage.storage import LocalStorage
    tmp = Path(tempfile.mkdtemp())
    return LocalStorage({layer: tmp / layer for layer in LAYERS})


class TestDataGeneratorHelpers(unittest.TestCase):

    def test_cpf_tem_11_digitos(self):
        cpf = _cpf()
        self.assertTrue(cpf.isdigit())
        self.assertEqual(len(cpf), 11)

    def test_nome_nao_vazio(self):
        self.assertTrue(_nome().strip())

    def test_cnpj_tem_14_digitos(self):
        cnpj = _cnpj()
        self.assertTrue(cnpj.isdigit())
        self.assertEqual(len(cnpj), 14)

    def test_cnpj_fallback_sem_faker(self):
        with patch("src.generators.data_generator.fake", None):
            self.assertEqual(len(_cnpj()), 14)

    def test_random_date_dentro_do_intervalo(self):
        start, end = datetime(2020, 1, 1), datetime(2020, 12, 31)
        parsed = pd.Timestamp(_random_date(start, end))
        self.assertGreaterEqual(parsed, pd.Timestamp(start))
        self.assertLessEqual(parsed, pd.Timestamp(end))

    def test_inject_nulls_preserva_valores_fora_da_mascara(self):
        series = pd.Series([1, 2, 3, 4, 5])
        with patch("numpy.random.random",
                   return_value=np.array([0.0, 0.9, 0.9, 0.9, 0.9])):
            result = _inject_nulls(series, 0.5)
        self.assertTrue(result.isnull().iloc[0])
        self.assertEqual(list(result.iloc[1:]), [2, 3, 4, 5])

class TestGerarClientes(unittest.TestCase):

    COLS = {"cd_cliente", "nr_cpf_cnpj", "nm_cliente", "dt_nascimento",
            "cd_segmento", "cd_agencia", "vl_renda_mensal", "fl_ativo",
            "dt_cadastro"}

    def test_baseline_schema_e_volume(self):
        df = _gerar_clientes(100, "baseline")
        self.assertEqual(len(df), 100)
        self.assertEqual(set(df.columns), self.COLS)

    def test_baseline_pk_sem_nulo(self):
        df = _gerar_clientes(100, "baseline")
        self.assertFalse(df["cd_cliente"].isnull().any())

    def test_baseline_injeta_nulo_em_renda(self):
        df = _gerar_clientes(500, "baseline")
        self.assertGreater(df["vl_renda_mensal"].isnull().sum(), 0)

    def test_baseline_injeta_agencia_invalida(self):
        df = _gerar_clientes(500, "baseline")
        self.assertTrue((df["cd_agencia"] == "AGENC-???").any())

    def test_segmento_dentro_do_dominio(self):
        df = _gerar_clientes(100, "baseline")
        dominio = {"VAREJO", "PRIME", "PRIVATE", "PJ_PEQUENO", "PJ_MEDIO"}
        self.assertTrue(set(df["cd_segmento"]).issubset(dominio))

    def test_non_breaking_adiciona_coluna_anulavel(self):
        df = _gerar_clientes(100, "non_breaking")
        self.assertIn("cd_gestor_relacionamento", df.columns)
        self.assertGreater(df["cd_gestor_relacionamento"].isnull().sum(), 0)

    def test_breaking_remove_coluna_obrigatoria(self):
        df = _gerar_clientes(100, "breaking")
        self.assertNotIn("cd_agencia", df.columns)

class TestGerarTransacoes(unittest.TestCase):

    def setUp(self):
        self.clientes = _gerar_clientes(50, "baseline")

    def test_injeta_duplicatas_intencionais(self):
        df = _gerar_transacoes(self.clientes, n=200)
        self.assertGreater(len(df), 200)
        self.assertGreater(df["id_transacao"].duplicated().sum(), 0)

    def test_fk_aponta_para_clientes(self):
        df = _gerar_transacoes(self.clientes, n=200)
        self.assertTrue(
            set(df["cd_cliente"].dropna()).issubset(set(self.clientes["cd_cliente"]))
            )

    def test_injeta_nulo_em_estabelecimento(self):
        df = _gerar_transacoes(self.clientes, n=300)
        self.assertGreater(df["cd_estabelecimento"].isnull().sum(), 0)

    def test_contratos_credito_fk_e_volume(self):
        df = _gerar_contratos_credito(self.clientes, n=120)
        self.assertEqual(len(df), 120)
        self.assertTrue(
            set(df["cd_cliente"].dropna()).issubset(set(self.clientes["cd_cliente"])))

class TestContratos(unittest.TestCase):

    def _assert_estrutura(self, contrato, table):
        self.assertIsInstance(contrato, dict)
        self.assertEqual(contrato["table"], table)
        self.assertIn("schema", contrato)
        self.assertTrue(contrato["schema"])
        self.assertIn("tolerance", contrato)

    def test_contrato_clientes_nos_tres_cenarios(self):
        for scenario in ("baseline", "non_breaking", "breaking"):
            with self.subTest(scenario=scenario):
                self._assert_estrutura(_contrato_clientes(scenario), "tb_clientes")

    def test_contrato_transacoes(self):
        self._assert_estrutura(_contrato_transacoes(), "tb_transacoes")

    def test_contrato_contratos_credito(self):
        self._assert_estrutura(_contrato_contratos_credito(), "tb_contratos_credito")

    def test_contrato_declara_as_colunas_do_dataframe(self):
        base = {c["name"] for c in _contrato_clientes("baseline")["schema"]}
        for scenario in ("non_breaking", "breaking"):
            with self.subTest(scenario=scenario):
                declared = {c["name"] for c in _contrato_clientes(scenario)["schema"]}
                self.assertEqual(declared, base)
        self.assertNotIn("cd_gestor_relacionamento", base)
        self.assertIn("cd_agencia", base)



class TestGenerateAll(unittest.TestCase):

    def test_gera_as_tres_tabelas(self):
        produced = generate_all(_storage(), scenario="baseline", fmt="csv")
        self.assertEqual(
            {p["table"] for p in produced},
            {"tb_clientes", "tb_transacoes", "tb_contratos_credito"},
        )

    def test_arquivos_e_contratos_persistidos(self):
        s = _storage()
        for p in generate_all(s, scenario="baseline", fmt="csv"):
            self.assertTrue(s.exists("bronze", p["filename"]))

    def test_formato_invalido_levanta(self):
        with self.assertRaises(ValueError):
            generate_all(_storage(), scenario="baseline", fmt="avro")

    def test_todos_os_formatos_nos_tres_cenarios(self):
        for scenario in ("baseline", "non_breaking", "breaking"):
            for fmt in ("csv", "json", "fixed"):
                with self.subTest(scenario=scenario, fmt=fmt):
                    s = _storage()
                    produced = generate_all(s, scenario=scenario, fmt=fmt)
                    self.assertEqual(len(produced), 3)

class TestGeracaoDeterministica(unittest.TestCase):
    """Sem isto a idempotencia nao e demonstravel: a mesma dat_ref tem que
    produzir o mesmo arquivo, byte a byte, e portanto o mesmo SHA-256."""

    def test_seed_all_devolve_a_mesma_semente_para_a_mesma_chave(self):
        self.assertEqual(seed_all("baseline", "csv", "2024-04-01"),
                         seed_all("baseline", "csv", "2024-04-01"))

    def test_chaves_diferentes_dao_sementes_diferentes(self):
        self.assertNotEqual(seed_all("baseline", "csv", "2024-04-01"),
                            seed_all("baseline", "csv", "2024-05-01"))
        self.assertNotEqual(seed_all("baseline", "csv", "2024-04-01"),
                            seed_all("type_drift", "csv", "2024-04-01"))

    def test_uuid_vem_do_random_semeado_e_nao_da_entropia_do_sistema(self):
        seed_all("baseline", "csv", "2024-04-01")
        primeiro = _uuid4()
        seed_all("baseline", "csv", "2024-04-01")
        self.assertEqual(_uuid4(), primeiro)

    def test_uuid_tem_formato_v4(self):
        seed_all("baseline", "csv", "2024-04-01")
        gerado = _uuid4()
        self.assertEqual(len(gerado), 36)
        self.assertEqual(gerado[14], "4")

    def _hashes(self, storage, produced):
        return {p["filename"]: file_sha256(storage.read_path("bronze", p["filename"]))
                for p in produced}

    def _gerar(self, **kwargs):
        s = _storage()
        produced = generate_all(s, **kwargs)
        return self._hashes(s, produced)

    def test_mesma_dat_ref_gera_o_mesmo_arquivo(self):
        a = self._gerar(scenario="baseline", fmt="csv", dat_ref="2024-04-01")
        b = self._gerar(scenario="baseline", fmt="csv", dat_ref="2024-04-01")
        self.assertEqual(a, b)

    def test_dat_ref_diferente_gera_arquivo_diferente(self):
        a = self._gerar(scenario="baseline", fmt="csv", dat_ref="2024-04-01")
        b = self._gerar(scenario="baseline", fmt="csv", dat_ref="2024-05-01")
        self.assertEqual(set(a), set(b))
        for nome in a:
            with self.subTest(arquivo=nome):
                self.assertNotEqual(a[nome], b[nome])

    def test_cenario_diferente_na_mesma_dat_ref_gera_arquivo_diferente(self):
        """E o que faz type_drift aparecer como ENTRADA DIVERGENTE no ledger."""
        a = self._gerar(scenario="baseline", fmt="csv", dat_ref="2024-04-01")
        b = self._gerar(scenario="type_drift", fmt="csv", dat_ref="2024-04-01")
        self.assertNotEqual(a["tb_clientes.csv"], b["tb_clientes.csv"])

    def test_determinismo_vale_para_json_e_fixo(self):
        for fmt in ("json", "fixed"):
            with self.subTest(fmt=fmt):
                a = self._gerar(scenario="baseline", fmt=fmt, dat_ref="2024-04-01")
                b = self._gerar(scenario="baseline", fmt=fmt, dat_ref="2024-04-01")
                self.assertEqual(a, b)

    def test_sem_dat_ref_a_geracao_nao_e_fixada(self):
        """Compatibilidade: sem dat_ref o gerador segue o comportamento antigo."""
        a = self._gerar(scenario="baseline", fmt="csv")
        b = self._gerar(scenario="baseline", fmt="csv")
        self.assertEqual(set(a), set(b))


if __name__ == "__main__":
    unittest.main()
