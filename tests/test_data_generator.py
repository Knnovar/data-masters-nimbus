"""
tests/test_data_generator.py — Testes para src/generators/data_generator.py

Cobre:
  - Funções auxiliares (_cpf, _nome, _cnpj, _random_date, _inject_nulls)
  - Geração de tabelas (_gerar_clientes, _gerar_transacoes, _gerar_agencias)
  - Cenários: baseline, non_breaking, breaking
  - Geração de contratos
  - Função principal _gerar_dados_completos
  - Validação de propriedades esperadas dos dados gerados
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.generators.data_generator import (
    _cpf,
    _nome,
    _cnpj,
    _random_date,
    _inject_nulls,
    _gerar_clientes,
    _contrato_clientes,
    _gerar_transacoes,
    _contrato_transacoes,
    _gerar_contratos_credito,
    _contrato_contratos_credito,
    _gerar_dados_completos,
    ScenarioType,
)


class TestDataGeneratorHelpers(unittest.TestCase):
    """Testes para funções auxiliares."""

    def test_cpf_generation(self):
        """Testa geração de CPF."""
        cpf = _cpf()
        self.assertIsInstance(cpf, str)
        self.assertEqual(len(cpf), 11)  # CPF tem 11 dígitos
        self.assertTrue(cpf.isdigit())  # Apenas dígitos

    def test_nome_generation(self):
        """Testa geração de nome."""
        nome = _nome()
        self.assertIsInstance(nome, str)
        self.assertGreater(len(nome), 0)  # Nome não vazio

    def test_cnpj_generation(self):
        """Testa geração de CNPJ."""
        cnpj = _cnpj()
        self.assertIsInstance(cnpj, str)
        self.assertEqual(len(cnpj), 14)  # CNPJ tem 14 dígitos
        self.assertTrue(cnpj.isdigit())  # Apenas dígitos

    def test_random_date(self):
        """Testa geração de data aleatória."""
        start = pd.Timestamp("2020-01-01")
        end = pd.Timestamp("2020-12-31")
        date_str = _random_date(start.to_pydatetime(), end.to_pydatetime())
        self.assertIsInstance(date_str, str)
        # Tenta converter para data para validar formato
        parsed_date = pd.Timestamp(date_str)
        self.assertGreaterEqual(parsed_date, start)
        self.assertLessEqual(parsed_date, end)

    def test_inject_nulls(self):
        """Testa injeção de nulos em séries."""
        series = pd.Series([1, 2, 3, 4, 5])
        # Com pct=0.0, nenhum nulo deve ser injetado
        result = _inject_nulls(series, 0.0)
        pd.testing.assert_series_equal(result, series)

        # Com pct=1.0, todos devem ser nulos (exceto pela aleatoriedade)
        # Testamos com semente fixa para reproducibilidade
        with patch('numpy.random.random', return_value=np.array([0.5, 0.5, 0.5, 0.5, 0.5])):
            result = _inject_nulls(series, 0.6)  # 0.5 < 0.6 -> todos viram nulos
            expected = pd.Series([None, None, None, None, None])
            pd.testing.assert_series_equal(result, expected)


class TestTableGeneration(unittest.TestCase):
    """Testes para geração de tabelas."""

    def setUp(self):
        """Configuração comum para os testes."""
        self.n_rows = 100  # Número pequeno para testes rápidos

    def test_gerar_clientes_baseline(self):
        """Testa geração de tabela de clientes no cenário baseline."""
        df = _gerar_clientes(n=self.n_rows, scenario="baseline")

        # Verifica shape
        self.assertEqual(df.shape[0], self.n_rows)
        self.assertGreater(df.shape[1], 0)

        # Verifica colunas esperadas
        expected_columns = {
            "cd_cliente", "nr_cpf_cnpj", "nm_cliente", "dt_nascimento",
            "cd_segmento", "cd_agencia", "vl_renda_mensal", "fl_ativo", "dt_cadastro"
        }
        self.assertEqual(set(df.columns), expected_columns)

        # Verifica tipos de dados
        self.assertTrue(df["cd_cliente"].dtype == object)  # string
        self.assertTrue(df["nr_cpf_cnpj"].dtype == object)  # string
        self.assertTrue(df["nm_cliente"].dtype == object)  # string
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(df["dt_nascimento"]) or
                       df["dt_nascimento"].dtype == object)  # date ou string

        # Verifica que não há nulos em campos obrigatórios (exceto vl_renda_mensal que tem 18% de nulos intencional)
        self.assertFalse(df["cd_cliente"].isnull().any())
        self.assertFalse(df["nr_cpf_cnpj"].isnull().any())
        self.assertFalse(df["nm_cliente"].isnull().any())
        self.assertFalse(df["dt_nascimento"].isnull().any())
        self.assertFalse(df["cd_segmento"].isnull().any())
        self.assertFalse(df["cd_agencia"].isnull().any())
        self.assertFalse(df["fl_ativo"].isnull().any())
        self.assertFalse(df["dt_cadastro"].isnull().any())

        # Verifica que vl_renda_mensal tem aproximadamente 18% de nulos (conforme especificação)
        null_pct = df["vl_renda_mensal"].isnull().mean()
        self.assertAlmostEqual(null_pct, 0.18, delta=0.05)  # Tolerância de 5%

        # Verifica valores de segmento
        valid_segmentos = {"VAREJO", "PRIME", "PRIVATE", "PJ_PEQUENO", "PJ_MEDIO"}
        self.assertTrue(set(df["cd_segmento"].dropna().unique()).issubset(valid_segmentos))

        # Verifica que fl_ativo é booleano
        self.assertTrue(set(df["fl_ativo"].dropna().unique()).issubset({True, False}))

    def test_gerar_clientes_non_breaking(self):
        """Testa geração de tabela de clientes no cenário non_breaking."""
        df = _gerar_clientes(n=self.n_rows, scenario="non_breaking")

        # Deve ter uma coluna adicional: cd_gestor_relacionamento
        expected_columns = {
            "cd_cliente", "nr_cpf_cnpj", "nm_cliente", "dt_nascimento",
            "cd_segmento", "cd_agencia", "vl_renda_mensal", "fl_ativo", "dt_cadastro",
            "cd_gestor_relacionamento"
        }
        self.assertEqual(set(df.columns), expected_columns)

        # A nova coluna deve existir e ter aproximadamente 60% de nulos (conforme código)
        null_pct = df["cd_gestor_relacionamento"].isnull().mean()
        self.assertAlmostEqual(null_pct, 0.60, delta=0.05)  # Tolerância de 5%

    def test_gerar_clientes_breaking(self):
        """Testa geração de tabela de clientes no cenário breaking."""
        df = _gerar_clientes(n=self.n_rows, scenario="breaking")

        # NÃO deve ter a coluna cd_agencia (foi removida)
        expected_columns = {
            "cd_cliente", "nr_cpf_cnpj", "nm_cliente", "dt_nascimento",
            "cd_segmento", "vl_renda_mensal", "fl_ativo", "dt_cadastro"
        }
        self.assertEqual(set(df.columns), expected_columns)

        # Verifica que cd_agencia não está presente
        self.assertNotIn("cd_agencia", df.columns)

    def test_gerar_transacoes(self):
        """Testa geração de tabela de transações."""
        # Primeiro gera clientes para usar como referência
        clientes_df = _gerar_clientes(n=50, scenario="baseline")
        df = _gerar_transacoes(clientes_df=clientes_df, n=self.n_rows)

        # Verifica shape
        self.assertEqual(df.shape[0], self.n_rows)

        # Verifica colunas esperadas
        expected_columns = {
            "id_transacao", "cd_cliente", "vl_transacao", "dt_transacao",
            "tp_transacao", "nm_origem", "nm_destino"
        }
        self.assertEqual(set(df.columns), expected_columns)

        # Verifica que todos os cd_cliente existem na tabela de clientes
        self.assertTrue(set(df["cd_cliente"].dropna().unique()).issubset(set(clientes_df["cd_cliente"])))

        # Verifica tipos de transação válidos
        valid_tipos = {"COMPRA", "SAQUE", "TED", "PIX", "PAGAMENTO_BOLETO", "ESTORNO"}
        self.assertTrue(set(df["tp_transacao"].dropna().unique()).issubset(valid_tipos))

        # Verifica que valores são positivos
        self.assertTrue((df["vl_transacao"] > 0).all())

    def test_gerar_agencias(self):
        """Testa geração de tabela de agências."""
        df = _gerar_agencias(n=self.n_rows)

        # Verifica shape
        self.assertEqual(df.shape[0], self.n_rows)

        # Verifica colunas esperadas
        expected_columns = {
            "cd_agencia", "nm_agencia", "cd_banco", "nm_banco",
            "dt_abertura", "vl_capital"
        }
        self.assertEqual(set(df.columns), expected_columns)

        # Verifica formato do código da agência (4 dígitos)
        self.assertTrue(df["cd_agencia"].str.match(r'^\d{4}$').all())

        # Verifica que capital é positivo
        self.assertTrue((df["vl_capital"] > 0).all())

    def test_gerar_dados_completos_baseline(self):
        """Testa geração completa de dados no cenário baseline."""
        clientes, transacoes, agencias = _gerar_dados_completos(scenario="baseline")

        # Verifica que todos são DataFrames
        self.assertIsInstance(clientes, pd.DataFrame)
        self.assertIsInstance(transacoes, pd.DataFrame)
        self.assertIsInstance(agencias, pd.DataFrame)

        # Verifica tamanhos razoáveis (padrão da função)
        self.assertGreater(len(clientes), 0)
        self.assertGreater(len(transacoes), 0)
        self.assertGreater(len(agencias), 0)

        # Verifica relacionamento entre tabelas
        self.assertTrue(set(transacoes["cd_cliente"].dropna().unique()).issubset(set(clientes["cd_cliente"])))

    def test_gerar_dados_completos_scenarios(self):
        """Testa geração completa para todos os cenários."""
        for scenario in ["baseline", "non_breaking", "breaking"]:
            with self.subTest(scenario=scenario):
                clientes, transacoes, agencias = _gerar_dados_completos(scenario=scenario)

                # Verifica que todos são DataFrames
                self.assertIsInstance(clientes, pd.DataFrame)
                self.assertIsInstance(transacoes, pd.DataFrame)
                self.assertIsInstance(agencias, pd.DataFrame)

                # Verificações específicas por cenário
                if scenario == "breaking":
                    # No cenário breaking, clientes NÃO deve ter cd_agencia
                    self.assertNotIn("cd_agencia", clientes.columns)
                else:
                    # Nos outros cenários, clientes deve ter cd_agencia
                    self.assertIn("cd_agencia", clientes.columns)

                if scenario == "non_breaking":
                    # No cenário non_breaking, clientes deve ter cd_gestor_relacionamento
                    self.assertIn("cd_gestor_relacionamento", clientes.columns)
                else:
                    # Nos outros cenários, clientes NÃO deve ter cd_gestor_relacionamento
                    self.assertNotIn("cd_gestor_relacionamento", clientes.columns)

    def test_contrato_generation(self):
        """Testa geração de contratos."""
        for scenario in ["baseline", "non_breaking", "breaking"]:
            with self.subTest(scenario=scenario):
                # Testa contrato de clientes
                contrato_clientes = _contrato_clientes(scenario)
                self.assertIsInstance(contrato_clientes, dict)
                self.assertEqual(contrato_clientes["table"], "tb_clientes")
                self.assertIn("schema", contrato_clientes)
                self.assertIn("business_context", contrato_clientes)

                # Testa contrato de transações
                contrato_transacoes = _contrato_transacoes(scenario)
                self.assertIsInstance(contrato_transacoes, dict)
                self.assertEqual(contrato_transacoes["table"], "tb_transacoes")
                self.assertIn("schema", contrato_transacoes)

                # Testa contrato de agências
                contrato_agencias = _contrato_agencias(scenario)
                self.assertIsInstance(contrato_agencias, dict)
                self.assertEqual(contrato_agencias["table"], "tb_agencias")
                self.assertIn("schema", contrato_agencias)


class TestEdgeCases(unittest.TestCase):
    """Testes para casos de borda e condições de erro."""

    def test_zero_rows(self):
        """Testa geração com zero linhas."""
        df = _gerar_clientes(n=0, scenario="baseline")
        self.assertEqual(df.shape[0], 0)
        # Mas deve ter as colunas
        self.assertGreater(df.shape[1], 0)

    def test_negative_rows(self):
        """Testa geração com número negativo de linhas (deve tratar como zero)."""
        # A implementação atual provavelmente vai criar uma lista vazia e depois DataFrame
        df = _gerar_clientes(n=-10, scenario="baseline")
        self.assertEqual(df.shape[0], 0)  # range(-10) produz iterável vazio

    def test_inject_nulls_edge_cases(self):
        """Testa casos de borda para injeção de nulos."""
        series = pd.Series([1, 2, 3, 4, 5])

        # pct = 0.0 -> nenhum nulo
        result = _inject_nulls(series, 0.0)
        pd.testing.assert_series_equal(result, series)

        # pct = 1.0 -> todos nulos (com mock para garantir)
        with patch('numpy.random.random', return_value=np.array([0.0, 0.0, 0.0, 0.0, 0.0])):
            result = _inject_nulls(series, 1.0)
            expected = pd.Series([None, None, None, None, None])
            pd.testing.assert_series_equal(result, expected)


if __name__ == "__main__":
    unittest.main()