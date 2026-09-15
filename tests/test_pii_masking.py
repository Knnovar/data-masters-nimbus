"""
tests/test_pii_masking.py - Testes do mascaramento de PII na quarentena.

Garante tres coisas que a banca pergunta: que o valor sensivel nao sobrevive em
claro no arquivo de rejeitos, que o token continua correlacionavel (mesmo valor,
mesmo token) e que quem decide o que e sensivel e o Manifest, nao o nome da
coluna.
"""

import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.storage.pii_masking import (MASK_PREFIX, mask_rejected,
                                     mask_value, sensitive_columns)
from src.storage.storage import LocalStorage, _apply_contract
from src.validation.contracts import DataContract

_LAYERS = ["bronze", "silver", "gold", "quarantine", "contracts", "metrics", "reports"]


def make_contract(sensiveis=("nome",)) -> DataContract:
    return DataContract.from_dict({
        "table": "tb_clientes",
        "description": "clientes",
        "owner": "riscos",
        "version": "1.0.0",
        "tolerance": {"max_reject_pct": 50.0},
        "schema": [
            {"name": "id", "type": "integer", "primary_key": True},
            {"name": "nome", "type": "string",
             "regulatory_flags": ["LGPD_SENSITIVE"] if "nome" in sensiveis else []},
            {"name": "cpf", "type": "string",
             "regulatory_flags": ["LGPD_SENSITIVE"] if "cpf" in sensiveis else []},
            {"name": "idade", "type": "integer"},
        ],
    })


class TestMaskValue(unittest.TestCase):

    def test_token_tem_prefixo_e_nao_contem_o_valor(self):
        token = mask_value("Maria Silva")
        self.assertTrue(token.startswith(MASK_PREFIX))
        self.assertNotIn("Maria", token)

    def test_token_e_deterministico(self):
        self.assertEqual(mask_value("123.456.789-00"), mask_value("123.456.789-00"))

    def test_valores_diferentes_geram_tokens_diferentes(self):
        self.assertNotEqual(mask_value("Ana"), mask_value("Bruno"))

    def test_vazio_continua_vazio(self):
        for valor in (None, "", "   ", "nan", "None"):
            self.assertEqual(mask_value(valor), "")


class TestSensitiveColumns(unittest.TestCase):

    def test_le_do_manifest(self):
        self.assertEqual(sensitive_columns(make_contract(("nome", "cpf"))), ["nome", "cpf"])

    def test_contrato_ausente_nao_quebra(self):
        self.assertEqual(sensitive_columns(None), [])


class TestMaskRejected(unittest.TestCase):

    def _df(self):
        return pd.DataFrame({
            "id": ["1", "2"],
            "nome": ["Maria Silva", "Maria Silva"],
            "cpf": ["111", "222"],
            "idade": ["x", "y"],
            "_reject_columns": ["idade", "nome,idade"],
            "_reject_values": ["x", "Maria Silva|y"],
            "_reject_reason": ["TYPE_NOT_CONFORMANT", "TYPE_NOT_CONFORMANT"],
        })

    def test_mascara_apenas_coluna_declarada(self):
        out = mask_rejected(self._df(), make_contract(("nome",)))
        self.assertTrue(all(v.startswith(MASK_PREFIX) for v in out["nome"]))
        self.assertEqual(list(out["cpf"]), ["111", "222"])
        self.assertEqual(list(out["idade"]), ["x", "y"])

    def test_mesma_pessoa_continua_correlacionavel(self):
        out = mask_rejected(self._df(), make_contract(("nome",)))
        self.assertEqual(out["nome"].iloc[0], out["nome"].iloc[1])

    def test_mascara_tambem_o_rastro_reject_values(self):
        out = mask_rejected(self._df(), make_contract(("nome",)))
        self.assertNotIn("Maria", out["_reject_values"].iloc[1])
        # a posicao nao sensivel do rastro e preservada
        self.assertTrue(out["_reject_values"].iloc[1].endswith("|y"))
        self.assertEqual(out["_reject_values"].iloc[0], "x")

    def test_sem_coluna_sensivel_devolve_intacto(self):
        df = self._df()
        out = mask_rejected(df, make_contract(()))
        pd.testing.assert_frame_equal(df, out)

    def test_nao_altera_o_dataframe_original(self):
        df = self._df()
        mask_rejected(df, make_contract(("nome",)))
        self.assertEqual(df["nome"].iloc[0], "Maria Silva")


class TestQuarentenaGravada(unittest.TestCase):
    """O caminho real: _apply_contract grava o rejeito ja mascarado."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.storage = LocalStorage({l: base / l for l in _LAYERS})
        self.base = base

    def tearDown(self):
        self.tmp.cleanup()

    def _promove(self, mascarar=True):
        import config
        anterior = getattr(config, "QUARANTINE_MASK_PII", True)
        config.QUARANTINE_MASK_PII = mascarar
        try:
            df = pd.DataFrame({"id": ["1"], "nome": ["Maria Silva"],
                               "cpf": ["111"], "idade": ["nao_e_numero"]})
            _apply_contract(self.storage, df, "tb_clientes.csv", make_contract(("nome",)))
        finally:
            config.QUARANTINE_MASK_PII = anterior
        destino = self.base / "quarantine" / "reject_tb_clientes.csv"
        self.assertTrue(destino.exists())
        return destino.read_text(encoding="utf-8")

    def test_arquivo_de_rejeito_nao_contem_pii(self):
        conteudo = self._promove(mascarar=True)
        self.assertNotIn("Maria Silva", conteudo)
        self.assertIn(MASK_PREFIX, conteudo)
        # a linha continua auditavel: motivo e valor nao sensivel preservados
        self.assertIn("nao_e_numero", conteudo)

    def test_flag_desligada_mantem_comportamento_antigo(self):
        conteudo = self._promove(mascarar=False)
        self.assertIn("Maria Silva", conteudo)


if __name__ == "__main__":
    unittest.main(verbosity=2)
