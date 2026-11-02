"""Offline tests for browser auction adapters."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from browser_collect import parse_copart_rows, parse_vip_text

class Tests(unittest.TestCase):
    def test_copart_two_dates_one_yard(self):
        rows=[["Curitiba - PR","03.11.2099","04.11.2099","55"],
              ["Goiânia - GO","04.11.2099","04.11.2099","89"]]
        result=parse_copart_rows(rows)
        self.assertEqual(len(result),3)
        self.assertEqual({r["state"] for r in result},{"PR","GO"})
        self.assertTrue(all(r["vehicle_count"] is None for r in result))
    def test_copart_rejects_missing_date(self):
        self.assertEqual(parse_copart_rows([["Betim - MG","","","48"]]),[])
    def test_vip_multi_state(self):
        sample="\nSeguradoras\nInício: 03/11/2099 10:00\nLotes 83\nEstados BA-GO-MT\nTipo Leilão Online"
        result=parse_vip_text(sample)
        self.assertEqual({r["state"] for r in result},{"BA","GO","MT"})
        self.assertTrue(all(r["vehicle_count"] is None for r in result))
    def test_vip_rejects_unspecified_uf(self):
        self.assertEqual(parse_vip_text("Seguradoras\nInício: 03/11/2099 10:00\nEstados Não Informado"),[])
    def test_past_events_excluded(self):
        self.assertEqual(parse_copart_rows([["Goiânia - GO","01.01.2020","","70"]]),[])
if __name__=="__main__": unittest.main()
