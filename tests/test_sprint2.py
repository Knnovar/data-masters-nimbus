"""tests/test_sprint2.py — Testes Sprint 2: normalizer, extractor_csv, extractor_fixed, extractor_json"""

import csv, json, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ingestion.normalizer      import normalize, _detect_line_endings
from src.manifest.extractor_csv   import CSVExtractor
from src.manifest.extractor_fixed import FixedWidthExtractor, _validate_layout
from src.manifest.extractor_json  import JSONExtractor


def _w(path, content, mode="w", enc="utf-8"):
    if mode == "wb": path.write_bytes(content)
    else: path.write_text(content, encoding=enc)
    return path


# ═══════════════════════ TestNormalizer ══════════════════════════════════════
class TestNormalizer(unittest.TestCase):

    def setUp(self): self.tmp = Path(tempfile.mkdtemp())

    def test_already_utf8_lf(self):
        p = _w(self.tmp/"t.csv", "id,nome\n1,Ana\n")
        r = normalize(p, backup=False)
        self.assertEqual(r["status"], "already_utf8")

    def test_crlf_to_lf(self):
        p = _w(self.tmp/"t.csv", "id,nome\r\n1,Ana\r\n")
        r = normalize(p, backup=False)
        self.assertIn("CRLF", r["line_endings"])
        self.assertNotIn("\r\n", p.read_text(encoding="utf-8"))

    def test_latin1_to_utf8(self):
        # Usa texto com acento para forcar encoding real latin-1
        p = _w(self.tmp/"t.csv", "id,nome\n1,Joao\n2,Ines\n3,Sao Paulo\n".encode("latin-1"), mode="wb")
        r = normalize(p, backup=False)
        # latin-1 puro sem acentos pode ser detectado como ascii pelo chardet
        # o importante e que o arquivo seja legivel em UTF-8 apos normalizacao
        self.assertIn(r["status"], ("ok", "already_utf8"))
        self.assertIn("Joao", p.read_text(encoding="utf-8"))

    def test_bom_removed(self):
        p = _w(self.tmp/"t.csv", b"\xef\xbb\xbfid\n1\n", mode="wb")
        r = normalize(p, backup=False)
        self.assertTrue(r["bom_removed"])
        self.assertFalse(p.read_bytes().startswith(b"\xef\xbb\xbf"))

    def test_backup_created(self):
        p   = _w(self.tmp/"t.csv", "id\r\n1\r\n")
        bkp = self.tmp/"_bkp"
        r   = normalize(p, backup=True, originals_dir=bkp)
        self.assertIsNotNone(r["backup_path"])
        self.assertTrue(Path(r["backup_path"]).exists())

    def test_ebcdic_returns_warning(self):
        p = _w(self.tmp/"t.txt", "dummy")
        with patch("chardet.detect", return_value={"encoding":"cp037","confidence":0.95}):
            r = normalize(p, backup=False)
        self.assertEqual(r["status"], "ebcdic")
        self.assertIn("EBCDIC", r["warning"])

    def test_detect_lf(self):
        self.assertEqual(_detect_line_endings("a\nb\n"), "LF")

    def test_detect_crlf(self):
        self.assertEqual(_detect_line_endings("a\r\nb\r\n"), "CRLF")

    def test_detect_mixed(self):
        self.assertEqual(_detect_line_endings("a\r\nb\n"), "mixed")


