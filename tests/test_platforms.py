"""Offline parsing tests; production site accessibility is checked by the workflow."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from platforms import parse_copart, parse_vip

class CalendarTests(unittest.TestCase):
    def test_copart_city_and_state(self):
        text = "Lista de Vendas | Curitiba - PR | 03.11.2099 | 53 | Goiânia - GO | 04.11.2099 | 56"
        rows = parse_copart(text)
        self.assertEqual(len(rows), 2)
        self.assertEqual({r["state"] for r in rows}, {"PR", "GO"})
        self.assertTrue(all(r["vehicle_count"] is None for r in rows))

    def test_vip_multistate_is_searchable_per_state(self):
        text = "Seguradoras INICIA EM 2D Início 03/11/2099 10:00 Lotes 18 Estados BA-GO-MT Tipo Leilão Online"
        rows = parse_vip(text)
        self.assertEqual({r["state"] for r in rows}, {"BA", "GO", "MT"})
        self.assertTrue(all(r["vehicle_count"] is None for r in rows))

    def test_past_event_excluded(self):
        self.assertEqual(parse_vip("Seguradoras Início 01/01/2020 10:00 Lotes 5 Estados GO"), [])

if __name__ == "__main__":
    unittest.main()
