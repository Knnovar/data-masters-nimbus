"""
tests/test_grant_emitter.py - Testes do DDL de acesso derivado do Manifest.

O ponto central destes testes nao e a sintaxe do SQL: e a garantia de que o
emissor **so gera texto**. Nenhum caminho aqui abre conexao com workspace, e a
classificacao do contrato e a unica fonte do que entra no script.
"""

import sys
import tempfile
import unittest
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.governance.grant_emitter import MASK_FUNCTION, build_ddl, load_contract, main
from src.validation.contracts import DataContract


def manifest_dict(classificacao="confidential", sensiveis=("nome", "cpf"),
                  status="VALIDATED"):
    return {
        "table": "tb_clientes",
        "description": "cadastro de clientes",
        "owner": "dominio_riscos",
        "version": "1.0.0",
        "manifest_status": status,
        "regulatory": {"data_classification": classificacao},
        "tolerance": {"max_reject_pct": 1.0},
        "schema": [
            {"name": "id_cliente", "type": "integer", "primary_key": True},
            {"name": "nome", "type": "string",
             "regulatory_flags": ["LGPD_SENSITIVE"] if "nome" in sensiveis else []},
            {"name": "cpf", "type": "string",
             "regulatory_flags": ["LGPD_SENSITIVE"] if "cpf" in sensiveis else []},
            {"name": "dt_nascimento", "type": "date",
             "regulatory_flags": ["LGPD_SENSITIVE"] if "dt_nascimento" in sensiveis else []},
        ],
    }


def build(contract=None, **kwargs):
    contract = contract or DataContract.from_dict(manifest_dict())
    params = {"catalog": "nimbus", "schema": "silver",
              "reader_group": "grp_readers", "pii_group": "grp_pii"}
    params.update(kwargs)
    return build_ddl(contract, **params)


class TestGrants(unittest.TestCase):

    def test_concede_select_na_tabela_do_contrato(self):
        ddl = build()
        self.assertIn("GRANT SELECT ON TABLE `nimbus`.`silver`.`tb_clientes` TO `grp_readers`;", ddl)

    def test_concede_navegacao_no_catalogo_e_schema(self):
        ddl = build()
        self.assertIn("GRANT USE CATALOG ON CATALOG `nimbus` TO `grp_readers`;", ddl)
        self.assertIn("GRANT USE SCHEMA ON SCHEMA `nimbus`.`silver` TO `grp_readers`;", ddl)

    def test_classificacao_restricted_nao_concede_select_automatico(self):
        contract = DataContract.from_dict(manifest_dict(classificacao="restricted"))
        ddl = build(contract)
        self.assertNotIn("\nGRANT SELECT ON TABLE", ddl)
        self.assertIn("-- GRANT SELECT ON TABLE", ddl)

    def test_catalogo_e_schema_sao_parametrizaveis(self):
        ddl = build(catalog="corp", schema="risco_silver")
        self.assertIn("`corp`.`risco_silver`.`tb_clientes`", ddl)


class TestMascaras(unittest.TestCase):

    def test_cria_mascara_para_cada_coluna_sensivel(self):
        ddl = build()
        for coluna in ("nome", "cpf"):
            self.assertIn(
                "ALTER TABLE `nimbus`.`silver`.`tb_clientes` ALTER COLUMN `{}` SET MASK".format(coluna),
                ddl)

    def test_uma_funcao_por_tipo_e_nao_por_coluna(self):
        ddl = build()
        self.assertEqual(ddl.count("CREATE OR REPLACE FUNCTION"), 1)

    def test_funcao_de_mascara_respeita_o_grupo_informado(self):
        ddl = build()
        self.assertIn(
            "CREATE OR REPLACE FUNCTION `nimbus`.`silver`.`{}_string`(val STRING)".format(
                MASK_FUNCTION), ddl)
        self.assertIn("is_account_group_member('grp_pii')", ddl)

    def test_mascara_casa_com_o_tipo_da_coluna(self):
        contract = DataContract.from_dict(manifest_dict(sensiveis=("nome", "dt_nascimento")))
        ddl = build(contract)
        # UC exige que a funcao devolva o tipo da coluna: DATE nao pode devolver '***'
        self.assertIn("`{}_date`(val DATE)".format(MASK_FUNCTION), ddl)
        self.assertIn("THEN val ELSE NULL END;", ddl)
        self.assertIn("ALTER COLUMN `dt_nascimento` SET MASK `nimbus`.`silver`.`{}_date`;".format(
            MASK_FUNCTION), ddl)

    def test_coluna_nao_marcada_nao_ganha_mascara(self):
        ddl = build()
        self.assertNotIn("ALTER COLUMN `id_cliente` SET MASK", ddl)

    def test_sem_coluna_sensivel_nao_gera_funcao(self):
        contract = DataContract.from_dict(manifest_dict(sensiveis=()))
        ddl = build(contract)
        self.assertNotIn("CREATE OR REPLACE FUNCTION", ddl)
        self.assertIn("Nenhuma coluna marcada LGPD_SENSITIVE", ddl)


class TestCabecalhoEGovernanca(unittest.TestCase):

    def test_declara_que_nao_executa(self):
        self.assertIn("NAO E EXECUTADO PELO PIPELINE", build())

    def test_manifest_draft_gera_aviso(self):
        contract = DataContract.from_dict(manifest_dict(status="DRAFT"))
        ddl = build(contract)
        self.assertIn("[ATENCAO] Manifest em DRAFT", ddl)

    def test_manifest_validated_nao_gera_aviso(self):
        self.assertNotIn("[ATENCAO]", build())

    def test_cabecalho_traz_owner_e_versao(self):
        ddl = build()
        self.assertIn("dominio_riscos", ddl)
        self.assertIn("versao 1.0.0", ddl)


class TestCli(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.manifest = Path(self.tmp.name) / "tb_clientes.yaml"
        self.manifest.write_text(yaml.safe_dump(manifest_dict()), encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_load_contract_le_o_yaml(self):
        self.assertEqual(load_contract(self.manifest).table, "tb_clientes")

    def test_grava_arquivo_com_output(self):
        destino = Path(self.tmp.name) / "out" / "grants.sql"
        code = main(["--file", str(self.manifest), "--output", str(destino)])
        self.assertEqual(code, 0)
        self.assertIn("GRANT SELECT ON TABLE", destino.read_text(encoding="utf-8"))

    def test_manifest_inexistente_sai_com_erro(self):
        self.assertEqual(main(["--file", str(Path(self.tmp.name) / "nao_existe.yaml")]), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
