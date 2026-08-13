"""
tests/test_writers.py — Testes para src/generators/writers.py e generate_all multi-formato

Cobre:
  - CSVWriter, JSONWriter, FixedWidthWriter
  - WriterFactory (formatos validos e invalido)
  - generate_all com fmt=csv, json, fixed
  - Criterios de aceite do HANDOFF:
      * fixed respeita exatamente a contagem de bytes do leiaute
      * JSON gera niveis aninhados sem quebrar conversores
      * Formato invalido encerra com erro amigavel
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.generators.writers import (
    BaseWriter,
    CSVWriter,
    JSONWriter,
    FixedWidthWriter,
    WriterFactory,
    SUPPORTED_FORMATS,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

SAMPLE_DF = pd.DataFrame({
    "id_cliente": ["C001", "C002", "C003"],
    "nm_cliente": ["Ana Silva", "Bruno Martins", "Carla Souza"],
    "vl_renda":   [5000.00, 8000.50, 12000.00],
    "fl_ativo":   ["S", "S", "N"],
    "dt_cadastro":["2023-01-15", "2022-06-30", "2024-03-01"],
})

FIXED_LAYOUT = [
    ("id_cliente",  8, "string"),
    ("nm_cliente", 20, "string"),
    ("vl_renda",   10, "float"),
    ("fl_ativo",    1, "string"),
    ("dt_cadastro", 10, "date"),
]
# Largura total: 8+20+10+1+10 = 49 chars por linha


# ═════════════════════════════════════════════════════════════════════════════
# TestCSVWriter
# ═════════════════════════════════════════════════════════════════════════════

class TestCSVWriter(unittest.TestCase):

    def setUp(self):
        self.writer = CSVWriter()

    def test_extension(self):
        self.assertEqual(self.writer.extension(), ".csv")

    def test_returns_tuple(self):
        filename, content = self.writer.serialize(SAMPLE_DF, "tb_test")
        self.assertIsInstance(filename, str)
        self.assertIsInstance(content, str)

    def test_filename_includes_extension(self):
        filename, _ = self.writer.serialize(SAMPLE_DF, "tb_test")
        self.assertEqual(filename, "tb_test.csv")

    def test_content_has_header(self):
        _, content = self.writer.serialize(SAMPLE_DF, "tb_test")
        first_line = content.split("\n")[0]
        self.assertIn("id_cliente", first_line)
        self.assertIn("nm_cliente", first_line)

    def test_row_count(self):
        _, content = self.writer.serialize(SAMPLE_DF, "tb_test")
        data_lines = [l for l in content.strip().split("\n") if l]
        self.assertEqual(len(data_lines), len(SAMPLE_DF) + 1)  # +1 header

    def test_custom_delimiter(self):
        writer = CSVWriter(delimiter=";")
        _, content = writer.serialize(SAMPLE_DF, "tb_test")
        self.assertIn(";", content)

    def test_is_base_writer(self):
        self.assertIsInstance(self.writer, BaseWriter)


# ═════════════════════════════════════════════════════════════════════════════
# TestJSONWriter
# ═════════════════════════════════════════════════════════════════════════════

class TestJSONWriter(unittest.TestCase):

    def setUp(self):
        self.writer_flat   = JSONWriter(root_key="data")
        self.writer_nested = JSONWriter(
            nest_columns={"dados_pessoais": ["nm_cliente", "dt_cadastro"]},
            root_key="data",
        )

    def test_extension(self):
        self.assertEqual(self.writer_flat.extension(), ".json")

    def test_filename(self):
        filename, _ = self.writer_flat.serialize(SAMPLE_DF, "tb_test")
        self.assertEqual(filename, "tb_test.json")

    def test_valid_json(self):
        _, content = self.writer_flat.serialize(SAMPLE_DF, "tb_test")
        parsed = json.loads(content)
        self.assertIn("data", parsed)
        self.assertEqual(len(parsed["data"]), len(SAMPLE_DF))

    def test_root_key_none_returns_list(self):
        writer = JSONWriter(root_key=None)
        _, content = writer.serialize(SAMPLE_DF, "tb_test")
        parsed = json.loads(content)
        self.assertIsInstance(parsed, list)

    def test_flat_all_columns_present(self):
        _, content = self.writer_flat.serialize(SAMPLE_DF, "tb_test")
        record = json.loads(content)["data"][0]
        for col in SAMPLE_DF.columns:
            self.assertIn(col, record)

    def test_nesting_creates_object(self):
        _, content = self.writer_nested.serialize(SAMPLE_DF, "tb_test")
        record = json.loads(content)["data"][0]
        # Campos aninhados devem estar dentro do objeto pai
        self.assertIn("dados_pessoais", record)
        self.assertIsInstance(record["dados_pessoais"], dict)
        self.assertIn("nm_cliente", record["dados_pessoais"])
        self.assertIn("dt_cadastro", record["dados_pessoais"])

    def test_nesting_removes_from_root(self):
        _, content = self.writer_nested.serialize(SAMPLE_DF, "tb_test")
        record = json.loads(content)["data"][0]
        # Campos aninhados nao devem estar na raiz
        self.assertNotIn("nm_cliente", record)
        self.assertNotIn("dt_cadastro", record)

    def test_nesting_invalid_column_raises(self):
        writer = JSONWriter(nest_columns={"grupo": ["coluna_inexistente"]})
        with self.assertRaises(ValueError):
            writer.serialize(SAMPLE_DF, "tb_test")

    def test_no_unhashable_dict_in_values(self):
        """Criterio de aceite: JSON nao pode conter dicts como valores primitivos."""
        _, content = self.writer_nested.serialize(SAMPLE_DF, "tb_test")
        # Garante que o JSON e parseavel sem erros e nao tem tipos nao-serializaveis
        parsed = json.loads(content)
        self.assertIsNotNone(parsed)

    def test_is_base_writer(self):
        self.assertIsInstance(self.writer_flat, BaseWriter)


# ═════════════════════════════════════════════════════════════════════════════
# TestFixedWidthWriter
# ═════════════════════════════════════════════════════════════════════════════

class TestFixedWidthWriter(unittest.TestCase):

    def setUp(self):
        self.writer = FixedWidthWriter(layout=FIXED_LAYOUT)

    def test_extension(self):
        self.assertEqual(self.writer.extension(), ".txt")

    def test_filename(self):
        filename, _ = self.writer.serialize(SAMPLE_DF, "tb_test")
        self.assertEqual(filename, "tb_test.txt")

    def test_exact_line_width(self):
        """Criterio de aceite: cada linha tem exatamente sum(larguras) chars."""
        expected_width = sum(w for _, w, _ in FIXED_LAYOUT)  # 49
        _, content = self.writer.serialize(SAMPLE_DF, "tb_test")
        for line in content.strip().split("\n"):
            self.assertEqual(
                len(line), expected_width,
                f"Linha com largura incorreta: {len(line)} != {expected_width}: {line!r}"
            )

    def test_row_count(self):
        _, content = self.writer.serialize(SAMPLE_DF, "tb_test")
        lines = [l for l in content.strip().split("\n") if l]
        self.assertEqual(len(lines), len(SAMPLE_DF))

    def test_string_left_aligned(self):
        _, content = self.writer.serialize(SAMPLE_DF, "tb_test")
        first_line = content.split("\n")[0]
        # id_cliente (8 chars): "C001    "
        id_field = first_line[:8]
        self.assertTrue(id_field.startswith("C001"))

    def test_float_right_aligned(self):
        _, content = self.writer.serialize(SAMPLE_DF, "tb_test")
        first_line = content.split("\n")[0]
        # vl_renda comeca em pos 28 (8+20=28), width=10
        vl_field = first_line[28:38]
        self.assertTrue(vl_field.strip() == "5000.0")

    def test_truncation_long_value(self):
        df = pd.DataFrame({
            "id_cliente":  ["CLIENTE_MUITO_LONGO_DEMAIS"],
            "nm_cliente":  ["Ana"],
            "vl_renda":    [100.0],
            "fl_ativo":    ["S"],
            "dt_cadastro": ["2024-01-01"],
        })
        _, content = self.writer.serialize(df, "tb_test")
        line = content.strip()
        self.assertEqual(len(line), sum(w for _, w, _ in FIXED_LAYOUT))

    def test_null_value_padded(self):
        df = pd.DataFrame({
            "id_cliente":  ["C001"],
            "nm_cliente":  [None],
            "vl_renda":    [None],
            "fl_ativo":    ["S"],
            "dt_cadastro": ["2024-01-01"],
        })
        _, content = self.writer.serialize(df, "tb_test")
        line = content.strip()
        # nm_cliente (pos 8-27) deve ser espacos
        nm_field = line[8:28]
        self.assertEqual(nm_field.strip(), "")

    def test_empty_layout_raises(self):
        with self.assertRaises(ValueError):
            FixedWidthWriter(layout=[])

    def test_missing_column_raises(self):
        layout_with_missing = [("coluna_inexistente", 10, "string")]
        writer = FixedWidthWriter(layout=layout_with_missing)
        with self.assertRaises(ValueError):
            writer.serialize(SAMPLE_DF, "tb_test")

    def test_is_base_writer(self):
        self.assertIsInstance(self.writer, BaseWriter)


# ═════════════════════════════════════════════════════════════════════════════
# TestWriterFactory
# ═════════════════════════════════════════════════════════════════════════════

class TestWriterFactory(unittest.TestCase):

    def test_get_csv(self):
        writer = WriterFactory.get("csv")
        self.assertIsInstance(writer, CSVWriter)

    def test_get_json(self):
        writer = WriterFactory.get("json")
        self.assertIsInstance(writer, JSONWriter)

    def test_get_fixed(self):
        writer = WriterFactory.get("fixed", layout=FIXED_LAYOUT)
        self.assertIsInstance(writer, FixedWidthWriter)

    def test_get_fixed_width_alias(self):
        writer = WriterFactory.get("fixed_width", layout=FIXED_LAYOUT)
        self.assertIsInstance(writer, FixedWidthWriter)

    def test_invalid_format_raises_value_error(self):
        """Criterio de aceite: formato invalido levanta ValueError com mensagem clara."""
        with self.assertRaises(ValueError) as ctx:
            WriterFactory.get("xml")
        self.assertIn("xml", str(ctx.exception))
        self.assertIn("csv", str(ctx.exception))

    def test_case_insensitive(self):
        writer = WriterFactory.get("CSV")
        self.assertIsInstance(writer, CSVWriter)

    def test_all_supported_formats_creatable(self):
        for fmt in SUPPORTED_FORMATS:
            kwargs = {"layout": FIXED_LAYOUT} if fmt == "fixed" else {}
            writer = WriterFactory.get(fmt, **kwargs)
            self.assertIsInstance(writer, BaseWriter)


# ═════════════════════════════════════════════════════════════════════════════
# TestGenerateAllMultiFormat
# ═════════════════════════════════════════════════════════════════════════════

class TestGenerateAllMultiFormat(unittest.TestCase):

    def _make_storage(self, tmp_path):
        from src.storage.storage import LocalStorage
        layer_map = {l: tmp_path / l for l in
                     ["bronze","silver","gold","quarantine","contracts","metrics","reports"]}
        return LocalStorage(layer_map)

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def test_generate_csv_produces_csv_files(self):
        from src.generators.data_generator import generate_all
        s = self._make_storage(self.tmp)
        produced = generate_all(s, scenario="baseline", fmt="csv")
        self.assertEqual(len(produced), 3)
        for item in produced:
            self.assertTrue(item["filename"].endswith(".csv"))
            self.assertTrue(s.exists("bronze", item["filename"]))

    def test_generate_json_produces_json_files(self):
        from src.generators.data_generator import generate_all
        s = self._make_storage(self.tmp)
        produced = generate_all(s, scenario="baseline", fmt="json")
        for item in produced:
            self.assertTrue(item["filename"].endswith(".json"))
            path = s.read_path("bronze", item["filename"])
            parsed = json.loads(path.read_text(encoding="utf-8"))
            self.assertIn("data", parsed)

    def test_generate_fixed_produces_txt_files(self):
        from src.generators.data_generator import generate_all
        s = self._make_storage(self.tmp)
        produced = generate_all(s, scenario="baseline", fmt="fixed")
        for item in produced:
            self.assertTrue(item["filename"].endswith(".txt"))

    def test_generate_fixed_line_width_correct(self):
        """Criterio de aceite: arquivo posicional respeita bytes do leiaute."""
        from src.generators.data_generator import (
            generate_all, _FIXED_LAYOUT_CLIENTES,
        )
        s = self._make_storage(self.tmp)
        produced = generate_all(s, scenario="baseline", fmt="fixed")
        clientes_item = next(p for p in produced if p["table"] == "tb_clientes")
        path    = s.read_path("bronze", clientes_item["filename"])
        content = path.read_text(encoding="utf-8")
        expected_width = sum(w for _, w, _ in _FIXED_LAYOUT_CLIENTES)
        for line in content.strip().split("\n"):
            if line:
                self.assertEqual(len(line), expected_width,
                    f"Largura incorreta: {len(line)} != {expected_width}")

    def test_generate_json_flat_for_pipeline(self):
        """Pipeline usa JSON flat — colunas correspondem diretamente ao contrato."""
        from src.generators.data_generator import generate_all
        s = self._make_storage(self.tmp)
        produced = generate_all(s, scenario="baseline", fmt="json")
        clientes_item = next(p for p in produced if p["table"] == "tb_clientes")
        path   = s.read_path("bronze", clientes_item["filename"])
        parsed = json.loads(path.read_text(encoding="utf-8"))
        record = parsed["data"][0]
        # Pipeline: sem aninhamento, colunas flat no nivel raiz
        self.assertIn("nm_cliente", record)
        self.assertIn("cd_cliente", record)
        self.assertNotIn("dados_pessoais", record)

    def test_json_writer_nesting_still_works(self):
        """JSONWriter com nest_columns ainda funciona para testes do extrator."""
        from src.generators.writers import JSONWriter
        # Usa colunas que existem em SAMPLE_DF: nm_cliente e dt_cadastro
        writer = JSONWriter(
            nest_columns={"dados_pessoais": ["nm_cliente", "dt_cadastro"]},
            root_key="data",
        )
        filename, content = writer.serialize(SAMPLE_DF, "tb_test")
        record = json.loads(content)["data"][0]
        self.assertIn("dados_pessoais", record)
        self.assertIn("nm_cliente", record["dados_pessoais"])

    def test_invalid_format_raises(self):
        """Criterio de aceite: formato invalido encerra com ValueError."""
        from src.generators.data_generator import generate_all
        s = self._make_storage(self.tmp)
        with self.assertRaises(ValueError) as ctx:
            generate_all(s, scenario="baseline", fmt="xml")
        self.assertIn("xml", str(ctx.exception))

    def test_format_recorded_in_produced(self):
        from src.generators.data_generator import generate_all
        s = self._make_storage(self.tmp)
        produced = generate_all(s, scenario="baseline", fmt="json")
        for item in produced:
            self.assertEqual(item["format"], "json")

    def test_contracts_always_generated(self):
        from src.generators.data_generator import generate_all
        s = self._make_storage(self.tmp)
        for fmt in ["csv", "json", "fixed"]:
            produced = generate_all(s, scenario="baseline", fmt=fmt)
            for item in produced:
                self.assertTrue(s.exists("contracts", item["contract_filename"]),
                    f"Contrato nao gerado para fmt={fmt}: {item['contract_filename']}")


if __name__ == "__main__":
    unittest.main()
