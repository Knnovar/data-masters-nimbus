"""
tests/test_contracts.py - Testes para src/validation/contracts.py
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.validation.contracts import (
    DataContract, ColumnContract, TolerancePolicy,
    SourceInfo, RegulatoryInfo, StewardInfo, SampleQuery,
)

MINIMAL = {
    "table": "tb_teste", "description": "Tabela de teste",
    "owner": "squad", "version": "1.0.0",
    "tolerance": {"max_null_pct": 20, "allow_duplicates": False},
    "schema": [
        {"name": "id",    "type": "string", "nullable": False, "primary_key": True},
        {"name": "valor", "type": "float",  "nullable": True},
    ],
}

EXTENDED = {
    **MINIMAL,
    "manifest_status": "DRAFT",
    "source": {"system": "SIS_X", "format": "csv", "encoding": "utf-8",
               "os": "unix", "update_frequency": "daily"},
    "regulatory": {"tags": ["LGPD", "BACEN_4658"], "data_classification": "confidential",
                   "retention_years": 7},
    "steward": {"name": "Joao", "email": "joao@banco.com"},
    "business_context": "Contexto de negocio.",
    "dependencies": ["tb_outra"],
    "sample_queries": [{"description": "Contagem", "sql": "SELECT COUNT(*) FROM tb_teste"}],
    "schema": [
        {"name": "id",    "type": "string", "nullable": False, "primary_key": True,
         "description": "Chave primaria.", "regulatory_flags": [], "business_rules": []},
        {"name": "nr_cpf","type": "string", "nullable": False, "description": "CPF.",
         "regulatory_flags": ["LGPD_SENSITIVE"], "business_rules": []},
        {"name": "valor", "type": "float",  "nullable": True, "description": "Valor.",
         "regulatory_flags": ["SCR_CANDIDATE"], "business_rules": []},
    ],
}


class TestLoading(unittest.TestCase):

    def test_minimal_loads(self):
        c = DataContract.from_dict(MINIMAL)
        self.assertEqual(c.table, "tb_teste")
        self.assertEqual(len(c.schema), 2)

    def test_extended_loads(self):
        c = DataContract.from_dict(EXTENDED)
        self.assertEqual(c.manifest_status, "DRAFT")
        self.assertEqual(c.source.format, "csv")
        self.assertEqual(c.regulatory.tags, ["LGPD", "BACEN_4658"])
        self.assertEqual(c.steward.email, "joao@banco.com")
        self.assertEqual(len(c.sample_queries), 1)

    def test_minimal_has_safe_defaults(self):
        c = DataContract.from_dict(MINIMAL)
        self.assertEqual(c.manifest_status, "DRAFT")
        self.assertIsNone(c.source)
        self.assertIsNone(c.regulatory)
        self.assertIsNone(c.business_context)
        self.assertEqual(c.dependencies, [])

    def test_invalid_version_raises(self):
        bad = {**MINIMAL, "version": "1.0"}
        with self.assertRaises(ValueError):
            DataContract.from_dict(bad)

    def test_non_numeric_version_raises(self):
        bad = {**MINIMAL, "version": "1.a.0"}
        with self.assertRaises(ValueError):
            DataContract.from_dict(bad)


class TestMethods(unittest.TestCase):

    def setUp(self):
        self.c = DataContract.from_dict(EXTENDED)
        self.m = DataContract.from_dict(MINIMAL)

    def test_get_primary_keys(self):
        self.assertEqual(self.c.get_primary_keys(), ["id"])

    def test_get_non_nullable(self):
        non_null = self.c.get_non_nullable()
        self.assertIn("id", non_null)
        self.assertIn("nr_cpf", non_null)
        self.assertNotIn("valor", non_null)

    def test_column_names(self):
        self.assertEqual(self.c.column_names(), ["id", "nr_cpf", "valor"])

    def test_is_validated_draft(self):
        self.assertFalse(self.c.is_validated())

    def test_is_validated_true(self):
        v = DataContract.from_dict({**EXTENDED, "manifest_status": "VALIDATED"})
        self.assertTrue(v.is_validated())

    def test_has_extended_metadata_true(self):
        self.assertTrue(self.c.has_extended_metadata())

    def test_has_extended_metadata_false(self):
        self.assertFalse(self.m.has_extended_metadata())

    def test_lgpd_sensitive_columns(self):
        sensitive = self.c.lgpd_sensitive_columns()
        self.assertIn("nr_cpf", sensitive)
        self.assertNotIn("id", sensitive)
        self.assertNotIn("valor", sensitive)


class TestColumnContract(unittest.TestCase):

    def test_basic_column_defaults(self):
        col = ColumnContract.from_dict({"name": "cd_teste", "type": "string"})
        self.assertTrue(col.nullable)
        self.assertFalse(col.primary_key)
        self.assertIsNone(col.description)
        self.assertEqual(col.regulatory_flags, [])

    def test_extended_fields(self):
        col = ColumnContract.from_dict({
            "name": "nr_cpf", "type": "string",
            "description": "CPF", "sas_label": "CPF SEM MASCARA",
            "regulatory_flags": ["LGPD_SENSITIVE"], "business_rules": ["11 digitos"],
        })
        self.assertEqual(col.sas_label, "CPF SEM MASCARA")
        self.assertIn("LGPD_SENSITIVE", col.regulatory_flags)


class TestTolerancePolicy(unittest.TestCase):

    def test_defaults(self):
        t = TolerancePolicy.from_dict({})
        self.assertEqual(t.max_null_pct, 20.0)
        self.assertFalse(t.allow_duplicates)

    def test_custom(self):
        t = TolerancePolicy.from_dict({"max_null_pct": 5, "allow_duplicates": True})
        self.assertEqual(t.max_null_pct, 5)
        self.assertTrue(t.allow_duplicates)


if __name__ == "__main__":
    unittest.main()