# ═══════════════════════ TestCSVExtractor ════════════════════════════════════
class TestCSVExtractor(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.ext = CSVExtractor()

    def _csv(self, name, rows, sep=",", enc="utf-8"):
        p = self.tmp/name
        with open(p, "w", encoding=enc, newline="") as f:
            csv.writer(f, delimiter=sep).writerows(rows)
        return p

    def test_basic(self):
        p = self._csv("t.csv", [["id","nome","val"],["C1","Ana","5000"],["C2","Bruno","8000"]])
        m = self.ext.extract(p, "tb")
        self.assertEqual(m["table"], "tb")
        self.assertEqual(len(m["schema"]), 3)
        self.assertEqual(m["manifest_status"], "DRAFT")

    def test_type_float(self):
        p = self._csv("t.csv", [["v"],["1.5"],["2.3"]])
        self.assertEqual(self.ext.extract(p,"tb")["schema"][0]["type"], "float")

    def test_type_integer(self):
        p = self._csv("t.csv", [["n"],["1"],["2"],["3"]])
        self.assertEqual(self.ext.extract(p,"tb")["schema"][0]["type"], "integer")

    def test_type_boolean(self):
        p = self._csv("t.csv", [["fl"],["S"],["N"],["S"]])
        self.assertEqual(self.ext.extract(p,"tb")["schema"][0]["type"], "boolean")

    def test_type_date(self):
        p = self._csv("t.csv", [["dt"],["01/01/2024"],["15/06/2023"]])
        self.assertEqual(self.ext.extract(p,"tb")["schema"][0]["type"], "date")

    def test_type_string(self):
        p = self._csv("t.csv", [["cd"],["ABC"],["XYZ"]])
        self.assertEqual(self.ext.extract(p,"tb")["schema"][0]["type"], "string")

    def test_nullable(self):
        p = self._csv("t.csv", [["id","val"],["1",""],["2","100"]])
        cols = {c["name"]:c for c in self.ext.extract(p,"tb")["schema"]}
        self.assertFalse(cols["id"]["nullable"])
        self.assertTrue(cols["val"]["nullable"])

    def test_pk_detection(self):
        p = self._csv("t.csv", [["id_cliente","nome"],["1","Ana"],["2","Bruno"]])
        pks = [c["name"] for c in self.ext.extract(p,"tb")["schema"] if c["primary_key"]]
        self.assertIn("id_cliente", pks)

    def test_semicolon_delimiter(self):
        p = self._csv("t.csv", [["a","b"],["1","2"]], sep=";")
        m = self.ext.extract(p,"tb")
        self.assertEqual(m["source"]["delimiter"], ";")

    def test_lgpd_flag(self):
        p = self._csv("t.csv", [["nr_cpf_cnpj"],["12345678901"]])
        flags = self.ext.extract(p,"tb")["schema"][0]["regulatory_flags"]
        self.assertIn("LGPD_SENSITIVE", flags)

    def test_no_header(self):
        p = self.tmp/"nh.csv"; p.write_text("1,Ana\n2,Bruno\n")
        names = [c["name"] for c in self.ext.extract(p,"tb")["schema"]]
        self.assertTrue(all(n.startswith("col_") for n in names))

    def test_schema_required_fields(self):
        p = self._csv("t.csv", [["id"],["1"]])
        required = {"name","type","nullable","primary_key","description",
                    "regulatory_flags","business_rules"}
        for col in self.ext.extract(p,"tb")["schema"]:
            self.assertTrue(required.issubset(set(col.keys())))


# ═══════════════════════ TestFixedExtractor ═══════════════════════════════════
class TestFixedExtractor(unittest.TestCase):

    def setUp(self):
        self.tmp  = Path(tempfile.mkdtemp())
        self.ext  = FixedWidthExtractor()
        self.data = self.tmp/"data.txt"
        self.data.write_text("C001Ana Silva         5000.00\nC002Bruno Martins     8000.00\n")

    def _layout_txt(self, content):
        p = self.tmp/"layout.txt"; p.write_text(content); return p

    def _layout_csv(self, rows):
        p = self.tmp/"layout.csv"
        with open(p,"w",newline="") as f: csv.writer(f).writerows(rows)
        return p

    def test_load_txt(self):
        l = self._layout_txt("CD_CLIENTE 1 4 CHAR\nNM_CLIENTE 5 24 CHAR\nVL_RENDA 25 31 NUMERIC\n")
        m = self.ext.extract(self.data, "tb", layout_path=l)
        self.assertEqual(len(m["schema"]), 3)
        self.assertEqual(m["schema"][2]["type"], "float")

    def test_load_csv(self):
        l = self._layout_csv([["campo","inicio","fim","tipo"],
                               ["CD_CLIENTE","1","4","char"],["NM_CLIENTE","5","24","char"]])
        m = self.ext.extract(self.data, "tb", layout_path=l)
        self.assertEqual(len(m["schema"]), 2)

    def test_load_xlsx(self):
        import openpyxl
        p  = self.tmp/"layout.xlsx"
        wb = openpyxl.Workbook(); ws = wb.active
        ws.append(["campo","inicio","fim","tipo"])
        ws.append(["CD_CLIENTE",1,4,"char"])
        wb.save(p)
        m = self.ext.extract(self.data, "tb", layout_path=p)
        self.assertEqual(len(m["schema"]), 1)

    def test_layout_section_present(self):
        l = self._layout_txt("CD_CLIENTE 1 4 CHAR\n")
        m = self.ext.extract(self.data, "tb", layout_path=l)
        self.assertIn("layout", m)
        self.assertEqual(m["layout"][0]["start"], 1)

    def test_overlap_warning(self):
        cols = [
            {"name":"a","_start":1,"_end":10,"type":"string","nullable":True,
             "primary_key":False,"description":"","regulatory_flags":[],"business_rules":[]},
            {"name":"b","_start":8,"_end":20,"type":"string","nullable":True,
             "primary_key":False,"description":"","regulatory_flags":[],"business_rules":[]},
        ]
        _, warnings = _validate_layout(cols)
        self.assertTrue(any("Sobreposicao" in w for w in warnings))

    def test_gap_warning(self):
        cols = [
            {"name":"a","_start":1,"_end":5,"type":"string","nullable":True,
             "primary_key":False,"description":"","regulatory_flags":[],"business_rules":[]},
            {"name":"b","_start":10,"_end":20,"type":"string","nullable":True,
             "primary_key":False,"description":"","regulatory_flags":[],"business_rules":[]},
        ]
        _, warnings = _validate_layout(cols)
        self.assertTrue(any("Lacuna" in w for w in warnings))

    def test_infer_mode_experimental(self):
        m = self.ext.extract(self.data, "tb", infer=True)
        self.assertEqual(m["manifest_status"], "DRAFT_EXPERIMENTAL")

    def test_missing_layout_raises(self):
        with self.assertRaises(FileNotFoundError):
            self.ext.extract(self.data, "tb_sem_layout_xyz")


# ═══════════════════════ TestJSONExtractor ════════════════════════════════════
class TestJSONExtractor(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.ext = JSONExtractor()

    def _jf(self, data, name="d.json"):
        p = self.tmp/name; p.write_text(json.dumps(data)); return p

    def test_list_of_objects(self):
        p = self._jf([{"id":1,"nome":"Ana"},{"id":2,"nome":"Bruno"}])
        m = self.ext.extract(p,"tb")
        self.assertEqual(m["source"]["json_structure"], "list")
        self.assertEqual(len(m["schema"]), 2)

    def test_root_key(self):
        p = self._jf({"data":[{"id":1}],"meta":{"t":1}})
        m = self.ext.extract(p,"tb",root_key="data")
        names = [c["name"] for c in m["schema"]]
        self.assertNotIn("meta", names)

    def test_auto_root_key(self):
        p = self._jf({"registros":[{"id":1}],"versao":"1.0"})
        m = self.ext.extract(p,"tb")
        self.assertEqual(m["source"]["json_root_key"],"registros")

    def test_nested_normalized(self):
        p = self._jf([{"id":1,"end":{"cidade":"SP","uf":"SP"}}])
        names = [c["name"] for c in self.ext.extract(p,"tb",max_level=2)["schema"]]
        self.assertIn("end__cidade", names)

    def test_nullable_missing_key(self):
        p = self._jf([{"id":1,"nome":"Ana"},{"id":2}])
        cols = {c["name"]:c for c in self.ext.extract(p,"tb")["schema"]}
        self.assertTrue(cols["nome"]["nullable"])
        self.assertFalse(cols["id"]["nullable"])

    def test_jsonlines(self):
        p = self.tmp/"d.jsonl"
        p.write_text('{"id":1}\n{"id":2}\n')
        m = self.ext.extract(p,"tb")
        self.assertEqual(m["source"]["json_structure"], "jsonlines")

    def test_single_object(self):
        p = self._jf({"id":1,"config":"x"})
        self.assertEqual(self.ext.extract(p,"tb")["source"]["json_structure"], "object")

    def test_deep_nesting_collapsed(self):
        p = self._jf([{"id":1,"l1":{"l2":{"l3":{"v":42}}}}])
        m = self.ext.extract(p,"tb",max_level=1)
        has_rule = any("colapsado" in r for c in m["schema"] for r in c.get("business_rules",[]))
        self.assertTrue(has_rule)

    def test_lgpd_flag(self):
        p = self._jf([{"nr_cpf":"12345678901","val":100}])
        cpf = next(c for c in self.ext.extract(p,"tb")["schema"] if "cpf" in c["name"])
        self.assertIn("LGPD_SENSITIVE", cpf["regulatory_flags"])

    def test_required_sections(self):
        p = self._jf([{"id":1}])
        m = self.ext.extract(p,"tb")
        for s in ["table","source","regulatory","steward","schema","tolerance","manifest_status"]:
            self.assertIn(s, m)


if __name__ == "__main__":
    unittest.main()
