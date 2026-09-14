"""
tests/test_gate_silver.py - Ordem gate/Silver.

O gate so pode decidir depois do cast (e o cast que produz a taxa de rejeito),
entao o Parquet da carga reprovada ja existe quando o bloqueio acontece. Estes
testes cobrem o que se faz com ele: sair da Silver e ir para a quarentena, para
que nenhum consumidor leia carga bloqueada achando que passou.
"""

import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))
import config
from run_pipeline import quarantine_blocked_silver
from src.storage.storage import LocalStorage

_LAYERS = ["bronze", "silver", "gold", "quarantine", "contracts", "metrics", "reports"]


class TestQuarantineBlockedSilver(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.storage = LocalStorage({l: self.base / l for l in _LAYERS})
        self.storage.write_parquet("silver", "tb_clientes.parquet",
                                   pd.DataFrame({"id": [1, 2]}))
        self._flag = config.QUARANTINE_BLOCKED_SILVER

    def tearDown(self):
        config.QUARANTINE_BLOCKED_SILVER = self._flag
        self.tmp.cleanup()

    def test_retira_o_parquet_da_silver(self):
        movido = quarantine_blocked_silver(self.storage, "tb_clientes.parquet")
        self.assertEqual(movido, "tb_clientes.parquet")
        self.assertFalse(self.storage.exists("silver", "tb_clientes.parquet"))

    def test_artefato_continua_auditavel_na_quarentena(self):
        quarantine_blocked_silver(self.storage, "tb_clientes.parquet")
        self.assertTrue(self.storage.exists("quarantine", "tb_clientes.parquet"))
        destino = self.storage.read_path("quarantine", "tb_clientes.parquet")
        self.assertEqual(len(pd.read_parquet(destino)), 2)

    def test_flag_desligada_mantem_o_parquet_na_silver(self):
        config.QUARANTINE_BLOCKED_SILVER = False
        self.assertIsNone(quarantine_blocked_silver(self.storage, "tb_clientes.parquet"))
        self.assertTrue(self.storage.exists("silver", "tb_clientes.parquet"))

    def test_sem_arquivo_promovido_nao_faz_nada(self):
        self.assertIsNone(quarantine_blocked_silver(self.storage, None))
        self.assertIsNone(quarantine_blocked_silver(self.storage, "nao_existe.parquet"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
